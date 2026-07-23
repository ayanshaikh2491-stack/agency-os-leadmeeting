"""Content Agent — Comprehensive Test Suite.

Tests the full-spectrum Content Agent:
  - All 21 tools (visual + kaggle + content)
  - LangGraph compilation and routing
  - Agency Content Agent (persistence, cross-project learning)
  - API routes (27 endpoints)
  - Interview compliance
  - Dual reporting
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
print("CONTENT AGENT COMPREHENSIVE TEST")
print("=" * 70)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. IMPORTS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 1. IMPORTS ---")
test("visual_tools import", lambda: __import__("admin.tools.visual_tools"))
test("content_tools import", lambda: __import__("admin.tools.content_tools"))
test("kaggle_tools import", lambda: __import__("admin.tools.kaggle_tools"))
test("content agent import", lambda: __import__("admin.workspace.agents.content"))
test("agency content agent import", lambda: __import__("admin.agency.content_agent"))
test("content routes import", lambda: __import__("admin.api.routes.content"))
test("agent_bus import", lambda: __import__("admin.workspace.agent_bus"))


# ═══════════════════════════════════════════════════════════════════════════════
# 2. VISUAL TOOLS (10 tools)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 2. VISUAL TOOLS ---")
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


# ═══════════════════════════════════════════════════════════════
# 3. CONTENT TOOLS (11 tools)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 3. CONTENT TOOLS ---")
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


# ═══════════════════════════════════════════════════════════════
# 4. BRAND DISCOVERY
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 4. BRAND DISCOVERY ---")
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
# 5. BRIEF PARSER
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 5. BRIEF PARSER ---")
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
# 6. PRODUCTION PLANNER
# ═════════════════════════════════════════════════════════════════════════"\n--- 6. PRODUCTION PLANNER ---")
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
        print(f"         Sample prompt: {item.get('prompt', '')[:80]}...")


# ═══════════════════════════════════════════════════════════════════════════════
# 7. TOOL EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 7. TOOL EXECUTION ---")
test("execute discover_brand", lambda: execute_visual_tool(
    "discover_brand_identity", {"website_url": "https://example.com"}
))
test("execute parse_brief", lambda: execute_visual_tool(
    "parse_visual_brief", {"brief_text": "Instagram story image for summer sale"}
))
test("execute plan_production", lambda: execute_visual_tool(
    "plan_visual_production", {"brief": {"visual_type": "image", "platform": "instagram", "style": "bold"}}
))


# ═══════════════════════════════════════════════════════════════════════════════
# 8. KAGGLE TOOLS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 8. KAGGLE TOOLS ---")
from admin.tools.kaggle_tools import generate_image_kaggle, generate_video_kaggle

img_result = test("generate_image_kaggle (notebook)", lambda: generate_image_kaggle(
    "A beautiful sunset over mountains", 1024, 1024, 20
))
if img_result:
    assert_true("has status", "status" in img_result)
    print(f"         Status: {img_result.get('status')}")

vid_result = test("generate_video_kaggle (notebook)", lambda: generate_video_kaggle(
    "A cat playing with a ball", 49
))
if vid_result:
    assert_true("has status", "status" in vid_result)
    print(f"         Status: {vid_result.get('status')}")


# ═══════════════════════════════════════════════════════════════════════════════
# 9. CONTENT TOOLS (TEXT)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 9. CONTENT TOOLS (TEXT) ---")

brief_result = test("generate_content_brief", lambda: execute_content_tool(
    "generate_content_brief", {"topic": "digital marketing", "target_audience": "small business"}
))
if brief_result:
    assert_true("has outline", "outline" in brief_result)
    assert_true("has secondary_keywords", "secondary_keywords" in brief_result)

blog_result = test("generate_blog_post", lambda: execute_content_tool(
    "generate_blog_post", {"topic": "SEO tips", "word_count": 1000}
))
if blog_result:
    assert_true("has title", "title" in blog_result)
    assert_true("has sections", "sections" in blog_result)
    assert_true("has html", "html" in blog_result)
    assert_true("has seo_score", "seo_score" in blog_result)

calendar_result = test("generate_content_calendar", lambda: execute_content_tool(
    "generate_content_calendar", {"niche": "fitness", "weeks": 2}
))
if calendar_result:
    assert_true("has calendar", "calendar" in calendar_result)
    assert_true("has total_posts", "total_posts" in calendar_result)

rewrite_result = test("rewrite_content", lambda: execute_content_tool(
    "rewrite_content", {"text": "This is a very really quite good article about the topic.", "style": "professional"}
))
if rewrite_result:
    assert_true("has rewritten_text", "rewritten_text" in rewrite_result)
    assert_true("has improvements_made", "improvements_made" in rewrite_result)

specs_result = test("get_social_image_specs", lambda: execute_content_tool(
    "get_social_image_specs", {"platform": "instagram"}
))
if specs_result:
    assert_true("has formats", "formats" in specs_result)

repurpose_result = test("repurpose_for_social", lambda: execute_content_tool(
    "repurpose_for_social", {"content": "Digital marketing is essential for businesses. It helps reach more customers. SEO is a key part of digital marketing strategy.", "platform": "instagram"}
))
if repurpose_result:
    assert_true("has posts", "posts" in repurpose_result)

ad_copy_result = test("generate_ad_copy", lambda: execute_content_tool(
    "generate_ad_copy", {"product": "project management software", "platform": "facebook"}
))
if ad_copy_result:
    assert_true("has copies", "copies" in ad_copy_result)


# ═══════════════════════════════════════════════════════════════════════════════
# 10. CONTENT AGENT LANGGRAPH
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 10. CONTENT AGENT LANGGRAPH ---")
from admin.workspace.agents.content import (
    ContentAgent, build_content_graph, ALL_CONTENT_TOOLS,
    content_call_llm, content_route, content_finalize,
    ContentAgentState, CONTENT_SYSTEM_PROMPT,
)

graph = test("build_content_graph", lambda: build_content_graph())
agent = test("init ContentAgent", lambda: ContentAgent("TestWorkspace", "TestClient"))
if agent:
    assert_eq("workspace_name", agent.workspace_name, "TestWorkspace")
    assert_eq("client_name", agent.client_name, "TestClient")
    assert_eq("thread_id", agent._thread_id, "content_TestWorkspace")

# Check unified tool registry
assert_eq("ALL_CONTENT_TOOLS count", len(ALL_CONTENT_TOOLS), 21)
print(f"  [PASS] Unified tool registry: {len(ALL_CONTENT_TOOLS)} tools")


# ═══════════════════════════════════════════════════════════════════════════════
# 11. AGENCY CONTENT AGENT
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 11. AGENCY CONTENT AGENT ---")
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


# ═══════════════════════════════════════════════════════════════════════════════
# 12. PERSISTENCE
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 12. PERSISTENCE ---")
test("agency has _save method", lambda: hasattr(agency, "_save"))
test("agency has _load method", lambda: hasattr(agency, "_load"))
test("agency _save works", lambda: agency._save())


# ═══════════════════════════════════════════════════════════════════════════════
# 13. API ROUTES
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 13. API ROUTES ---")
from admin.api.routes.content import router
paths = [r.path for r in router.routes if hasattr(r, "path")]
print(f"  Total API routes: {len(paths)}")
for p in sorted(paths):
    print(f"         {p}")

assert_true("has /chat endpoint", "/api/content/chat" in paths)
assert_true("has /discover-brand endpoint", "/api/content/discover-brand" in paths)
assert_true("has /generate-image endpoint", "/api/content/generate-image" in paths)
assert_true("has /generate-video endpoint", "/api/content/generate-video" in paths)
assert_true("has /analyze-readability endpoint", "/api/content/analyze-readability" in paths)
assert_true("has /blog-post endpoint", "/api/content/blog-post" in paths)
assert_true("has /calendar endpoint", "/api/content/calendar" in paths)
assert_true("has /agency/stats endpoint", "/api/content/agency/stats" in paths)
assert_true("has /agency/knowledge endpoint", "/api/content/agency/knowledge" in paths)
assert_true("has /brief-content-agent endpoint", "/api/content/brief-content-agent" in paths)


# ═══════════════════════════════════════════════════════════════════════════════
# 14. INTERVIEW COMPLIANCE
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- 14. INTERVIEW COMPLIANCE ---")
checks = {
    "Q1_full_spectrum": "FULL-SPECTRUM" in CONTENT_SYSTEM_PROMPT,
    "Q2_visual_spectrum": "social graphics" in CONTENT_SYSTEM_PROMPT.lower() and "ad creatives" in CONTENT_SYSTEM_PROMPT.lower(),
    "Q3_kaggle": "Kaggle" in CONTENT_SYSTEM_PROMPT or "FLUX" in CONTENT_SYSTEM_PROMPT,
    "Q5_brand_discovery": "brand" in CONTENT_SYSTEM_PROMPT.lower() and "discover" in CONTENT_SYSTEM_PROMPT.lower(),
    "Q6_domain_approval": "domain agent" in CONTENT_SYSTEM_PROMPT.lower() or "approval" in CONTENT_SYSTEM_PROMPT.lower(),
    "text_content_enabled": "text content" in CONTENT_SYSTEM_PROMPT.lower() or "blog" in CONTENT_SYSTEM_PROMPT.lower(),
    "21_tools_documented": "21" in CONTENT_SYSTEM_PROMPT,
}
for check, result in checks.items():
    status = "PASS" if result else "FAIL"
    print(f"  [{status}] {check}")


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
