"""Client Store API — Shopify-like storefront management per workspace.

Endpoints:
  GET   /api/store/status              — store availability + product stats
  GET   /api/store/public              — public storefront (no auth): settings + products
  GET   /api/store/products            — list products (?workspace=&client=)
  POST  /api/store/products            — create a product (token required)
  PATCH /api/store/products/{pid}      — update a product (token required)
  DELETE /api/store/products/{pid}     — delete a product (token required)
  GET   /api/store/settings            — store settings (?workspace=&client=)
  PATCH /api/store/settings            — upsert store settings (token required)
  POST  /api/store/sync                — rebuild + redeploy client site from store (token)
  POST  /api/store/accounts            — create a client account (agency/admin)
  POST  /api/store/client/login        — client login -> signed token
  GET   /api/store/client/me           — current client identity (token)
  GET   /api/store/sales               — SBA pipeline stats for this workspace
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel

from admin.agency.website_supabase import get_config
from admin.store import store_auth, store_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/store", tags=["client-store"])


def _auth_workspace(x_store_token: str = Header("", alias="X-Store-Token"),
                    workspace: str = Query("")) -> dict[str, Any]:
    """Require a valid store token, pinned to the requested workspace."""
    payload = store_auth.verify_token(x_store_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired store token")
    if workspace and payload.get("ws") != workspace:
        raise HTTPException(status_code=403, detail="Token not valid for this workspace")
    return payload


def _auth_optional(x_store_token: str = Header("", alias="X-Store-Token")) -> dict[str, Any] | None:
    """Verify a token when supplied. Returns payload or None (agency context).

    Clients must send their token; the agency admin UI may manage the store
    without one. A supplied token always pins the caller to its workspace.
    """
    if not x_store_token:
        return None
    return store_auth.verify_token(x_store_token)


def _enforce_client_scope(auth: dict[str, Any] | None, workspace: str, client: str) -> None:
    """Reject a logged-in client touching another workspace/client."""
    if auth:
        if auth.get("ws") != workspace or auth.get("client") != client:
            raise HTTPException(status_code=403, detail="Cannot modify another workspace's store")


# ── Request Models ───────────────────────────────────────────────────────────

class ProductRequest(BaseModel):
    workspace: str = "Default"
    client: str = "Client"
    product: dict[str, Any] | None = None
    data: dict[str, Any] | None = None


class ProductUpdateRequest(BaseModel):
    workspace: str = "Default"
    client: str = "Client"
    data: dict[str, Any]


class SettingsRequest(BaseModel):
    workspace: str = "Default"
    client: str = "Client"
    data: dict[str, Any]


class SyncRequest(BaseModel):
    workspace: str = "Default"
    client: str = "Client"
    deploy: bool = True


class LoginRequest(BaseModel):
    workspace: str = "Default"
    client: str = "Client"
    email: str
    password: str


class AccountRequest(BaseModel):
    workspace: str = "Default"
    client: str = "Client"
    email: str
    password: str
    name: str = ""


def _require_store() -> None:
    if not get_config():
        raise HTTPException(status_code=503, detail="Store backend not configured (POCKETBASE_URL/POCKETBASE_SERVICE_KEY missing)")


# ── Status ───────────────────────────────────────────────────────────────────


@router.get("/status")
async def store_status(
    workspace: str = Query("Default"),
    client: str = Query("Client"),
):
    _require_store()
    return {
        "available": True,
        "workspace": workspace,
        "client": client,
        "products": store_store.product_stats(workspace, client),
        "settings": store_store.get_settings(workspace, client),
    }


# ── Products ─────────────────────────────────────────────────────────────────


@router.get("/products")
async def list_products(
    workspace: str = Query("Default"),
    client: str = Query("Client"),
    active_only: bool = Query(False),
):
    _require_store()
    return store_store.list_products(workspace, client, active_only=active_only)


@router.post("/products")
async def create_product(req: ProductRequest, auth: dict | None = Depends(_auth_optional)):
    _require_store()
    _enforce_client_scope(auth, req.workspace, req.client)
    product = req.product or req.data or {}
    created = store_store.create_product(req.workspace, req.client, product)
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create product")
    return created


@router.patch("/products/{pid}")
async def update_product(pid: str, req: ProductUpdateRequest, auth: dict | None = Depends(_auth_optional)):
    _require_store()
    _enforce_client_scope(auth, req.workspace, req.client)
    updated = store_store.update_product(req.workspace, req.client, pid, req.data)
    if not updated:
        raise HTTPException(status_code=404, detail="Product not found or update failed")
    return updated


@router.delete("/products/{pid}")
async def delete_product(pid: str, workspace: str = Query("Default"), client: str = Query("Client"),
                         auth: dict | None = Depends(_auth_optional)):
    _require_store()
    _enforce_client_scope(auth, workspace, client)
    ok = store_store.delete_product(workspace, client, pid)
    if not ok:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"success": True, "deleted": pid}


# ── Settings ─────────────────────────────────────────────────────────────────


@router.get("/settings")
async def get_settings(
    workspace: str = Query("Default"),
    client: str = Query("Client"),
):
    _require_store()
    return store_store.get_settings(workspace, client)


@router.patch("/settings")
async def update_settings(req: SettingsRequest, auth: dict | None = Depends(_auth_optional)):
    _require_store()
    _enforce_client_scope(auth, req.workspace, req.client)
    saved = store_store.upsert_settings(req.workspace, req.client, req.data)
    if not saved:
        raise HTTPException(status_code=500, detail="Failed to save settings")
    return store_store.get_settings(req.workspace, req.client)


# ── Public storefront (no auth) ──────────────────────────────────────────────


@router.get("/public")
async def public_storefront(
    workspace: str = Query("Default"),
    client: str = Query("Client"),
):
    """Public view: store settings + active products. No token required."""
    _require_store()
    return {
        "workspace": workspace,
        "client": client,
        "settings": store_store.get_settings(workspace, client),
        "products": store_store.list_products(workspace, client, active_only=True),
    }


# ── Client accounts + auth ───────────────────────────────────────────────────


@router.post("/accounts")
async def create_account(req: AccountRequest):
    """Create a client account for a workspace (agency admin UI)."""
    _require_store()
    account = store_auth.create_account(req.workspace, req.client, req.email, req.password, req.name)
    if not account:
        raise HTTPException(status_code=400, detail="Account not created (invalid email/password or backend down)")
    return account


@router.post("/client/login")
async def client_login(req: LoginRequest):
    """Client login -> signed token bound to (workspace, client)."""
    _require_store()
    account = store_auth.verify_login(req.workspace, req.client, req.email, req.password)
    if not account:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = store_auth.issue_token(req.workspace, req.client, account["email"], account["name"])
    return {"token": token, "account": account, "workspace": req.workspace}


@router.get("/client/me")
async def client_me(payload: dict = Depends(_auth_workspace)):
    """Current client identity (requires token)."""
    return {
        "workspace": payload.get("ws", ""),
        "client": payload.get("client", ""),
        "email": payload.get("email", ""),
        "name": payload.get("name", ""),
    }


@router.get("/sales")
async def store_sales(
    workspace: str = Query("Default"),
    client: str = Query("Client"),
):
    """SBA pipeline stats for this workspace (leads, contacted, hot, meetings)."""
    _require_store()
    return store_auth.sales_stats(workspace, client)


# ── Sync to live website ─────────────────────────────────────────────────────


@router.post("/sync")
async def sync_store_site(req: SyncRequest, auth: dict | None = Depends(_auth_optional)):
    """Rebuild the client's live site from current store products + settings.

    Delegates to the Website Agent's store-aware builder and optionally
    redeploys to Vercel.
    """
    _require_store()
    _enforce_client_scope(auth, req.workspace, req.client)
    try:
        from admin.tools import website_tools
        result = website_tools.build_site_from_store(
            workspace=req.workspace,
            client=req.client,
            deploy=req.deploy,
        )
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.exception("store sync failed")
        raise HTTPException(status_code=500, detail=f"Sync failed: {e}") from e
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
