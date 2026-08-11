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
  GET   /api/store/sales               — real store sales (revenue, orders, units)
  POST  /api/store/orders              — public checkout: place an order
  GET   /api/store/orders              — list orders (token required)
  PATCH /api/store/orders/{oid}        — update status + dispatch info (token)
  GET   /api/store/track               — public order tracking (order# + email)
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


class ServiceRequest(BaseModel):
    workspace: str = "Default"
    client: str = "Client"
    service: dict[str, Any] | None = None
    data: dict[str, Any] | None = None


class ServiceUpdateRequest(BaseModel):
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


class OrderRequest(BaseModel):
    workspace: str = "Default"
    client: str = "Client"
    product_id: str = ""
    quantity: int = 1
    items: list[dict[str, Any]] | None = None
    customer: dict[str, Any] | None = None
    payment_method: str = ""
    notes: str = ""


class OrderStatusPATCH(BaseModel):
    status: str
    tracking_number: str = ""
    carrier: str = ""
    dispatch_note: str = ""


def _require_store() -> None:
    if not get_config():
        raise HTTPException(status_code=503, detail="Store backend not configured (POCKETBASE_URL/POCKETBASE_SERVICE_KEY missing)")


async def _notify_order_placed(workspace: str, client: str, order: dict[str, Any]) -> None:
    """Best-effort emails when an order is placed.

    Sends a confirmation to the customer and a notification to the store
    owner (settings.contact_email). Both are fire-and-forget: any failure is
    logged, never raised, so checkout never depends on email.
    """
    from admin.store import store_store as ss
    from admin.tools.sba_email_client import SBAEmailClient

    email_client = SBAEmailClient()
    if not email_client.enabled:
        return

    customer_email = str(order.get("customer_email") or "").strip()
    settings = ss.get_settings(workspace, client)
    owner_email = str(settings.get("contact_email") or "").strip()
    store_name = str(settings.get("store_name") or "").strip() or client
    order_number = str(order.get("order_number") or order.get("id") or "")
    total = str(order.get("total") or "")
    currency = str(settings.get("currency") or "₹")
    items = order.get("items") or []
    items_txt = "\n".join(
        f"  - {it.get('name', 'Item')} x{it.get('quantity', 1)} @ {currency}{it.get('price', 0)}"
        for it in items
    ) or f"  - {order.get('product_name', 'Item')} x{order.get('quantity', 1)}"

    if customer_email:
        await email_client.send_email(
            customer_email,
            f"✅ Order {order_number} confirmed — {store_name}",
            f"Namaste {order.get('customer_name') or 'there'},\n\n"
            f"Your order at {store_name} is confirmed.\n\n"
            f"Order number: {order_number}\n"
            f"Status: Placed\n\n"
            f"Items:\n{items_txt}\n"
            f"\nTotal: {currency}{total}\n\n"
            f"We'll update you as the order moves to processing, shipping and delivery.\n"
            f"Thank you for shopping with us!\n\n— {store_name}",
            cc_owner=False,
        )

    if owner_email and owner_email != customer_email:
        location = " · ".join(x for x in [
            order.get("customer_city") or "",
            order.get("customer_state") or "",
            order.get("customer_pincode") or "",
        ] if x)
        source = order.get("source") or "Direct"
        await email_client.send_email(
            owner_email,
            f"🛒 New order {order_number} — {store_name}",
            f"A new order was placed on your store.\n\n"
            f"Order number: {order_number}\n"
            f"Customer: {order.get('customer_name') or '—'} <{customer_email}>\n"
            f"Phone: {order.get('customer_phone') or '—'}\n"
            f"Address: {order.get('customer_address') or '—'}\n"
            f"Location: {location or '—'}  (source: {source})\n\n"
            f"Items:\n{items_txt}\n"
            f"\nTotal: {currency}{total}  (payment: {order.get('payment_method') or 'COD'})\n\n"
            f"Login to your store dashboard to update the order status and "
            f"dispatch (tracking number/carrier).",
            cc_owner=False,
        )


async def _notify_order_shipped(workspace: str, client: str, order: dict[str, Any]) -> None:
    """Best-effort dispatch email to the customer when an order ships."""
    from admin.store import store_store as ss
    from admin.tools.sba_email_client import SBAEmailClient

    email_client = SBAEmailClient()
    if not email_client.enabled:
        return

    customer_email = str(order.get("customer_email") or "").strip()
    if not customer_email:
        return
    settings = ss.get_settings(workspace, client)
    store_name = str(settings.get("store_name") or "").strip() or client
    order_number = str(order.get("order_number") or order.get("id") or "")
    carrier = str(order.get("carrier") or "").strip()
    tracking = str(order.get("tracking_number") or "").strip()
    currency = str(settings.get("currency") or "₹")

    await email_client.send_email(
        customer_email,
        f"📦 Order {order_number} dispatched — {store_name}",
        f"Namaste {order.get('customer_name') or 'there'},\n\n"
        f"Good news! Your order {order_number} has been dispatched.\n\n"
        f"Carrier: {carrier or '—'}\n"
        f"Tracking number: {tracking or '—'}\n"
        f"{order.get('dispatch_note') or ''}\n"
        f"Total: {currency}{order.get('total') or ''}\n\n"
        f"Track online: {store_name} website ka Track Order section use karo "
        f"(order number + apna email).\n\n— {store_name}",
        cc_owner=False,
    )


# ── Status ───────────────────────────────────────────────────────────────────


@router.get("/status")
async def store_status(
    workspace: str = Query("Default"),
    client: str = Query("Client"),
):
    _require_store()
    site_url = ""
    try:
        from admin.agency.website_supabase import get_website_build
        build = get_website_build(workspace, client)
        site_url = (build or {}).get("site_url") or ""
    except Exception as e:  # noqa: BLE001
        logger.warning("store: status site_url lookup failed: %s", e)
    return {
        "available": True,
        "workspace": workspace,
        "client": client,
        "products": store_store.product_stats(workspace, client),
        "services": store_store.service_stats(workspace, client),
        "settings": store_store.get_settings(workspace, client),
        "site_url": site_url,
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


# ── Services ─────────────────────────────────────────────────────────────────


@router.get("/services")
async def list_services(
    workspace: str = Query("Default"),
    client: str = Query("Client"),
    active_only: bool = Query(False),
):
    _require_store()
    return store_store.list_services(workspace, client, active_only=active_only)


@router.post("/services")
async def create_service(req: ServiceRequest, auth: dict | None = Depends(_auth_optional)):
    _require_store()
    _enforce_client_scope(auth, req.workspace, req.client)
    service = req.service or req.data or {}
    created = store_store.create_service(req.workspace, req.client, service)
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create service")
    return created


@router.patch("/services/{sid}")
async def update_service(sid: str, req: ServiceUpdateRequest, auth: dict | None = Depends(_auth_optional)):
    _require_store()
    _enforce_client_scope(auth, req.workspace, req.client)
    updated = store_store.update_service(req.workspace, req.client, sid, req.data)
    if not updated:
        raise HTTPException(status_code=404, detail="Service not found or update failed")
    return updated


@router.delete("/services/{sid}")
async def delete_service(sid: str, workspace: str = Query("Default"), client: str = Query("Client"),
                         auth: dict | None = Depends(_auth_optional)):
    _require_store()
    _enforce_client_scope(auth, workspace, client)
    ok = store_store.delete_service(workspace, client, sid)
    if not ok:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"success": True, "deleted": sid}


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
    """Public view: store settings + active products + services. No token required."""
    _require_store()
    return {
        "workspace": workspace,
        "client": client,
        "settings": store_store.get_settings(workspace, client),
        "products": store_store.list_products(workspace, client, active_only=True),
        "services": store_store.list_services(workspace, client, active_only=True),
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
    """Real store sales for this workspace/client (revenue, orders, units).

    Not SBA lead stats — this is actual revenue from orders placed through
    the client's storefront.
    """
    _require_store()
    return store_store.sales_stats(workspace, client)


# ── Orders (public checkout + owner list) ───────────────────────────────────


@router.post("/orders")
async def create_order(req: OrderRequest):
    """Public checkout — a customer places an order for one product.

    No auth needed: anyone can buy from the public storefront. Stock is
    decremented and the order is recorded for the owner's sales dashboard.
    """
    _require_store()
    result = store_store.place_order(
        req.workspace, req.client, req.product_id, req.quantity,
        items=req.items, customer=req.customer,
        payment_method=req.payment_method, notes=req.notes,
    )
    if result is None:
        raise HTTPException(status_code=503, detail="Store backend not available")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    # Best-effort order notifications (customer confirmation + owner alert).
    # Never blocks/fails the checkout when email is unavailable.
    try:
        await _notify_order_placed(req.workspace, req.client, result)
    except Exception:  # noqa: BLE001
        logger.exception("store: order notification failed (order still placed)")
    return result


@router.get("/orders")
async def store_orders(
    payload: dict | None = Depends(_auth_optional),
    workspace: str = Query("Default"),
    client: str = Query("Client"),
):
    """List orders for this store (owner or agency)."""
    _require_store()
    _enforce_client_scope(payload, workspace, client)
    return store_store.list_orders(workspace, client)


@router.patch("/orders/{oid}")
async def update_order_status(
    oid: str,
    req: OrderStatusPATCH,
    workspace: str = Query("Default"),
    client: str = Query("Client"),
    payload: dict | None = Depends(_auth_optional),
):
    """Owner updates an order's status + optional dispatch info."""
    _require_store()
    _enforce_client_scope(payload, workspace, client)
    extra = {
        "tracking_number": req.tracking_number,
        "carrier": req.carrier,
        "dispatch_note": req.dispatch_note,
    }
    result = store_store.update_order_status(workspace, client, oid, req.status, extra=extra)
    if result is None:
        raise HTTPException(status_code=503, detail="Store backend not available")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    # Dispatch notification (customer email) when an order ships.
    if (result.get("status") == "shipped" and result.get("tracking_number")):
        try:
            await _notify_order_shipped(workspace, client, result)
        except Exception:  # noqa: BLE001
            logger.exception("store: shipped notification failed")
    return result


@router.get("/track")
async def track_order_public(
    workspace: str = Query("Default"),
    client: str = Query("Client"),
    order_number: str = Query(""),
    email: str = Query(""),
):
    """Public order tracking — order_number + email must match. No auth."""
    _require_store()
    if not order_number.strip() or not email.strip():
        raise HTTPException(status_code=400, detail="Order number + email dono required hain")
    result = store_store.track_order(workspace, client, order_number.strip(), email.strip())
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ── Storefront views (public analytics) ────────────────────────────────────


@router.post("/views")
async def record_store_view(
    workspace: str = Query("Default"),
    client: str = Query("Client"),
):
    """Record one pageview of the client's public storefront. No auth."""
    _require_store()
    ok = store_store.record_view(workspace, client)
    return {"success": ok, "workspace": workspace, "client": client}


@router.get("/views")
async def store_views(
    workspace: str = Query("Default"),
    client: str = Query("Client"),
):
    """Total pageviews of the client's public storefront."""
    _require_store()
    return {"views": store_store.view_count(workspace, client)}


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
