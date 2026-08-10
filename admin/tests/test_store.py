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
