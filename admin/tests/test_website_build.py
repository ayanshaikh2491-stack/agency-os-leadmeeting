"""Website Agent — real website builder tests (local-only, deterministic)."""
import asyncio
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from admin.tools.website_tools import _build_website_project, _escape_html, _slugify


# ── _build_website_project ───────────────────────────────────────────────────

def test_builder_nextjs_files_contain_business_info():
    project = _build_website_project(
        title="Acme Bakery",
        tagline="Fresh bread daily",
        services=["Cakes", "Pastries", "Catering"],
        business_email="hello@acme.example",
        sections=["hero", "services", "contact", "footer"],
        framework="nextjs",
    )
    assert project["framework"] == "nextjs"
    assert project["title"] == "Acme Bakery"
    files = project["files"]
    for rel in ["package.json", "app/page.tsx", "app/layout.tsx", "app/globals.css", "README.md", "components/Services.tsx", "components/Contact.tsx"]:
        assert rel in files, rel
    page = files["app/page.tsx"]
    assert "Acme Bakery" in page
    services_tsx = files["components/Services.tsx"]
    assert "Cakes" in services_tsx and "Pastries" in services_tsx
    contact_tsx = files["components/Contact.tsx"]
    assert "hello@acme.example" in contact_tsx


def test_builder_html_files_contain_escaped_title():
    project = _build_website_project(
        title="Portfolio",
        sections=["hero", "footer"],
        framework="html",
    )
    assert "index.html" in project["files"]
    assert "style.css" in project["files"]
    html = project["files"]["index.html"]
    assert "Portfolio" in html


def test_builder_escapes_injection_in_layout():
    project = _build_website_project(title='<script>alert(1)</script> & "x"', sections=["hero"])
    layout = project["files"]["app/layout.tsx"]
    assert "<script>" not in layout
    assert "&lt;script&gt;" in layout


def test_builder_services_fallback_and_skills_bias():
    project = _build_website_project(title="T", skills=["nextjs-developer", "frontend-design"])
    assert project["framework"] == "nextjs"
    assert project["services"], "default services fallback expected"
    assert "nextjs-developer" in project["skills_applied"]


def test_slugify_and_escape_helpers():
    assert _slugify("Acme Bakery!") == "acme-bakery"
    assert _escape_html("<b>&\"x\"</b>") == "&lt;b&gt;&amp;&quot;x&quot;&lt;/b&gt;"
