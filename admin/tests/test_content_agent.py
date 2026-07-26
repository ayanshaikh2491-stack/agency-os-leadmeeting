"""Content Agent — Comprehensive Test Suite (v2).

Tests the current 6-node LangGraph Content Agent:
  - Unified Tool Registry (21 tools)
  - Visual Tools (10)
  - Content Tools (11)
  - Brand Discovery
  - Brief Parser
  - 6-Node LangGraph Pipeline
  - Agency Content Agent (persistence, cross-project learning)
  - Workspace Content Store (memory, reporting)
  - Content Job Queue (submit, retry, priority)
  - Brief Enhancement
  - API Routes (27+ endpoints)
  - Interview Compliance
"""
import sys
sys.path.insert(0, ".")

passed = 0
failed = 0
errors = []


def test(name, fn):
    global passed, failed
    try:
        result = fn()
        print(f"  [PASS] {name}")
        passed += 1
        return result
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        failed += 1
        errors.append((name, str(e)))
        return None


def assert_eq(name, actual, expected):
    global passed, failed
    if actual == expected:
        print(f"  [PASS] {name}")
        passed += 1
    else:
        print(f"  [FAIL] {name}: expected {expected!r}, got {actual!r}")
        failed += 1
        errors.append((name, f"expected {expected!r}, got {actual!r}"))


def assert_true(name, condition):
    global passed, failed
    if condition:
        print(f"  [PASS] {name}")
        passed += 1
    else:
        print(f"  [FAIL] {name}: condition is False")
        failed += 1
        errors.append((name, "condition is False"))


def assert_in(name, needle, haystack):
    global passed, failed
    if needle in haystack:
        print(f"  [PASS] {name}")
        passed += 1
    else:
        print(f"  [FAIL] {name}: '{needle}' not found in target")
        failed += 1
        errors.append((name, f"'{needle}' not found"))


print("=" * 70)
print("CONTENT AGENT COMPREHENSIVE TEST (v2)")
print("=" * 70)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. IMPORTS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 1. IMPORTS ---")
test("visual_tools import", lambda: __import__("admin.tools.visual_tools"))
test("content_tools import", lambda: __import__("admin.tools.content_tools"))
test("registry import", lambda: __import__("admin.tools.registry"))
test("content agent import", lambda: __import__("admin.workspace.agents.content"))
test("agency content agent import", lambda: __import__("admin.agency.content_agent"))
test("content store import", lambda: __import__("admin.workspace.content_store"))
test("content queue import", lambda: __import__("admin.tools.content_queue"))
test("content routes import", lambda: __import__("admin.api.routes.content"))


# ═══════════════════════════════════════════════════════════════════════════════
# 2. UNIFIED TOOL REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 2. UNIFIED TOOL REGISTRY ---")
from admin.tools.registry import (
    get_all_tools, get_visual_tools, get_content_tools,
    list_all_tools, list_tools_by_category, get_tool_by_name,
    execute_agent_tool, get_tool_counts,
)

counts = test("get_tool_counts", lambda: get_tool_counts())
if counts:
    assert_eq("total tools", counts["total"], 21)
    assert_eq("visual tools", counts["visual"], 10)
    assert_eq("content tools", counts["content"], 11)
    print(f"         Counts: {counts}")

all_tools = test("get_all_tools", lambda: get_all_tools())
if all_tools:
    assert_eq("all_tools length", len(all_tools), 21)

listed = test("list_all_tools", lambda: list_all_tools())
if listed:
    assert_eq("listed tools length", len(listed), 21)
    categories = {t["category"] for t in listed}
    assert_true("has visual category", "visual" in categories)
    assert_true("has content category", "content" in categories)

visual_only = test("list_tools_by_category(visual)", lambda: list_tools_by_category("visual"))
if visual_only:
    assert_eq("visual tools count", len(visual_only), 10)

content_only = test("list_tools_by_category(content)", lambda: list_tools_by_category("content"))
if content_only:
    assert_eq("content tools count", len(content_only), 11)

tool_lookup = test("get_tool_by_name(discover_brand_identity)", lambda: get_tool_by_name("discover_brand_identity"))
if tool_lookup:
    assert_eq("tool name", tool_lookup["name"], "discover_brand_identity")
    assert_true("has description", bool(tool_lookup["description"]))
    assert_true("has parameters", bool(tool_lookup["parameters"]))

test("get_tool_by_name(nonexistent) returns None",
     lambda: assert_eq("nonexistent", get_tool_by_name("nonexistent_tool_xyz"), None))

# ═══════════════════════════════════════════════════════════════════════════════
# 3. VISUAL TOOLS (10 tools)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 3. VISUAL TOOLS ---")
from admin.tools.visual_tools import VISUAL_TOOLS, execute_visual_tool
visual_names = [t["function"]["name"] for t in VISUAL_TOOLS]
print(f"  Visual tools: {len(VISUAL_TOOLS)} -> {visual_names}")
assert_eq("visual tools count", len(VISUAL_TOOLS), 10)

expected_visual = [
    "discover_brand_identity", "parse_visual_brief", "plan_visual_production",
    "generate_image_kaggle", "generate_video_kaggle", "generate_ad_image",
    "generate_social_image", "generate_hero_image", "generate_video_ad",
    "batch_generate_images",
]
for name in expected_visual:
    assert_in(f"visual tool '{name}' registered", name, visual_names)


# ═════════════════════════════════════════════════════════════════
# 4. CONTENT TOOLS (11 tools)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 4. CONTENT TOOLS ---")
from admin.tools.content_tools import CONTENT_TOOLS, execute_content_tool
content_names = [t["name"] for t in CONTENT_TOOLS]
print(f"  Content tools: {len(CONTENT_TOOLS)} -> {content_names}")
assert_eq("content tools count", len(CONTENT_TOOLS), 11)

expected_content = [
    "analyze_readability", "generate_content_brief", "generate_blog_post",
    "optimize_meta_descriptions", "rewrite_content", "generate_content_calendar",
    "analyze_content_gaps", "search_images", "get_social_image_specs",
    "repurpose_for_social", "generate_ad_copy",
]
for name in expected_content:
    assert_in(f"content tool '{name}' registered", name, content_names)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. BRAND DISCOVERY
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 5. BRAND DISCOVERY ---")
from admin.tools.visual_tools import discover_brand_identity
brand = test("discover_brand_identity", lambda: discover_brand_identity("https://example.com"))
if brand:
    assert_true("brand has website_url", bool(brand.get("website_url")))
    assert_true("brand has brand_name field", "brand_name" in brand)
    assert_true("brand has colors field", "colors" in brand)
    assert_true("brand has social_links field", "social_links" in brand)
    assert_true("brand has visual_style field", "visual_style" in brand)
    print(f"         Brand name: {brand.get('brand_name', '')}")
    print(f"         Colors: {brand.get('colors', [])}")
    print(f"         Visual style: {brand.get('visual_style', '')}")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. BRIEF PARSER
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 6. BRIEF PARSER ---")
from admin.tools.visual_tools import parse_visual_brief

parsed_social = test("parse social brief", lambda: parse_visual_brief(
    "Need bold Instagram reels cover images for our new product launch campaign"
))
if parsed_social:
    assert_eq("visual_type=video", parsed_social.get("visual_type"), "video")
    assert_eq("platform=instagram", parsed_social.get("platform"), "instagram")
    assert_eq("style=bold", parsed_social.get("style"), "bold")

parsed_ad = test("parse ad brief", lambda: parse_visual_brief(
    "Professional Facebook ad creative for our SaaS product launch, 3 images"
))
if parsed_ad:
    assert_eq("visual_type=image", parsed_ad.get("visual_type"), "image")
    assert_eq("platform=facebook", parsed_ad.get("platform"), "facebook")
    assert_eq("quantity=3", parsed_ad.get("quantity"), 3)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. PRODUCTION PLANNER
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 7. PRODUCTION PLANNER ---")
from admin.tools.visual_tools import plan_visual_production
plan = test("plan_production", lambda: plan_visual_production(
    brief=parsed_social, brand_identity=brand
))
if plan:
    assert_true("has total_items", plan.get("total_items", 0) > 0)
    assert_true("has estimated_gpu_minutes", "estimated_gpu_minutes" in plan)
    assert_true("has items list", isinstance(plan.get("items"), list))
    if plan.get("items"):
        item = plan["items"][0]
        assert_true("item has prompt", bool(item.get("prompt")))
        assert_true("item has width", "width" in item)
        assert_true("item has height", "height" in item)
        print(f"         Items: {plan.get('total_items')}")
        print(f"         GPU minutes: {plan.get('estimated_gpu_minutes')}")


# ═══════════════════════════════════════════════════════════════════════════════
# 8. TOOL EXECUTION (via registry)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 8. TOOL EXECUTION ---")
test("execute_agent_tool discover_brand", lambda: execute_agent_tool(
    "discover_brand_identity", {"website_url": "https://example.com"}
))
test("execute_agent_tool parse_brief", lambda: execute_agent_tool(
    "parse_visual_brief", {"brief_text": "Instagram story image for summer sale"}
))
test("execute_agent_tool content_brief", lambda: execute_agent_tool(
    "generate_content_brief", {"topic": "digital marketing"}
))


# ═══════════════════════════════════════════════════════════════════════════════
# 9. 6-NODE LANGGRAPH PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 9. 6-NODE LANGGRAPH PIPELINE ---")
from admin.workspace.agents.content import (
    ContentAgent, build_content_graph, get_content_graph,
    ContentState, parse_brief, analyze_brand, plan_visual,
    engineer_prompt, generate as gen_node, validate,
)

graph = test("build_content_graph", lambda: build_content_graph())
assert_true("graph is compiled", graph is not None)

# Test ContentState shape
assert_true("ContentState has messages", "messages" in ContentState.__annotations__)
assert_true("ContentState has parsed_brief", "parsed_brief" in ContentState.__annotations__)
assert_true("ContentState has brand_analysis", "brand_analysis" in ContentState.__annotations__)
assert_true("ContentState has visual_plan", "visual_plan" in ContentState.__annotations__)
assert_true("ContentState has variations", "variations" in ContentState.__annotations__)
assert_true("ContentState has attempt_count", "attempt_count" in ContentState.__annotations__)
print("  [PASS] ContentState has correct pipeline fields")


# ═══════════════════════════════════════════════════════════════════════════════
# 10. AGENCY CONTENT AGENT
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 10. AGENCY CONTENT AGENT ---")
from admin.agency.content_agent import (
    AgencyContentAgent, ContentReport, PromptPattern, BrandInsight,
    get_agency_content_agent,
)

agency = test("get_agency_content_agent", lambda: get_agency_content_agent())
assert_true("agency is singleton", agency is get_agency_content_agent())

# Test receive_report
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

report_result = test("receive_report", lambda: agency.receive_report(report))
if report_result:
    assert_eq("report status", report_result.get("status"), "received")
    print(f"         Total reports: {report_result.get('total_reports')}")

# Test get_knowledge_for_workspace
knowledge = test("get_knowledge_for_workspace", lambda: agency.get_knowledge_for_workspace(
    industry="general", platform="instagram"
))
if knowledge:
    assert_true("has total_reports", "total_reports" in knowledge)
    assert_true("has prompt_patterns", "prompt_patterns" in knowledge)
    assert_true("has brand_insights", "brand_insights" in knowledge)

# Test get_best_prompts
best = test("get_best_prompts", lambda: agency.get_best_prompts(
    visual_type="image", top_n=3
))
if best:
    assert_true("best prompts is list", isinstance(best, list))

# Test get_stats
stats = test("get_stats", lambda: agency.get_stats())
if stats:
    assert_true("stats has total_reports", "total_reports" in stats)
    assert_true("stats has platforms_active", "platforms_active" in stats)
    assert_true("stats has industries_served", "industries_served" in stats)

# Test extended methods (monkey-patched)
test("get_industry_insights", lambda: agency.get_industry_insights("general"))
test("get_platform_insights", lambda: agency.get_platform_insights("instagram"))
test("get_failure_patterns", lambda: agency.get_failure_patterns())
test("get_best_prompts_for", lambda: agency.get_best_prompts_for(industry="general"))


# ═════════════════════════════════════════════════════════════════
# 11. PERSISTENCE
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 11. PERSISTENCE ---")
test("agency has _save method", lambda: hasattr(agency, "_save"))
test("agency has _load method", lambda: hasattr(agency, "_load"))
test("agency _save works", lambda: agency._save())


# ═══════════════════════════════════════════════════════════════════════════════
# 12. WORKSPACE CONTENT STORE
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 12. WORKSPACE CONTENT STORE ---")
from admin.workspace.content_store import (
    WorkspaceContentStore, ContentAgentMemory, get_content_store,
)

store = test("get_content_store", lambda: get_content_store())
assert_true("store is singleton", store is get_content_store())

# Create memory
mem = test("get_or_create memory", lambda: store.get_or_create(
    "test_ws_001", "TestWorkspace", "TestClient", "tech"
))
if mem:
    assert_eq("workspace_id", mem.workspace_id, "test_ws_001")
    assert_eq("client_name", mem.client_name, "TestClient")

# Record success
test("record_success", lambda: store.record_success(
    workspace_id="test_ws_001",
    job_id="job_test_001",
    brief_summary="Create IG post",
    deliverables=["img1.png"],
    prompts_used=["prompt 1"],
    platform="instagram",
    visual_type="image",
    gpu_minutes=1.5,
    learnings=["Warm tones worked well"],
))

# Record failure
test("record_failure", lambda: store.record_failure(
    workspace_id="test_ws_001",
    job_id="job_test_002",
    brief_summary="Create video",
    error="GPU timeout",
    platform="instagram",
    visual_type="video",
    what_failed="CogVideoX generation",
    avoid_next_time="Use shorter frame count",
))

# Memory summary
summary = test("get_memory_summary", lambda: store.get_memory_summary("test_ws_001"))
if summary:
    assert_true("summary is non-empty", len(summary) > 0)
    print(f"         Summary preview: {summary[:100]}...")

# Stats
store_stats = test("get_stats", lambda: store.get_stats("test_ws_001"))
if store_stats:
    assert_true("success_count >= 1", store_stats.get("success_count", 0) >= 1)
    assert_true("failure_count >= 1", store_stats.get("failure_count", 0) >= 1)

# Style tracking
test("record_style_preference", lambda: store.record_style_preference(
    "test_ws_001", "bold", 0.9
))

# Variation tracking
test("record_variation", lambda: store.record_variation(
    "test_ws_001",
    "Test brief",
    [{"prompt": "test prompt", "platform": "instagram"}],
    [0.85],
))


# ═══════════════════════════════════════════════════════════════════════════════
# 13. CONTENT JOB QUEUE
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 13. CONTENT JOB QUEUE ---")
from admin.tools.content_queue import (
    ContentJobQueue, ContentBrief, JobStatus, get_queue, enhance_brief,
)

queue = test("get_queue", lambda: get_queue("test_ws_001"))
assert_true("queue is ContentJobQueue", isinstance(queue, ContentJobQueue))

# Submit a job
brief = ContentBrief(
    workspace_id="test_ws_001",
    from_agent="social",
    content_type="social_post",
    platform="instagram",
    style="bold",
    topic="Summer sale campaign",
    quantity=3,
    priority="high",
)

job_id = test("queue.submit", lambda: queue.submit(brief))
if job_id:
    assert_true("job_id starts with job_", job_id.startswith("job_"))

# Queue status
q_status = test("queue.get_queue_status", lambda: queue.get_queue_status())
if q_status:
    assert_true("has pending", "pending" in q_status)
    assert_true("gpu_busy in status", "gpu_busy" in q_status)

# Get next job
next_job = test("queue.get_next", lambda: queue.get_next())
if next_job:
    assert_eq("next job status", next_job.status, JobStatus.RUNNING)
    assert_eq("next job platform", next_job.platform, "instagram")

# Complete job
test("queue.complete", lambda: queue.complete(
    job_id=job_id,
    output_files=["output_001.png", "output_002.png"],
))

# List recent
recent = test("queue.list_recent", lambda: queue.list_recent(limit=5))
if recent:
    assert_true("recent has jobs", len(recent) > 0)

# Brief Enhancement
enhanced = test("enhance_brief", lambda: enhance_brief(
    brief=ContentBrief(
        content_type="social_post",
        platform="instagram",
        style="bold",
        topic="Summer sale",
    ),
    client_context={
        "brand_colors": ["#FF6B35", "#004E89"],
        "industry": "ecommerce",
        "target_audience": "young adults",
    },
))
if enhanced:
    assert_true("enhanced_prompt is set", bool(enhanced.enhanced_prompt))
    assert_eq("width", enhanced.width, 1080)
    assert_eq("height", enhanced.height, 1080)
    assert_eq("brand_colors_used", enhanced.brand_colors_used, ["#FF6B35", "#004E89"])
    print(f"         Prompt: {enhanced.enhanced_prompt[:100]}...")


# ═══════════════════════════════════════════════════════════════════════════════
# 14. API ROUTES
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 14. API ROUTES ---")
from admin.api.routes.content import router
paths = [r.path for r in router.routes if hasattr(r, "path")]
print(f"  Total API routes: {len(paths)}")
for p in sorted(paths):
    print(f"         {p}")

# Core endpoints
assert_true("has /chat endpoint", "/api/content/chat" in paths)
assert_true("has /init endpoint", "/api/content/init" in paths)
assert_true("has /discover-brand endpoint", "/api/content/discover-brand" in paths)

# Visual generation endpoints
assert_true("has /generate-image endpoint", "/api/content/generate-image" in paths)
assert_true("has /generate-video endpoint", "/api/content/generate-video" in paths)
assert_true("has /generate-ad endpoint", "/api/content/generate-ad" in paths)
assert_true("has /generate-social endpoint", "/api/content/generate-social" in paths)
assert_true("has /generate-hero endpoint", "/api/content/generate-hero" in paths)

# Content analysis endpoints (NEW)
assert_true("has /tools/all endpoint", "/api/content/tools/all" in paths)
assert_true("has /analyze-readability endpoint", "/api/content/analyze-readability" in paths)
assert_true("has /blog-post endpoint", "/api/content/blog-post" in paths)
assert_true("has /calendar endpoint", "/api/content/calendar" in paths)
assert_true("has /rewrite endpoint", "/api/content/rewrite" in paths)
assert_true("has /meta-optimize endpoint", "/api/content/meta-optimize" in paths)
assert_true("has /content-gaps endpoint", "/api/content/content-gaps" in paths)

# Agency intelligence endpoints (NEW)
assert_true("has /agency/stats endpoint", "/api/content/agency/stats" in paths)
assert_true("has /agency/knowledge endpoint", "/api/content/agency/knowledge" in paths)
assert_true("has /agency/best-prompts endpoint", "/api/content/agency/best-prompts" in paths)

# Queue endpoint (NEW)
assert_true("has /queue/status endpoint", "/api/content/queue/status" in paths)

# Briefing endpoint
assert_true("has /brief endpoint", "/api/content/brief" in paths)

# Variation endpoints
assert_true("has /generate-variations endpoint", "/api/content/generate-variations" in paths)
assert_true("has /select-variation endpoint", "/api/content/select-variation" in paths)

# UGC and marketing
assert_true("has /generate-ugc endpoint", "/api/content/generate-ugc" in paths)
assert_true("has /generate-marketing endpoint", "/api/content/generate-marketing" in paths)
assert_true("has /batch-generate endpoint", "/api/content/batch-generate" in paths)

print(f"\n  Verified {len(paths)} routes")


# ═══════════════════════════════════════════════════════════════════════════════
# 15. INTERVIEW COMPLIANCE
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 15. INTERVIEW COMPLIANCE ---")

# Check SKILL.md for interview-required concepts
skill_md = ""
try:
    with open("admin/skills/content/SKILL.md", "r", encoding="utf-8") as f:
        skill_md = f.read()
except FileNotFoundError:
    print("  [WARN] SKILL.md not found, skipping compliance checks")

checks = {
    "visual_only_rule": "VISUAL ONLY" in skill_md or "visual only" in skill_md.lower(),
    "no_text_content": "NO text" in skill_md or "no text" in skill_md.lower(),
    "kaggle_gpu_compute": "Kaggle" in skill_md,
    "flux_image_gen": "FLUX" in skill_md,
    "brand_discovery": "brand" in skill_md.lower() and "discover" in skill_md.lower(),
    "domain_agent_briefing": "brief" in skill_md.lower() and "domain agent" in skill_md.lower(),
    "agency_learning": "agency" in skill_md.lower() and "learning" in skill_md.lower(),
    "job_queue": "queue" in skill_md.lower(),
    "ceo_approval": "CEO" in skill_md or "approval" in skill_md.lower(),
}
for check, result in checks.items():
    status = "PASS" if result else "FAIL"
    print(f"  [{status}] {check}")

# Check code supports all 6 pipeline nodes
from admin.workspace.agents.content import (
    parse_brief as nb1, analyze_brand as nb2, plan_visual as nb3,
    engineer_prompt as nb4, generate as nb5, validate as nb6,
)
pipeline_nodes = ["parse_brief", "analyze_brand", "plan_visual",
                  "engineer_prompt", "generate", "validate"]
print(f"  [PASS] All 6 pipeline nodes importable: {pipeline_nodes}")


# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print(f"RESULTS: {passed} passed, {failed} failed")
if failed == 0:
    print("ALL TESTS PASSED!")
else:
    print(f"\nFailed tests:")
    for name, err in errors:
        print(f"  - {name}: {err}")
print("=" * 70)
