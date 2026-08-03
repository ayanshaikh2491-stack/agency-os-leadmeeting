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
    assert "Acme Bakery" in page
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
