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
    layout = files["app/layout.tsx"]
    assert "Acme Bakery" in layout
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


# ── build_site ────────────────────────────────────────────────────────────────

from admin.tools.website_tools import WEBSITE_TOOLS, build_site, execute_website_tool


def test_build_site_writes_real_files(tmp_path):
    result = build_site(
        title="Acme Bakery",
        tagline="Fresh bread daily",
        services="Cakes, Pastries, Catering",
        business_email="hello@acme.example",
        output_dir=str(tmp_path),
        framework="nextjs",
    )
    assert result["status"] == "built"
    for rel in ["package.json", "app/page.tsx", "app/layout.tsx", "app/globals.css", "README.md"]:
        assert os.path.isfile(os.path.join(str(tmp_path), rel)), rel
    page = (tmp_path / "app" / "page.tsx").read_text(encoding="utf-8")
    layout = (tmp_path / "app" / "layout.tsx").read_text(encoding="utf-8")
    assert "Acme Bakery" in layout
    contact = (tmp_path / "components" / "Contact.tsx").read_text(encoding="utf-8")
    assert "hello@acme.example" in contact


def test_build_site_html_variant_writes_files(tmp_path):
    result = build_site(title="Portfolio", framework="html", output_dir=str(tmp_path))
    assert os.path.isfile(os.path.join(str(tmp_path), "index.html"))
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "Portfolio" in html
    assert os.path.isfile(os.path.join(str(tmp_path), "style.css"))


def test_build_site_custom_color_and_services(tmp_path):
    result = build_site(
        title="SaaS Flow",
        tagline="Automate everything",
        services="Analytics, Automation, Reports",
        business_email="team@saasflow.example",
        color_primary="#FF5500",
        output_dir=str(tmp_path),
    )
    globals_css = (tmp_path / "app" / "globals.css").read_text(encoding="utf-8")
    assert "#FF5500" in globals_css
    services_tsx = (tmp_path / "components" / "Services.tsx").read_text(encoding="utf-8")
    assert "Analytics" in services_tsx and "Reports" in services_tsx


def test_build_site_registered_and_dispatchable(tmp_path):
    names = {t["function"]["name"] for t in WEBSITE_TOOLS}
    assert "build_site" in names
    out = execute_website_tool("build_site", {"title": "X", "output_dir": str(tmp_path)})
    assert out["status"] == "built"
    assert os.path.isfile(os.path.join(str(tmp_path), "app", "page.tsx"))
    assert out["file_count"] >= 7


# ── generate_code ──────────────────────────────────────────────────────────

def test_generate_code_backward_compatible_and_writes(tmp_path):
    from admin.tools.website_tools import generate_code

    out = generate_code(title="Acme", sections="hero,features,cta,footer", framework="nextjs")
    assert out["page_code"]
    assert out["framework"] == "nextjs"
    assert out["title"] == "Acme"
    assert "components" in out
    assert out["components"]

    out2 = generate_code(
        title="Acme Services",
        services="Design, SEO",
        business_email="hi@acme.example",
        output_dir=str(tmp_path),
        skills=["nextjs-developer"],
    )
    assert out2["status"] == "built"
    assert os.path.isfile(os.path.join(str(tmp_path), "app", "page.tsx"))
    html_path = tmp_path / "index.html"
    # html framework still works
    out3 = generate_code(framework="html", title="Static", output_dir=str(tmp_path / "static"))
    assert (tmp_path / "static" / "index.html").is_file()


# ── Categories: multi-page website builder ──────────────────────────────────

from admin.tools.website_tools import WEBSITE_CATEGORIES, _category_data


def test_categories_registry_has_expected_types():
    for cat in ["business", "portfolio", "restaurant", "ecommerce", "saas", "agency",
                "realestate", "blog", "education", "health", "event", "hotel",
                "construction", "nonprofit"]:
        assert cat in WEBSITE_CATEGORIES, cat
    # every category has 4+ pages and every page has sections
    for cat, spec in WEBSITE_CATEGORIES.items():
        assert spec["label"]
        assert len(spec["pages"]) >= 4, cat
        for route, page in spec["pages"].items():
            assert page["nav"]
            assert page["sections"], (cat, route)


def test_category_content_fills_used_sections():
    for cat in WEBSITE_CATEGORIES:
        data = _category_data(cat)
        used = {s for page in WEBSITE_CATEGORIES[cat]["pages"].values() for s in page["sections"]}
        for sec in used:
            if sec in {"hero", "hero_small", "services", "about", "testimonials",
                       "contact", "footer", "cta", "pricing", "booking", "newsletter", "donate"}:
                continue  # static sections need no content
            key = {"menu": "menu_items", "courses": "courses", "rooms": "rooms",
                   "features": "features_custom"}.get(sec, sec)
            assert data.get(key), (cat, sec)


def test_each_category_builds_multi_page_html():
    for cat in WEBSITE_CATEGORIES:
        project = _build_website_project(title=f"Site {cat}", category=cat, framework="html")
        routes = {pg["route"] for pg in project["pages"]}
        assert "index" in routes
        for r in routes:
            fname = "index.html" if r == "index" else f"{r}.html"
            assert fname in project["files"], (cat, fname)
        # nav links exist on every page
        for r in routes:
            fname = "index.html" if r == "index" else f"{r}.html"
            html = project["files"][fname]
            for other in routes:
                other_f = "index.html" if other == "index" else f"{other}.html"
                if other_f != fname:
                    assert f'href="{other_f}"' in html, (cat, fname, other_f)
        assert "style.css" in project["files"]


def test_each_category_builds_multi_page_nextjs():
    for cat in WEBSITE_CATEGORIES:
        project = _build_website_project(title=f"Site {cat}", category=cat, framework="nextjs")
        routes = {pg["route"] for pg in project["pages"]}
        for r in routes:
            pname = "app/page.tsx" if r == "index" else f"app/{r}/page.tsx"
            assert pname in project["files"], (cat, pname)
        assert "components/Navbar.tsx" in project["files"]
        assert "components/Footer.tsx" in project["files"]
        layout = project["files"]["app/layout.tsx"]
        assert "<Navbar />" in layout and "<Footer />" in layout
        for s in project["sections"]:
            comp = f'components/{s.title().replace(" ", "")}.tsx'
            assert comp in project["files"], (cat, comp)


def test_restaurant_has_menu_and_hours_content():
    project = _build_website_project(title="Spice Garden", category="restaurant", framework="html")
    assert "menu.html" in project["files"]
    menu = project["files"]["menu.html"]
    assert "Our Menu" in menu
    assert "Margherita Pizza" in menu
    assert "₹349" in menu
    hours = project["files"]["index.html"]
    assert "Mon-Sun 11:00 AM - 11:00 PM" in hours
    assert "12 Park Street, Mumbai" in hours


def test_ecommerce_has_shop_page_and_products():
    project = _build_website_project(title="Store", category="ecommerce", framework="html")
    assert "shop.html" in project["files"]
    shop = project["files"]["shop.html"]
    assert "Wireless Headphones" in shop
    assert "₹4,999" in shop
    # nextjs route exists too
    pj = _build_website_project(title="Store", category="ecommerce", framework="nextjs")
    assert "app/shop/page.tsx" in pj["files"]


def test_category_specific_content_per_category():
    checks = {
        "saas": ("features_custom", "Analytics"),
        "hotel": ("rooms", "Deluxe Room"),
        "education": ("courses", "Web Development Bootcamp"),
        "realestate": ("listings", "Skyline Apartment"),
        "blog": ("posts", "scaled to 1M"),
        "nonprofit": ("projects", "School Meals Program"),
    }
    for cat, (key, needle) in checks.items():
        project = _build_website_project(title=f"X {cat}", category=cat, framework="html")
        blob = "\n".join(project["files"].values())
        assert needle in blob, (cat, key)


def test_invalid_category_falls_back_to_business():
    project = _build_website_project(title="X", category="does-not-exist")
    assert project["category"] == "business"
    assert any(pg["route"] == "services" for pg in project["pages"])


def test_legacy_single_page_still_works():
    project = _build_website_project(
        title="Single", sections="hero,services,contact,footer", framework="html"
    )
    assert project["pages"] == [{"route": "index", "nav": "Home", "sections": ["hero", "services", "contact", "footer"]}]
    assert "index.html" in project["files"]
    assert "menu.html" not in project["files"]
    assert "services.html" not in project["files"]


def test_build_site_accepts_category(tmp_path):
    result = build_site(title="Pizza Palace", category="restaurant", framework="html", output_dir=str(tmp_path))
    assert result["status"] == "built"
    assert result["category"] == "restaurant"
    assert os.path.isfile(os.path.join(str(tmp_path), "menu.html"))
    assert os.path.isfile(os.path.join(str(tmp_path), "index.html"))
    assert "Margherita Pizza" in (tmp_path / "menu.html").read_text(encoding="utf-8")


def test_build_site_default_category_is_business(tmp_path):
    result = build_site(title="Corp Co", framework="html", output_dir=str(tmp_path))
    assert result["category"] == "business"
    assert os.path.isfile(os.path.join(str(tmp_path), "services.html"))
    assert os.path.isfile(os.path.join(str(tmp_path), "about.html"))


def test_tool_registry_exposes_category():
    names = {t["function"]["name"] for t in WEBSITE_TOOLS}
    for tool_name in ["build_site", "publish_site"]:
        assert tool_name in names
        tool = next(t for t in WEBSITE_TOOLS if t["function"]["name"] == tool_name)
        props = tool["function"]["parameters"]["properties"]
        assert "category" in props, tool_name
        assert props["category"]["default"] == "business"


def test_publish_site_dispatch_passes_category(monkeypatch, tmp_path):
    from admin.tools import website_tools as wt

    captured = {}

    def fake_build(**kwargs):
        captured.update(kwargs)
        return {"status": "built", "title": "Taco Place", "category": "restaurant",
                "output_dir": str(tmp_path), "files": {}, "framework": "html"}

    def fake_deploy(**kwargs):
        return {"status": "deployed", "url": "https://taco-place.vercel.app"}

    monkeypatch.setattr(wt, "build_site", fake_build)
    monkeypatch.setattr(wt, "deploy_vercel", fake_deploy)
    out = execute_website_tool("publish_site", {"title": "Taco Place", "category": "restaurant", "framework": "html"})
    assert out["status"] == "published"
    assert captured.get("category") == "restaurant"


# ── Task 4: LangGraph loop (tool results reach the LLM) ─────────────────────

from admin.workspace.agents.website import WebsiteAgent, build_website_graph, website_route


def test_route_sends_tool_results_back_to_llm():
    state = {
        "messages": [{"role": "tool", "tool_call_id": "call_1", "content": '{"status":"built"}'}],
        "tool_round": 1,
    }
    assert website_route(state) == "call_llm"


def test_route_executes_pending_tool_calls():
    state = {
        "messages": [{"role": "assistant", "content": "", "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "build_site", "arguments": "{}"}}]}],
        "tool_round": 1,
    }
    assert website_route(state) == "run_tools"


def test_route_finalizes_on_plain_answer():
    state = {"messages": [{"role": "assistant", "content": "Here is your website."}], "tool_round": 1}
    assert website_route(state) == "finalize"


def test_route_finalizes_on_round_cap():
    state = {"messages": [{"role": "tool", "tool_call_id": "c", "content": "x"}], "tool_round": 8}
    assert website_route(state) == "finalize"


# ── full graph loop (fake LLM, no network) ────────────────────────────────────

class _FakeChoice:
    class _Msg:
        def __init__(self, content, tool_calls):
            self.content = content
            self.tool_calls = tool_calls

    def __init__(self, content, tool_calls):
        self.message = self._Msg(content, tool_calls)


class _FakeResp:
    def __init__(self, content, tool_calls):
        self.choices = [_FakeChoice(content, tool_calls)]


class _FakeTC:
    def __init__(self, name, arguments):
        self.id = "call_fake"
        self.type = "function"
        self.function = type("F", (), {"name": name, "arguments": arguments})()


class _FakeCompletions:
    def __init__(self, calls):
        self.calls = calls
        self.idx = 0

    def create(self, **kwargs):
        r = self.calls[min(self.idx, len(self.calls) - 1)]
        self.idx += 1
        return r


class _FakeClient:
    def __init__(self, calls):
        self.chat = type("C", (), {"completions": _FakeCompletions(calls)})()


def test_full_graph_loop_feeds_tool_result_back(monkeypatch, tmp_path):
    import admin.workspace.agents.website as wsmod

    fake = _FakeClient([
        _FakeResp("", [_FakeTC("build_site", json.dumps({"title": "LoopCo", "output_dir": str(tmp_path)}))]),
        _FakeResp("Done! I built the LoopCo site. Files are in the output directory.", []),
    ])
    monkeypatch.setattr(wsmod, "_get_llm_client", lambda: fake)

    graph = build_website_graph()
    state = {
        "messages": [{"role": "user", "content": "build a website for LoopCo"}],
        "workspace_name": "test",
        "client_name": "Client",
        "skills_meta": "",
        "tool_round": 0,
        "final_output": "",
        "error": None,
        "thinking_phases": [],
    }
    result = asyncio.run(graph.ainvoke(state, config={"configurable": {"thread_id": "t1"}}))
    assert "LoopCo" in result["final_output"]
    assert (tmp_path / "app" / "page.tsx").is_file()


# ── Task 5: thinking phases + reasoning chain wired into chat ───────────────

def test_build_thinking_phases_local_fallback(monkeypatch):
    import admin.workspace.agents.website_reasoning_chain as wrc
    monkeypatch.setattr(wrc, "_llm_call", lambda *a, **k: '{"error": "no llm"}')

    agent = WebsiteAgent(workspace_name="w", client_name="c")
    phases = agent._build_thinking_phases("build a website for my bakery", "Website built.", skills=["frontend-design"])
    assert len(phases) == 5
    assert phases[0]["phase"] == "understand"
    assert "DEVELOP" in phases[0]["summary"]
    assert all("phase" in p and "summary" in p for p in phases)


def test_chat_returns_phases_tuple(monkeypatch):
    import admin.workspace.agents.website_reasoning_chain as wrc
    monkeypatch.setattr(wrc, "_llm_call", lambda *a, **k: '{"error": "no llm"}')

    agent = WebsiteAgent(workspace_name="w", client_name="c")

    class _FakeGraph:
        async def ainvoke(self, state, config=None):
            return {"final_output": "Site ready.", "error": None}

    agent._graph = _FakeGraph()
    out, phases = asyncio.run(agent.chat("build a site", skills=["nextjs-developer"]))
    assert out == "Site ready."
    assert isinstance(phases, list)
    assert len(phases) == 5


# ── Task 6: routes — /build-site, /skills, chat returns phases + skills ─────

def test_routes_exist_and_skills_endpoint(monkeypatch):
    import admin.api.routes.website as wroutes

    # FastAPI route registration checks (prefix is included in route paths)
    route_paths = [r.path for r in wroutes.router.routes]
    assert "/api/website/build-site" in route_paths
    assert "/api/website/skills" in route_paths

    # /skills handler returns the registry
    resp = asyncio.run(wroutes.list_skills())
    assert resp["success"] is True
    names = {s["name"] for s in resp["data"]["skills"]}
    assert "frontend-design" in names
    assert "nextjs-developer" in names
