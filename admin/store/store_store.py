"""Store data store — products + settings per workspace, PocketBase-backed.

Uses the same REST pattern as `admin.agency.website_supabase` (urllib only).
Each workspace's rows live in its own schema (`{schema}__store_products`,
`{schema}__store_settings`) and are scoped to a client via `client_name`.
"""
from __future__ import annotations

import datetime
import logging
import re
from collections import Counter
from typing import Any

from admin.agency.website_supabase import _api, get_config
from admin.agency.workspace_provision import schema_for

logger = logging.getLogger(__name__)

PRODUCTS_TABLE = "store_products"
SERVICES_TABLE = "store_services"
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

# ── Customer location parsing (kaha se order aaya) ──────────────────────────
# Pincode prefix (first 3 digits) → (city, state) for common Indian cities.
# Deterministic + testable; fallback logic below handles the rest.
PINCODE_CITY_MAP = {
    "110": ("Delhi", "Delhi"),
    "121": ("Faridabad", "Haryana"),
    "122": ("Gurugram", "Haryana"),
    "400": ("Mumbai", "Maharashtra"),
    "401": ("Thane", "Maharashtra"),
    "411": ("Pune", "Maharashtra"),
    "500": ("Hyderabad", "Telangana"),
    "560": ("Bengaluru", "Karnataka"),
    "600": ("Chennai", "Tamil Nadu"),
    "641": ("Coimbatore", "Tamil Nadu"),
    "682": ("Kochi", "Kerala"),
    "695": ("Thiruvananthapuram", "Kerala"),
    "700": ("Kolkata", "West Bengal"),
    "380": ("Ahmedabad", "Gujarat"),
    "395": ("Surat", "Gujarat"),
    "302": ("Jaipur", "Rajasthan"),
    "226": ("Lucknow", "Uttar Pradesh"),
    "201": ("Ghaziabad", "Uttar Pradesh"),
    "452": ("Indore", "Madhya Pradesh"),
    "462": ("Bhopal", "Madhya Pradesh"),
}

STATES = [
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
    "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya", "mizoram",
    "nagaland", "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu",
    "telangana", "tripura", "uttar pradesh", "uttarakhand", "west bengal",
    "delhi", "jammu and kashmir", "ladakh", "puducherry", "chandigarh",
    "andaman and nicobar islands", "dadra and nagar haveli and daman and diu",
]
STATE_ABBR = {
    "ka": "karnataka", "mh": "maharashtra", "dl": "delhi", "tn": "tamil nadu",
    "ap": "andhra pradesh", "ts": "telangana", "gj": "gujarat", "rj": "rajasthan",
    "up": "uttar pradesh", "wb": "west bengal", "kl": "kerala", "pb": "punjab",
    "hr": "haryana", "mp": "madhya pradesh", "br": "bihar", "od": "odisha",
    "ga": "goa", "uk": "uttarakhand", "cg": "chhattisgarh", "jh": "jharkhand",
    "as": "assam", "sk": "sikkim", "mz": "mizoram", "mn": "manipur",
    "ml": "meghalaya", "nl": "nagaland", "tr": "tripura", "ar": "arunachal pradesh",
    "la": "ladakh", "jk": "jammu and kashmir", "py": "puducherry", "ch": "chandigarh",
}


def parse_location(address: str | None) -> dict[str, str]:
    """Extract city/state/pincode from a free-text delivery address.

    Pincode (6 digits) is the strongest signal → city/state via prefix map.
    Falls back to scanning for known state names/abbreviations, then uses the
    last comma segment of the address as the city.
    """
    addr = (address or "").strip()
    out = {"customer_city": "", "customer_state": "", "customer_pincode": ""}
    if not addr:
        return out
    low = addr.lower()

    m = re.search(r"\b(\d{6})\b", addr)
    if m:
        pincode = m.group(1)
        out["customer_pincode"] = pincode
        city_state = PINCODE_CITY_MAP.get(pincode[:3])
        if city_state:
            out["customer_city"], out["customer_state"] = city_state

    state = None
    for st in STATES:
        if st in low:
            state = st.title()
            break
    if not state:
        for abbr, full in STATE_ABBR.items():
            if re.search(r"\b" + re.escape(abbr) + r"\b", low):
                state = full.title()
                break
    if state and not out["customer_state"]:
        out["customer_state"] = state

    if not out["customer_city"]:
        known = {s.lower() for s in STATES} | set(STATE_ABBR)
        for seg in reversed([s.strip() for s in addr.split(",") if s.strip()]):
            seg_low = seg.lower()
            if not seg or re.search(r"\d", seg) or seg_low in known or seg_low in STATE_ABBR:
                continue
            out["customer_city"] = seg.split()[0][:40]
            break
    return out


def _norm_city_state(order: dict[str, Any]) -> tuple[str, str]:
    """Best-effort location for an order (explicit fields > parse address)."""
    city = str(order.get("customer_city") or "").strip()
    state = str(order.get("customer_state") or "").strip()
    if city or state:
        return city, state
    loc = parse_location(str(order.get("customer_address") or ""))
    return loc["customer_city"], loc["customer_state"]

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

SERVICE_FIELDS = {
    "name": "",
    "description": "",
    "price": "",
    "active": True,
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
# SERVICES
# ═══════════════════════════════════════════════════════════════════════════════


def _norm_service(row: dict[str, Any]) -> dict[str, Any]:
    """Coerce a store_services row into stable types."""
    def s(v: Any) -> str:
        return "" if v is None else str(v)
    out = dict(row)
    out["name"] = s(out.get("name"))
    out["description"] = s(out.get("description"))
    out["price"] = s(out.get("price"))
    try:
        out["active"] = bool(out.get("active", True))
    except (TypeError, ValueError):
        out["active"] = True
    try:
        out["sort_order"] = int(out.get("sort_order") or 0)
    except (TypeError, ValueError):
        out["sort_order"] = 0
    return out


def _clean_service_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Keep only known service fields."""
    payload = {}
    for key in SERVICE_FIELDS:
        if key in data and data[key] is not None:
            payload[key] = data[key]
    return payload


def list_services(workspace: str, client: str, active_only: bool = False) -> list[dict[str, Any]]:
    """List all services for (workspace, client), lowest sort_order first."""
    cfg = get_config()
    if not cfg:
        return []
    url, key = cfg
    try:
        rows = _api(
            "GET", url, key,
            "/rest/v1/" + SERVICES_TABLE + "?select=*&" + _client_q(client) + "&order=sort_order.asc",
            profile=schema_for(workspace),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("store: list_services failed: %s", e)
        return []
    services = [_norm_service(r) for r in rows]
    if active_only:
        services = [s for s in services if s["active"]]
    return services


def create_service(workspace: str, client: str, data: dict[str, Any]) -> dict[str, Any] | None:
    """Create a service for (workspace, client)."""
    cfg = get_config()
    if not cfg:
        return None
    url, key = cfg
    payload = {"client_name": client, **(_clean_service_payload(data) or {"name": "Untitled Service"})}
    try:
        rows = _api(
            "POST", url, key,
            "/rest/v1/" + SERVICES_TABLE,
            payload,
            profile=schema_for(workspace),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("store: create_service failed: %s", e)
        return None
    if not rows:
        return None
    row = rows[0] if isinstance(rows, list) else rows
    if row.get("client_name") != client:
        logger.warning("store: service insert scoped to wrong client")
        return None
    return _norm_service(row)


def update_service(workspace: str, client: str, sid: str, data: dict[str, Any]) -> dict[str, Any] | None:
    """Update a service (scoped to client)."""
    cfg = get_config()
    if not cfg:
        return None
    url, key = cfg
    payload = _clean_service_payload(data)
    if not payload:
        return get_service(workspace, client, sid)
    try:
        rows = _api(
            "PATCH", url, key,
            "/rest/v1/" + SERVICES_TABLE + "?id=eq." + sid,
            payload,
            profile=schema_for(workspace),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("store: update_service failed: %s", e)
        return None
    # Verify the updated row still belongs to this client.
    found = get_service(workspace, client, sid)
    return found


def delete_service(workspace: str, client: str, sid: str) -> bool:
    """Delete a service (scoped to client)."""
    cfg = get_config()
    if not cfg:
        return False
    url, key = cfg
    try:
        rows = _api(
            "GET", url, key,
            "/rest/v1/" + SERVICES_TABLE + "?select=*&id=eq." + sid,
            profile=schema_for(workspace),
        )
        if not rows or rows[0].get("client_name") != client:
            return False
        _api(
            "DELETE", url, key,
            "/rest/v1/" + SERVICES_TABLE + "?id=eq." + sid,
            profile=schema_for(workspace),
        )
        return True
    except Exception as e:  # noqa: BLE001
        logger.warning("store: delete_service failed: %s", e)
        return False


def get_service(workspace: str, client: str, sid: str) -> dict[str, Any] | None:
    """Fetch one service, scoped to client."""
    cfg = get_config()
    if not cfg:
        return None
    url, key = cfg
    try:
        rows = _api(
            "GET", url, key,
            "/rest/v1/" + SERVICES_TABLE + "?select=*&id=eq." + sid,
            profile=schema_for(workspace),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("store: get_service failed: %s", e)
        return None
    rows = [r for r in rows if r.get("client_name") == client]
    return _norm_service(rows[0]) if rows else None


def service_stats(workspace: str, client: str) -> dict[str, Any]:
    """Aggregate service counts for the client dashboard."""
    services = list_services(workspace, client)
    active = [s for s in services if s["active"]]
    return {
        "total": len(services),
        "active": len(active),
        "inactive": len(services) - len(active),
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
    for k in ("customer_city", "customer_state", "customer_pincode", "source",
              "tracking_number", "carrier", "dispatch_note", "shipped_at",
              "payment_method", "notes"):
        out[k] = s(out.get(k))
    if not out.get("source"):
        out["source"] = "Direct"
    city, state = _norm_city_state(out)
    if city and not out.get("customer_city"):
        out["customer_city"] = city
    if state and not out.get("customer_state"):
        out["customer_state"] = state
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


def _parse_price(product: dict[str, Any]) -> float:
    """Parse a price value that may include ₹ / commas into a float."""
    try:
        return float(str(product.get("price") or "0").replace("₹", "").replace(",", "").strip())
    except (TypeError, ValueError):
        return 0.0


def place_order(workspace: str, client: str, product_id: str | None = None,
                quantity: int = 1, customer: dict[str, Any] | None = None, *,
                items: list[dict[str, Any]] | None = None,
                payment_method: str = "", notes: str = "") -> dict[str, Any] | None:
    """Place an order (public checkout).

    Accepts either a single ``product_id``/``quantity`` (backwards compatible)
    or a list of ``items`` ``[{"product_id": ..., "quantity": ...}]`` for cart
    checkout. Validates every product exists, is active and in stock, decrements
    each product's stock, and records one order row. Returns the created order.
    """
    cfg = get_config()
    if not cfg:
        return None
    url, key = cfg
    customer = customer or {}

    # Normalize requested items into [(product, qty)]
    if not items:
        items = [{"product_id": product_id, "quantity": quantity}]
    requested: list[dict[str, Any]] = []
    for it in items:
        pid = (it or {}).get("product_id")
        q = max(1, int((it or {}).get("quantity") or 1))
        requested.append({"product_id": pid, "quantity": q})

    # Validate + price every line
    resolved: list[dict[str, Any]] = []
    total = 0.0
    for it in requested:
        product = get_product(workspace, client, it["product_id"])
        if not product:
            return {"error": "Product not found"}
        if not product.get("active", True):
            return {"error": f"'{product.get('name', '')}' is not available"}
        try:
            stock = int(product.get("stock") or 0)
        except (TypeError, ValueError):
            stock = 0
        if stock < it["quantity"]:
            return {"error": f"Not enough stock for '{product.get('name', '')}' (only {stock} left)"}
        price = _parse_price(product)
        resolved.append({
            "product": product,
            "quantity": it["quantity"],
            "price": price,
        })
        total += round(price * it["quantity"], 2)
    if not resolved:
        return {"error": "Order has no items"}

    order_number = "ORD-" + str(int(__import__("time").time() * 1000))[-8:]

    loc = parse_location(str(customer.get("address") or ""))
    source = str(customer.get("source") or "").strip() or "Direct"

    payload = {
        "client_name": client,
        "order_number": order_number,
        "product_id": resolved[0]["product"]["id"],
        "product_name": resolved[0]["product"].get("name", ""),
        "quantity": resolved[0]["quantity"],
        "unit_price": resolved[0]["price"],
        "total": total,
        "items": [{
            "product_id": r["product"]["id"],
            "name": r["product"].get("name", ""),
            "price": r["price"],
            "quantity": r["quantity"],
        } for r in resolved],
        "customer_name": str(customer.get("name") or "").strip(),
        "customer_email": str(customer.get("email") or "").strip(),
        "customer_phone": str(customer.get("phone") or "").strip(),
        "customer_address": str(customer.get("address") or "").strip(),
        "customer_city": loc["customer_city"],
        "customer_state": loc["customer_state"],
        "customer_pincode": loc["customer_pincode"],
        "source": source,
        "payment_method": str(payment_method or "").strip() or "COD",
        "notes": str(notes or "").strip(),
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
        # Decrement stock for every line item
        for r in resolved:
            try:
                prod = r["product"]
                cur = int(prod.get("stock") or 0)
                update_product(workspace, client, prod["id"], {"stock": max(0, cur - r["quantity"])})
            except Exception:  # noqa: BLE001
                logger.warning("store: stock decrement failed for %s", r["product"]["id"])
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


def find_order_by_number(workspace: str, client: str, order_number: str) -> dict[str, Any] | None:
    """Fetch one order by its human order number (ORD-xxxx), client-scoped."""
    cfg = get_config()
    if not cfg:
        return None
    import urllib.parse
    url, key = cfg
    try:
        rows = _api(
            "GET", url, key,
            "/rest/v1/" + ORDERS_TABLE + "?select=*&order_number=eq." + urllib.parse.quote(str(order_number)),
            profile=schema_for(workspace),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("store: find_order_by_number failed: %s", e)
        return None
    rows = [r for r in rows if r.get("client_name") == client]
    return _norm_order(rows[0]) if rows else None


def track_order(workspace: str, client: str, order_number: str, email: str) -> dict[str, Any]:
    """Public order tracking: order_number + email must match.

    Returns a safe summary (status, items, total, dispatch/tracking info)
    with no full personal data beyond what ties the order to its buyer.
    """
    order = find_order_by_number(workspace, client, order_number)
    expected = (order.get("customer_email") or "").strip().lower() if order else ""
    if not order or (email or "").strip().lower() != expected:
        return {"error": "Order nahi mila. Order number + email check karke dobara try karo."}
    return {
        "order_number": order["order_number"],
        "status": order["status"],
        "customer_name": order["customer_name"],
        "total": order["total"],
        "items": order["items"],
        "tracking_number": order.get("tracking_number"),
        "carrier": order.get("carrier"),
        "dispatch_note": order.get("dispatch_note"),
        "payment_method": order.get("payment_method") or "",
        "created_at": order.get("created_at"),
        "shipped_at": order.get("shipped_at"),
    }


def update_order_status(workspace: str, client: str, oid: str, status: str,
                        extra: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Update an order's status (owner action).

    Validates the status against the known lifecycle and scopes the update
    to (workspace, client). Optional `extra` may carry dispatch fields
    (tracking_number, carrier, dispatch_note); moving to "shipped" stamps
    shipped_at. Returns the updated order or an error dict.
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
    payload: dict[str, Any] = {"status": status}
    if extra:
        for k in ("tracking_number", "carrier", "dispatch_note"):
            # Only overwrite when the caller actually provides a value.
            # Empty strings would wipe previously recorded dispatch info
            # (e.g. advancing shipped -> delivered without re-sending tracking).
            if k in extra and str(extra[k] or "").strip():
                payload[k] = str(extra[k]).strip()
    if status == "shipped" and not existing.get("shipped_at"):
        payload["shipped_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        rows = _api(
            "PATCH", url, key,
            "/rest/v1/" + ORDERS_TABLE + "?id=eq." + oid,
            payload,
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
    cities = Counter((_norm_city_state(o)[0] or "Unknown") for o in orders)
    states = Counter((_norm_city_state(o)[1] or "Unknown") for o in orders)
    sources = Counter((o.get("source") or "Direct") for o in orders)
    return {
        "revenue": revenue,
        "orders": len(orders),
        "units": units,
        "avg_order": round(revenue / len(orders), 2) if orders else 0.0,
        "top_product": top,
        "status_breakdown": {s: sum(1 for o in orders if (o.get("status") or "placed") == s) for s in {o.get("status") or "placed" for o in orders}},
        "cities": [{"city": c, "orders": n} for c, n in cities.most_common(5)],
        "states": [{"state": s, "orders": n} for s, n in states.most_common(5)],
        "sources": [{"source": s, "orders": n} for s, n in sources.most_common(5)],
        "source": "orders",
    }
