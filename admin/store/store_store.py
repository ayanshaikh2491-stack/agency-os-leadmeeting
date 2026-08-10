"""Store data store — products + settings per workspace, PocketBase-backed.

Uses the same REST pattern as `admin.agency.website_supabase` (urllib only).
Each workspace's rows live in its own schema (`{schema}__store_products`,
`{schema}__store_settings`) and are scoped to a client via `client_name`.
"""
from __future__ import annotations

import logging
from typing import Any

from admin.agency.website_supabase import _api, get_config
from admin.agency.workspace_provision import schema_for

logger = logging.getLogger(__name__)

PRODUCTS_TABLE = "store_products"
SETTINGS_TABLE = "store_settings"

PRODUCT_FIELDS = {
    "name": "",
    "description": "",
    "price": "",
    "compare_at": "",
    "image_url": "",
    "category": "",
    "sku": "",
    "stock": 0,
    "active": True,
    "featured": False,
    "sort_order": 0,
}


def store_available() -> bool:
    """True when the gateway/backend is configured (SUPABASE_URL + key set)."""
    return get_config() is not None


def _client_q(client: str) -> str:
    import urllib.parse
    return "client_name=eq." + urllib.parse.quote(client)


def _norm_product(row: dict[str, Any]) -> dict[str, Any]:
    """Coerce PocketBase json fields into stable types for consumers."""
    def s(v: Any) -> str:
        return "" if v is None else str(v)
    out = dict(row)
    out["name"] = s(out.get("name"))
    out["description"] = s(out.get("description"))
    out["price"] = s(out.get("price"))
    out["compare_at"] = s(out.get("compare_at"))
    out["image_url"] = s(out.get("image_url"))
    out["category"] = s(out.get("category"))
    out["sku"] = s(out.get("sku"))
    try:
        out["stock"] = int(out.get("stock") or 0)
    except (TypeError, ValueError):
        out["stock"] = 0
    out["active"] = bool(out.get("active", True))
    out["featured"] = bool(out.get("featured", False))
    try:
        out["sort_order"] = int(out.get("sort_order") or 0)
    except (TypeError, ValueError):
        out["sort_order"] = 0
    return out


def _clean_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Keep only known product fields (drops id/created noise)."""
    payload = {}
    for key, default in PRODUCT_FIELDS.items():
        if key in data and data[key] is not None:
            payload[key] = data[key]
    return payload


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCTS
# ═══════════════════════════════════════════════════════════════════════════════


def list_products(workspace: str, client: str, active_only: bool = False) -> list[dict[str, Any]]:
    """List all products for (workspace, client), newest first."""
    cfg = get_config()
    if not cfg:
        return []
    url, key = cfg
    try:
        rows = _api(
            "GET", url, key,
            "/rest/v1/" + PRODUCTS_TABLE + "?select=*&" + _client_q(client) + "&order=created_at.desc",
            profile=schema_for(workspace),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("store: list_products failed: %s", e)
        return []
    products = [_norm_product(r) for r in rows]
    if active_only:
        products = [p for p in products if p["active"]]
    return products


def get_product(workspace: str, client: str, pid: str) -> dict[str, Any] | None:
    cfg = get_config()
    if not cfg:
        return None
    url, key = cfg
    try:
        rows = _api(
            "GET", url, key,
            "/rest/v1/" + PRODUCTS_TABLE + "?select=*&id=eq." + pid,
            profile=schema_for(workspace),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("store: get_product failed: %s", e)
        return None
    rows = [r for r in rows if r.get("client_name") == client]
    return _norm_product(rows[0]) if rows else None


def create_product(workspace: str, client: str, data: dict[str, Any]) -> dict[str, Any] | None:
    """Create a product for (workspace, client)."""
    cfg = get_config()
    if not cfg:
        return None
    url, key = cfg
    payload = {"client_name": client, **(_clean_payload(data) or {"name": "Untitled Product"})}
    try:
        rows = _api(
            "POST", url, key,
            "/rest/v1/" + PRODUCTS_TABLE,
            payload,
            profile=schema_for(workspace),
        )
        return _norm_product(rows[0]) if rows else None
    except Exception as e:  # noqa: BLE001
        logger.warning("store: create_product failed: %s", e)
        return None


def update_product(workspace: str, client: str, pid: str, data: dict[str, Any]) -> dict[str, Any] | None:
    """Update a product by its PocketBase id."""
    cfg = get_config()
    if not cfg:
        return None
    url, key = cfg
    payload = _clean_payload(data)
    if not payload:
        return get_product(workspace, client, pid)
    try:
        rows = _api(
            "PATCH", url, key,
            "/rest/v1/" + PRODUCTS_TABLE + "?id=eq." + pid,
            payload,
            profile=schema_for(workspace),
        )
        rows = [r for r in rows if r.get("client_name") == client]
        return _norm_product(rows[0]) if rows else None
    except Exception as e:  # noqa: BLE001
        logger.warning("store: update_product failed: %s", e)
        return None


def delete_product(workspace: str, client: str, pid: str) -> bool:
    cfg = get_config()
    if not cfg:
        return False
    url, key = cfg
    try:
        _api(
            "DELETE", url, key,
            "/rest/v1/" + PRODUCTS_TABLE + "?id=eq." + pid,
            profile=schema_for(workspace),
        )
        return True
    except Exception as e:  # noqa: BLE001
        logger.warning("store: delete_product failed: %s", e)
        return False


def product_stats(workspace: str, client: str) -> dict[str, Any]:
    """Aggregate counts for the client dashboard."""
    products = list_products(workspace, client)
    active = [p for p in products if p["active"]]
    return {
        "total": len(products),
        "active": len(active),
        "inactive": len(products) - len(active),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_SETTINGS: dict[str, Any] = {
    "store_name": "",
    "tagline": "",
    "category": "ecommerce",
    "style": "modern",
    "color_primary": "#2563EB",
    "framework": "nextjs",
    "currency": "₹",
    "show_stock": True,
    "contact_email": "",
    "domain": "",
}


def get_settings(workspace: str, client: str) -> dict[str, Any]:
    """Get store settings for (workspace, client), merged over defaults."""
    cfg = get_config()
    row: dict[str, Any] = {}
    if cfg:
        url, key = cfg
        try:
            rows = _api(
                "GET", url, key,
                "/rest/v1/" + SETTINGS_TABLE + "?select=*&" + _client_q(client),
                profile=schema_for(workspace),
            )
            if rows:
                row = dict(rows[0])
        except Exception as e:  # noqa: BLE001
            logger.warning("store: get_settings failed: %s", e)
    out = dict(DEFAULT_SETTINGS)
    for k, v in row.items():
        if k in out and v is not None:
            out[k] = str(v) if k != "show_stock" else bool(v)
    return out


def upsert_settings(workspace: str, client: str, data: dict[str, Any]) -> dict[str, Any] | None:
    """Upsert store settings (single row per client)."""
    cfg = get_config()
    if not cfg:
        return None
    url, key = cfg
    payload = {"client_name": client}
    for k, v in data.items():
        if k in DEFAULT_SETTINGS and v is not None:
            payload[k] = v
    try:
        rows = _api(
            "POST", url, key,
            "/rest/v1/" + SETTINGS_TABLE,
            payload,
            on_conflict="client_name",
            profile=schema_for(workspace),
        )
        return rows[0] if rows else None
    except Exception as e:  # noqa: BLE001
        logger.warning("store: upsert_settings failed: %s", e)
        return None
