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
ORDERS_TABLE = "store_orders"

# Order status lifecycle (Shopify-like)
ORDER_STATUSES = ["placed", "processing", "shipped", "delivered", "cancelled"]
ORDER_STATUS_LABELS = {
    "placed": "Placed",
    "processing": "Processing",
    "shipped": "Shipped",
    "delivered": "Delivered",
    "cancelled": "Cancelled",
}

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


# ═══════════════════════════════════════════════════════════════════════════════
# ORDERS + SALES (real store revenue — NOT SBA lead stats)
# ═══════════════════════════════════════════════════════════════════════════════


def _norm_order(row: dict[str, Any]) -> dict[str, Any]:
    """Coerce an order row into stable shapes for consumers."""
    def s(v: Any) -> str:
        return "" if v is None else str(v)
    out = dict(row)
    out["client_name"] = s(out.get("client_name"))
    out["order_number"] = s(out.get("order_number") or out.get("id") or "")
    out["customer_name"] = s(out.get("customer_name"))
    out["customer_email"] = s(out.get("customer_email"))
    out["customer_phone"] = s(out.get("customer_phone"))
    out["customer_address"] = s(out.get("customer_address"))
    out["status"] = s(out.get("status") or "placed")
    try:
        out["total"] = float(out.get("total") or 0)
    except (TypeError, ValueError):
        out["total"] = 0.0
    items = out.get("items")
    if isinstance(items, str):
        try:
            import json
            items = json.loads(items)
        except Exception:  # noqa: BLE001
            items = []
    if not isinstance(items, list):
        items = []
    out["items"] = items
    return out


def place_order(workspace: str, client: str, product_id: str, quantity: int,
                customer: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Place an order for one product (public checkout).

    Validates the product exists + is in stock, decrements stock, and records
    the order row in the workspace schema. Returns the created order.
    """
    cfg = get_config()
    if not cfg:
        return None
    qty = max(1, int(quantity or 1))
    customer = customer or {}
    url, key = cfg
    product = get_product(workspace, client, product_id)
    if not product:
        return {"error": "Product not found"}
    if not product.get("active", True):
        return {"error": "Product is not available"}
    try:
        stock = int(product.get("stock") or 0)
    except (TypeError, ValueError):
        stock = 0
    if stock < qty:
        return {"error": "Not enough stock"}

    price = 0.0
    try:
        price = float(str(product.get("price") or "0").replace("₹", "").replace(",", "").strip())
    except (TypeError, ValueError):
        price = 0.0
    total = round(price * qty, 2)

    order_number = "ORD-" + str(int(__import__("time").time() * 1000))[-8:]

    payload = {
        "client_name": client,
        "order_number": order_number,
        "product_id": product_id,
        "product_name": product.get("name", ""),
        "quantity": qty,
        "unit_price": price,
        "total": total,
        "items": [{
            "product_id": product_id,
            "name": product.get("name", ""),
            "price": price,
            "quantity": qty,
        }],
        "customer_name": str(customer.get("name") or "").strip(),
        "customer_email": str(customer.get("email") or "").strip(),
        "customer_phone": str(customer.get("phone") or "").strip(),
        "customer_address": str(customer.get("address") or "").strip(),
        "status": "placed",
    }
    try:
        rows = _api(
            "POST", url, key,
            "/rest/v1/" + ORDERS_TABLE,
            payload,
            profile=schema_for(workspace),
        )
        if not rows:
            return {"error": "Order create failed"}
        # Decrement stock
        try:
            update_product(workspace, client, product_id, {"stock": max(0, stock - qty)})
        except Exception:  # noqa: BLE001
            logger.warning("store: stock decrement failed for %s", product_id)
        return _norm_order(rows[0])
    except Exception as e:  # noqa: BLE001
        logger.warning("store: place_order failed: %s", e)
        return {"error": f"Order failed: {e}"}


def get_order(workspace: str, client: str, oid: str) -> dict[str, Any] | None:
    """Fetch one order by id, scoped to (workspace, client)."""
    cfg = get_config()
    if not cfg:
        return None
    url, key = cfg
    try:
        rows = _api(
            "GET", url, key,
            "/rest/v1/" + ORDERS_TABLE + "?select=*&id=eq." + oid,
            profile=schema_for(workspace),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("store: get_order failed: %s", e)
        return None
    rows = [r for r in rows if r.get("client_name") == client]
    return _norm_order(rows[0]) if rows else None


def list_orders(workspace: str, client: str, limit: int = 200) -> list[dict[str, Any]]:
    """List orders for (workspace, client), newest first."""
    cfg = get_config()
    if not cfg:
        return []
    url, key = cfg
    try:
        rows = _api(
            "GET", url, key,
            "/rest/v1/" + ORDERS_TABLE + "?select=*&" + _client_q(client) + "&order=created_at.desc",
            profile=schema_for(workspace),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("store: list_orders failed: %s", e)
        return []
    return [_norm_order(r) for r in rows][:limit]


def update_order_status(workspace: str, client: str, oid: str, status: str) -> dict[str, Any] | None:
    """Update an order's status (owner action).

    Validates the status against the known lifecycle and scopes the update
    to (workspace, client). Returns the updated order or an error dict.
    """
    status = (status or "").strip().lower()
    if status not in ORDER_STATUSES:
        return {"error": f"Invalid status '{status}'. Valid: {', '.join(ORDER_STATUSES)}"}
    cfg = get_config()
    if not cfg:
        return None
    existing = get_order(workspace, client, oid)
    if not existing:
        return {"error": "Order not found"}
    url, key = cfg
    try:
        rows = _api(
            "PATCH", url, key,
            "/rest/v1/" + ORDERS_TABLE + "?id=eq." + oid,
            {"status": status},
            profile=schema_for(workspace),
        )
        rows = [r for r in rows if r.get("client_name") == client]
        if rows:
            return _norm_order(rows[0])
        # Gateway may return empty on PATCH; fall back to re-read.
        updated = get_order(workspace, client, oid)
        return updated if updated else existing
    except Exception as e:  # noqa: BLE001
        logger.warning("store: update_order_status failed: %s", e)
        return {"error": f"Status update failed: {e}"}


def sales_stats(workspace: str, client: str) -> dict[str, Any]:
    """Real store sales: revenue, order count, units sold, top product.

    This is what the client store dashboard shows — actual orders placed
    through the storefront, NOT SBA lead pipeline counts.
    """
    orders = list_orders(workspace, client)
    revenue = round(sum(float(o.get("total") or 0) for o in orders), 2)
    units = 0
    by_product: dict[str, dict[str, Any]] = {}
    for o in orders:
        for item in o.get("items") or []:
            q = int(item.get("quantity") or 0)
            units += q
            pid = str(item.get("product_id") or o.get("product_id") or "?")
            entry = by_product.setdefault(pid, {"name": item.get("name") or o.get("product_name") or "Product", "units": 0, "revenue": 0.0})
            entry["units"] += q
            entry["revenue"] = round(entry["revenue"] + float(item.get("price") or 0) * q, 2)
    top = None
    if by_product:
        top = max(by_product.values(), key=lambda e: e["units"])
    return {
        "revenue": revenue,
        "orders": len(orders),
        "units": units,
        "avg_order": round(revenue / len(orders), 2) if orders else 0.0,
        "top_product": top,
        "status_breakdown": {s: sum(1 for o in orders if (o.get("status") or "placed") == s) for s in {o.get("status") or "placed" for o in orders}},
        "source": "orders",
    }
