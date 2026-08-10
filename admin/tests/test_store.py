"""Client Store — products + settings store and website sync tests.

Local-only and deterministic: the store module is mocked, the website
builder runs offline.
"""
import os
import sys
from unittest import mock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from admin.store import store_store
from admin.tools import website_tools

SAMPLE_PRODUCTS = [
    {
        "name": "Wireless Headphones",
        "description": "Noise-cancelling, 30h battery",
        "price": "4999",
        "image_url": "https://example.com/hp.jpg",
        "stock": 12,
        "active": True,
    },
    {
        "name": "Smart Watch",
        "description": "Fitness tracking, AMOLED",
        "price": "3499",
        "image_url": "",
        "stock": 0,
        "active": True,
    },
]


# ── product normalization ────────────────────────────────────────────────────

def test_norm_product_coerces_types():
    raw = {
        "name": "Widget",
        "price": 1499,  # json-normalized number
        "stock": "5",
        "active": True,
        "image_url": None,
        "featured": False,
        "sort_order": "3",
    }
    p = store_store._norm_product(raw)
    assert p["name"] == "Widget"
    assert p["price"] == "1499"
    assert p["stock"] == 5
    assert p["active"] is True
    assert p["image_url"] == ""
    assert p["sort_order"] == 3


def test_clean_payload_drops_unknown_keys():
    payload = store_store._clean_payload({"name": "X", "price": "10", "created_at": "t", "id": "abc"})
    assert "name" in payload and "price" in payload
    assert "id" not in payload and "created_at" not in payload


def test_list_products_requires_config():
    with mock.patch.object(store_store, "get_config", return_value=None):
        assert store_store.list_products("ws_x", "Client") == []


def test_list_products_active_only_filters():
    rows = [dict(SAMPLE_PRODUCTS[0], active=False), dict(SAMPLE_PRODUCTS[1])]
    with mock.patch.object(store_store, "get_config", return_value=("http://x:8050", "key")), \
         mock.patch.object(store_store, "_api", return_value=rows):
        all_p = store_store.list_products("ws_x", "C")
        active = store_store.list_products("ws_x", "C", active_only=True)
    assert len(all_p) == 2
    assert len(active) == 1 and active[0]["name"] == "Smart Watch"


# ── settings ─────────────────────────────────────────────────────────────────

def test_get_settings_merges_defaults():
    with mock.patch.object(store_store, "get_config", return_value=("http://x:8050", "key")), \
         mock.patch.object(store_store, "_api", return_value=[{"store_name": "My Shop", "show_stock": False}]):
        s = store_store.get_settings("ws_x", "C")
    assert s["store_name"] == "My Shop"
    assert s["show_stock"] is False
    assert s["category"] == "ecommerce"  # default preserved


# ── website builder with real products ───────────────────────────────────────

def test_builder_nextjs_renders_store_products():
    project = website_tools._build_website_project(
        title="Test Store",
        category="ecommerce",
        framework="nextjs",
        products=SAMPLE_PRODUCTS,
    )
    comp = project["files"]["components/Products.tsx"]
    assert "Wireless Headphones" in comp
    assert "https://example.com/hp.jpg" in comp      # image renders
    assert "In stock" in comp and "Out of stock" in comp


def test_builder_html_renders_store_products():
    project = website_tools._build_website_project(
        title="Test Store",
        category="ecommerce",
        framework="html",
        products=SAMPLE_PRODUCTS,
    )
    combined = project["files"]["index.html"] + project["files"]["shop.html"]
    assert "product-img" in combined
    assert "https://example.com/hp.jpg" in combined
    assert "In stock" in combined and "Out of stock" in combined


def test_builder_escapes_product_fields():
    evil = [{"name": "<script>alert(1)</script>", "description": "\"><img src=x>", "price": "10"}]
    project = website_tools._build_website_project(
        title="S", category="ecommerce", framework="html", products=evil,
    )
    html = project["files"]["index.html"]
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


# ── build_site_from_store (deploy=False) ─────────────────────────────────────

def test_build_site_from_store_composes():
    settings = {
        "store_name": "Demo Store",
        "tagline": "Fresh",
        "category": "ecommerce",
        "style": "modern",
        "color_primary": "#7C3AED",
        "framework": "html",
        "contact_email": "x@y.com",
    }
    with mock.patch.object(store_store, "get_config", return_value=("http://x:8050", "key")), \
         mock.patch.object(store_store, "list_products", return_value=SAMPLE_PRODUCTS), \
         mock.patch.object(store_store, "get_settings", return_value=settings):
        res = website_tools.build_site_from_store("ws_demo", "Demo Client", deploy=False)
    assert res["title"] == "Demo Store"
    assert res["product_count"] == 2
    assert res["deployed"] is False
    assert res["framework"] == "html"


# ── orders + status lifecycle ────────────────────────────────────────────────

ORDER_ROW = {
    "id": "ord1",
    "client_name": "C",
    "order_number": "ORD-12345678",
    "customer_name": "Rahul",
    "customer_email": "rahul@example.com",
    "customer_phone": "+919999999999",
    "customer_address": "Mumbai",
    "total": 499.0,
    "status": "placed",
    "items": [{"product_id": "p1", "name": "Widget", "price": 499.0, "quantity": 1}],
}


def test_norm_order_coerces_types():
    o = store_store._norm_order(dict(ORDER_ROW))
    assert o["order_number"] == "ORD-12345678"
    assert o["total"] == 499.0
    assert o["status"] == "placed"
    assert o["customer_phone"] == "+919999999999"
    assert isinstance(o["items"], list) and len(o["items"]) == 1


def test_update_order_status_validates():
    with mock.patch.object(store_store, "get_config", return_value=("http://x:8050", "key")):
        r = store_store.update_order_status("ws_x", "C", "ord1", "not-a-status")
    assert "error" in r and "Invalid status" in r["error"]


def test_update_order_status_missing_config():
    with mock.patch.object(store_store, "get_config", return_value=None):
        assert store_store.update_order_status("ws_x", "C", "ord1", "shipped") is None


def test_update_order_status_success():
    updated = dict(ORDER_ROW, status="shipped")
    with mock.patch.object(store_store, "get_config", return_value=("http://x:8050", "key")), \
         mock.patch.object(store_store, "get_order", return_value=dict(ORDER_ROW)), \
         mock.patch.object(store_store, "_api", return_value=[updated]):
        r = store_store.update_order_status("ws_x", "C", "ord1", "shipped")
    assert r["status"] == "shipped"
    assert r["order_number"] == "ORD-12345678"


def test_update_order_status_fallback_after_empty_patch():
    with mock.patch.object(store_store, "get_config", return_value=("http://x:8050", "key")), \
         mock.patch.object(store_store, "get_order", side_effect=[dict(ORDER_ROW), dict(ORDER_ROW, status="delivered")]), \
         mock.patch.object(store_store, "_api", return_value=[]):
        r = store_store.update_order_status("ws_x", "C", "ord1", "delivered")
    assert r["status"] == "delivered"


# ── location parsing + source (kaha se order aaya) ───────────────────────────

def test_parse_location_bengaluru_pincode():
    loc = store_store.parse_location("42 Test Lane, Bengaluru, Karnataka 560001")
    assert loc["customer_pincode"] == "560001"
    assert loc["customer_city"] == "Bengaluru"
    assert loc["customer_state"] == "Karnataka"


def test_parse_location_state_abbreviation():
    loc = store_store.parse_location("Hinjewadi Phase 2, Pune, MH 411057")
    assert loc["customer_pincode"] == "411057"
    assert loc["customer_city"] == "Pune"
    assert loc["customer_state"] == "Maharashtra"


def test_parse_location_empty():
    assert store_store.parse_location("") == {"customer_city": "", "customer_state": "", "customer_pincode": ""}
    assert store_store.parse_location(None)["customer_city"] == ""


def test_parse_location_city_fallback_without_pincode():
    # No pincode, no state → last comma segment becomes the city.
    loc = store_store.parse_location("Shop 5, MG Road, Indore")
    assert loc["customer_city"] == "Indore"
    assert loc["customer_state"] == ""


def test_place_order_stores_location_and_source():
    created = dict(ORDER_ROW,
                   customer_address="42 Test Lane, Bengaluru, Karnataka 560001",
                   customer_city="Bengaluru", customer_state="Karnataka",
                   customer_pincode="560001", source="Instagram")
    with mock.patch.object(store_store, "get_config", return_value=("http://x:8050", "key")), \
         mock.patch.object(store_store, "get_product", return_value={
             "id": "p1", "name": "Widget", "price": "499", "stock": 5, "active": True,
         }), \
         mock.patch.object(store_store, "update_product", return_value=None), \
         mock.patch.object(store_store, "_api", return_value=[created]):
        r = store_store.place_order("ws_x", "C", "p1", 1, {
            "name": "Rahul", "email": "r@x.com", "phone": "+919999999999",
            "address": "42 Test Lane, Bengaluru, Karnataka 560001", "source": "Instagram",
        })
    assert r["customer_city"] == "Bengaluru"
    assert r["customer_state"] == "Karnataka"
    assert r["customer_pincode"] == "560001"
    assert r["source"] == "Instagram"


def test_norm_order_default_source_direct():
    o = store_store._norm_order(dict(ORDER_ROW))
    assert o["source"] == "Direct"
    # "Mumbai" address: no pincode/state → city fallback picks it
    assert o["customer_city"] == "Mumbai"

    o2 = store_store._norm_order(dict(ORDER_ROW, customer_address="42 Test Lane, Bengaluru, Karnataka 560001"))
    assert o2["customer_city"] == "Bengaluru"
    assert o2["customer_state"] == "Karnataka"


# ── dispatch + tracking ──────────────────────────────────────────────────────

def test_update_order_status_with_tracking():
    shipped = dict(ORDER_ROW, status="shipped", tracking_number="DL123456789IN",
                   carrier="DTDC", shipped_at="2026-08-10T00:00:00Z")
    with mock.patch.object(store_store, "get_config", return_value=("http://x:8050", "key")), \
         mock.patch.object(store_store, "get_order", return_value=dict(ORDER_ROW)), \
         mock.patch.object(store_store, "_api", return_value=[shipped]):
        r = store_store.update_order_status("ws_x", "C", "ord1", "shipped",
                                            extra={"tracking_number": "DL123456789IN", "carrier": "DTDC"})
    assert r["status"] == "shipped"
    assert r["tracking_number"] == "DL123456789IN"
    assert r["carrier"] == "DTDC"
    assert r["shipped_at"]


def test_update_order_status_sets_shipped_at_on_first_ship():
    shipped = dict(ORDER_ROW, status="shipped", tracking_number="T1", shipped_at="2026-08-10T00:00:00Z")
    with mock.patch.object(store_store, "get_config", return_value=("http://x:8050", "key")), \
         mock.patch.object(store_store, "get_order", return_value=dict(ORDER_ROW)), \
         mock.patch.object(store_store, "_api", return_value=[shipped]) as api_mock:
        store_store.update_order_status("ws_x", "C", "ord1", "shipped", extra={"tracking_number": "T1"})
    # _api("PATCH", url, key, path, payload, profile=...) → payload is args[4]
    payload = api_mock.call_args[0][4]
    assert "shipped_at" in payload
    assert payload["tracking_number"] == "T1"


def test_update_order_status_plain_status_keeps_dispatch_info():
    """Status-only updates (empty dispatch fields) must NOT wipe tracking."""
    existing = dict(ORDER_ROW, status="shipped", tracking_number="T9", carrier="DTDC",
                    dispatch_note="via hub", shipped_at="2026-08-10T00:00:00Z")
    with mock.patch.object(store_store, "get_config", return_value=("http://x:8050", "key")), \
         mock.patch.object(store_store, "get_order", return_value=existing), \
         mock.patch.object(store_store, "_api", return_value=[dict(existing, status="delivered")]) as api_mock:
        r = store_store.update_order_status("ws_x", "C", "ord1", "delivered",
                                            extra={"tracking_number": "", "carrier": "", "dispatch_note": ""})
    # Payload must not contain empty dispatch keys that would erase tracking.
    payload = api_mock.call_args[0][4]
    assert "tracking_number" not in payload
    assert "carrier" not in payload
    assert "dispatch_note" not in payload
    assert r["tracking_number"] == "T9"
    assert r["carrier"] == "DTDC"


def test_track_order_match_and_mismatch():
    with mock.patch.object(store_store, "get_config", return_value=("http://x:8050", "key")), \
         mock.patch.object(store_store, "_api", return_value=[dict(ORDER_ROW, tracking_number="T9", carrier="DTDC")]):
        ok = store_store.track_order("ws_x", "C", "ORD-12345678", "rahul@example.com")
        assert ok["order_number"] == "ORD-12345678"
        assert ok["tracking_number"] == "T9"
        assert "customer_email" not in ok  # safe summary, no PII leak

        bad = store_store.track_order("ws_x", "C", "ORD-12345678", "wrong@example.com")
        assert "error" in bad


# ── sales stats: location + source breakdown ─────────────────────────────────

def test_sales_stats_includes_cities_and_sources():
    rows = [
        dict(ORDER_ROW, customer_city="Bengaluru", customer_state="Karnataka", source="Instagram", total=499.0),
        dict(ORDER_ROW, customer_city="Mumbai", customer_state="Maharashtra", source="Direct", total=799.0),
        dict(ORDER_ROW, customer_city="Bengaluru", customer_state="Karnataka", source="Instagram", total=499.0),
    ]
    with mock.patch.object(store_store, "get_config", return_value=("http://x:8050", "key")), \
         mock.patch.object(store_store, "_api", return_value=rows):
        s = store_store.sales_stats("ws_x", "C")
    assert s["source"] == "orders"
    assert s["cities"][0]["city"] == "Bengaluru" and s["cities"][0]["orders"] == 2
    assert s["sources"][0]["source"] == "Instagram"
    assert any(st["state"] == "Karnataka" for st in s["states"])
