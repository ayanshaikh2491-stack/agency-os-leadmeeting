"""Content Agent comprehensive tests (proper pytest, offline-safe).

Covers the unified tool registry, visual/content tools, brief parser,
production planner, LangGraph pipeline, agency agent, content store,
job queue, API routes, and SKILL.md compliance. No live LLM/network calls.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, ".")


# ── 1. Imports ────────────────────────────────────────────────────────────


def test_imports():
    import admin.tools.visual_tools  # noqa: F401
    import admin.tools.content_tools  # noqa: F401
    import admin.tools.registry  # noqa: F401
    import admin.workspace.agents.content  # noqa: F401
    import admin.agency.content_agent  # noqa: F401
    import admin.workspace.content_store  # noqa: F401
    import admin.tools.content_queue  # noqa: F401
    import admin.api.routes.content  # noqa: F401


# ── 2. Unified tool registry ──────────────────────────────────────────────


def test_registry_counts():
    from admin.tools.registry import get_tool_counts

    counts = get_tool_counts()
    assert counts["total"] == 21
    assert counts["visual"] == 10
    assert counts["content"] == 11


def test_registry_listing():
    from admin.tools.registry import (
        get_all_tools, get_tool_by_name, list_all_tools,
        list_tools_by_category,
    )

    assert len(get_all_tools()) == 21
    listed = list_all_tools()
    assert len(listed) == 21
    categories = {t["category"] for t in listed}
    assert "visual" in categories and "content" in categories
    assert len(list_tools_by_category("visual")) == 10
    assert len(list_tools_by_category("content")) == 11
    tool = get_tool_by_name("discover_brand_identity")
    assert tool["name"] == "discover_brand_identity"
    assert tool["description"] and tool["parameters"]
    assert get_tool_by_name("nonexistent_tool_xyz") is None


# ── 3. Visual tools ───────────────────────────────────────────────────────


def test_visual_tools_registered():
    from admin.tools.visual_tools import VISUAL_TOOLS

    names = [t["function"]["name"] for t in VISUAL_TOOLS]
    assert len(VISUAL_TOOLS) == 10
    expected = [
        "discover_brand_identity", "parse_visual_brief", "plan_visual_production",
        "generate_image_kaggle", "generate_video_kaggle", "generate_ad_image",
        "generate_social_image", "generate_hero_image", "generate_video_ad",
        "batch_generate_images",
    ]
    for name in expected:
        assert name in names


def test_parse_visual_brief():
    from admin.tools.visual_tools import parse_visual_brief

    parsed = parse_visual_brief(
        "Need bold Instagram reels cover images for our new product launch campaign"
    )
    assert parsed["visual_type"] == "video"
    assert parsed["platform"] == "instagram"
    assert parsed["style"] == "bold"

    parsed_ad = parse_visual_brief(
        "Professional Facebook ad creative for our SaaS product launch, 3 images"
    )
    assert parsed_ad["visual_type"] == "image"
    assert parsed_ad["platform"] == "facebook"
    assert parsed_ad["quantity"] == 3


def test_plan_visual_production():
    from admin.tools.visual_tools import parse_visual_brief, plan_visual_production

    brief = parse_visual_brief(
        "Need bold Instagram reels cover images for our new product launch campaign"
    )
    brand = {
        "website_url": "https://example.com",
        "brand_name": "Test Brand",
        "colors": ["#FF6B35"],
        "social_links": {},
        "visual_style": "bold",
    }
    plan = plan_visual_production(brief=brief, brand_identity=brand)
    assert plan["total_items"] > 0
    assert "estimated_gpu_minutes" in plan
    assert isinstance(plan.get("items"), list)
    assert plan["items"][0]["prompt"]
    assert "width" in plan["items"][0] and "height" in plan["items"][0]


# ── 4. Content tools ──────────────────────────────────────────────────────


def test_content_tools_registered():
    from admin.tools.content_tools import CONTENT_TOOLS

    names = [t["name"] for t in CONTENT_TOOLS]
    assert len(CONTENT_TOOLS) == 11
    expected = [
        "analyze_readability", "generate_content_brief", "generate_blog_post",
        "optimize_meta_descriptions", "rewrite_content", "generate_content_calendar",
        "analyze_content_gaps", "search_images", "get_social_image_specs",
        "repurpose_for_social", "generate_ad_copy",
    ]
    for name in expected:
        assert name in names


def test_registry_execution_offline_safe():
    from admin.tools.registry import execute_agent_tool

    result = execute_agent_tool(
        "parse_visual_brief", {"brief_text": "Instagram story image for summer sale"}
    )
    assert result is not None
    result2 = execute_agent_tool(
        "generate_content_brief", {"topic": "digital marketing"}
    )
    assert result2 is not None


# ── 5. LangGraph pipeline ─────────────────────────────────────────────────


def test_content_graph_builds():
    from admin.workspace.agents.content import (
        ContentState, build_content_graph, get_content_graph,
    )

    graph = build_content_graph()
    assert graph is not None
    assert get_content_graph() is not None
    annotations = ContentState.__annotations__
    for field in ["messages", "parsed_brief", "brand_analysis", "visual_plan",
                  "variations", "attempt_count"]:
        assert field in annotations


def test_pipeline_nodes_importable():
    from admin.workspace.agents.content import (  # noqa: F401
        parse_brief, analyze_brand, plan_visual, engineer_prompt, generate, validate,
    )


# ── 6. Agency content agent ───────────────────────────────────────────────


def test_agency_content_agent(tmp_path, monkeypatch):
    # Redirect persistence to a temp dir so the test never pollutes
    # the tracked data/agency_content_agent.json file.
    import admin.agency.content_agent as ca_mod
    monkeypatch.setattr(ca_mod, "_PERSIST_DIR", tmp_path)
    monkeypatch.setattr(ca_mod, "_PERSIST_FILE", tmp_path / "agency_content_agent.json")
    from admin.agency.content_agent import ContentReport, get_agency_content_agent

    agency = get_agency_content_agent()
    assert agency is get_agency_content_agent()  # singleton

    report = ContentReport(
        report_id="test_rpt_1",
        workspace_name="TestWorkspace",
        client_name="TestClient",
        brief_from="seo",
        brief_summary="Create Instagram post images",
        deliverables=["img_1", "img_2"],
        tools_used=["generate_social_image", "discover_brand_identity"],
        prompts_used=["Beautiful sunset over mountains, vibrant colors"],
        platform="instagram",
        visual_type="image",
        gpu_minutes=2.5,
        success=True,
        learnings=["Warm colors work better for travel posts"],
    )
    result = agency.receive_report(report)
    assert result.get("status") == "received"
    assert result.get("total_reports", 0) >= 1

    knowledge = agency.get_knowledge_for_workspace(industry="general", platform="instagram")
    assert "total_reports" in knowledge
    assert "prompt_patterns" in knowledge
    assert "brand_insights" in knowledge

    assert isinstance(agency.get_best_prompts(visual_type="image", top_n=3), list)
    stats = agency.get_stats()
    assert "total_reports" in stats and "platforms_active" in stats
    assert hasattr(agency, "_save") and hasattr(agency, "_load")
    agency._save()


# ── 7. Workspace content store ────────────────────────────────────────────


def test_workspace_content_store(tmp_path, monkeypatch):
    # Redirect both the workspace store and the agency agent persistence to
    # temp dirs so this test never writes to tracked data/ files.
    import admin.agency.content_agent as ca_mod
    monkeypatch.setattr(ca_mod, "_PERSIST_DIR", tmp_path)
    monkeypatch.setattr(ca_mod, "_PERSIST_FILE", tmp_path / "agency_content_agent.json")
    import admin.workspace.content_store as cs_mod
    monkeypatch.setattr(cs_mod, "_DATA_DIR", tmp_path)
    monkeypatch.setattr(cs_mod, "_AGENTS_DIR", tmp_path / "agents")
    monkeypatch.setattr(cs_mod, "_store", None)  # recreate with temp dirs
    from admin.workspace.content_store import get_content_store

    store = get_content_store()
    assert store is get_content_store()  # singleton
    mem = store.get_or_create("test_ws_001", "TestWorkspace", "TestClient", "tech")
    assert mem.workspace_id == "test_ws_001"
    assert mem.client_name == "TestClient"

    store.record_success(
        workspace_id="test_ws_001", job_id="job_test_001",
        brief_summary="Create IG post", deliverables=["img1.png"],
        prompts_used=["prompt 1"], platform="instagram", visual_type="image",
        gpu_minutes=1.5, learnings=["Warm tones worked well"],
    )
    store.record_failure(
        workspace_id="test_ws_001", job_id="job_test_002",
        brief_summary="Create video", error="GPU timeout", platform="instagram",
        visual_type="video", what_failed="CogVideoX generation",
        avoid_next_time="Use shorter frame count",
    )
    assert len(store.get_memory_summary("test_ws_001")) > 0
    stats = store.get_stats("test_ws_001")
    assert stats.get("success_count", 0) >= 1
    assert stats.get("failure_count", 0) >= 1
    store.record_style_preference("test_ws_001", "bold", 0.9)
    store.record_variation(
        "test_ws_001", "Test brief",
        [{"prompt": "test prompt", "platform": "instagram"}], [0.85],
    )


# ── 8. Content job queue ──────────────────────────────────────────────────


def test_content_job_queue():
    from admin.tools.content_queue import (
        ContentBrief, ContentJobQueue, JobStatus, enhance_brief, get_queue,
    )

    queue = get_queue("test_ws_001")
    assert isinstance(queue, ContentJobQueue)

    brief = ContentBrief(
        workspace_id="test_ws_001", from_agent="social", content_type="social_post",
        platform="instagram", style="bold", topic="Summer sale campaign",
        quantity=3, priority="high",
    )
    job_id = queue.submit(brief)
    assert job_id.startswith("job_")

    q_status = queue.get_queue_status()
    assert "pending" in q_status and "gpu_busy" in q_status

    next_job = queue.get_next()
    assert next_job.status == JobStatus.RUNNING
    assert next_job.platform == "instagram"
    queue.complete(job_id=job_id, output_files=["output_001.png"])
    assert len(queue.list_recent(limit=5)) > 0

    enhanced = enhance_brief(
        brief=ContentBrief(
            content_type="social_post", platform="instagram", style="bold",
            topic="Summer sale",
        ),
        client_context={
            "brand_colors": ["#FF6B35", "#004E89"],
            "industry": "ecommerce",
            "target_audience": "young adults",
        },
    )
    assert enhanced.enhanced_prompt
    assert enhanced.width == 1080 and enhanced.height == 1080
    assert enhanced.brand_colors_used == ["#FF6B35", "#004E89"]


# ── 9. API routes ─────────────────────────────────────────────────────────


def test_content_api_routes():
    from admin.api.routes.content import router

    paths = [r.path for r in router.routes if hasattr(r, "path")]
    required = [
        "/api/content/chat", "/api/content/init", "/api/content/discover-brand",
        "/api/content/generate-image", "/api/content/generate-video",
        "/api/content/generate-ad", "/api/content/generate-social",
        "/api/content/generate-hero", "/api/content/tools/all",
        "/api/content/analyze-readability", "/api/content/blog-post",
        "/api/content/calendar", "/api/content/rewrite",
        "/api/content/meta-optimize", "/api/content/content-gaps",
        "/api/content/agency/stats", "/api/content/agency/knowledge",
        "/api/content/agency/best-prompts", "/api/content/queue/status",
        "/api/content/brief", "/api/content/generate-variations",
        "/api/content/select-variation", "/api/content/generate-ugc",
        "/api/content/generate-marketing", "/api/content/batch-generate",
    ]
    for route in required:
        assert route in paths, f"missing route {route}"


# ── 10. SKILL.md compliance ───────────────────────────────────────────────


def test_skill_md_compliance():
    skill_path = Path("admin/skills/content/SKILL.md")
    skill_md = skill_path.read_text(encoding="utf-8")
    lower = skill_md.lower()
    assert "VISUAL ONLY" in skill_md or "visual only" in lower
    assert "Does NOT Do" in skill_md
    assert "Kaggle" in skill_md
    assert "FLUX" in skill_md
    assert "brand" in lower and "discover" in lower
    assert "brief" in lower and "domain agent" in lower
    assert "agency" in lower and "learning" in lower
    assert "queue" in lower
    assert "CEO" in skill_md or "approval" in lower
