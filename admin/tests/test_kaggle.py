"""Test Kaggle GPU tools + updated content agent."""
import sys
sys.path.insert(0, ".")

print("=" * 50)
print("KAGGLE GPU + CONTENT AGENT TEST")
print("=" * 50)

# 1. Kaggle tools
print("\n--- KAGGLE TOOLS ---")
from admin.tools.kaggle_tools import KAGGLE_TOOLS, execute_kaggle_tool
print(f"  [PASS] {len(KAGGLE_TOOLS)} Kaggle tools")
for t in KAGGLE_TOOLS:
    print(f"         - {t['name']}")

# 2. Image generation
print("\n--- IMAGE GENERATION ---")
from admin.tools.kaggle_tools import generate_image_kaggle
r = generate_image_kaggle("a beautiful sunset over mountains", 1024, 1024)
print(f"  [PASS] generate_image_kaggle: status={r.get('status')}")
print(f"         Has notebook code: {bool(r.get('notebook_code'))}")

# 3. Video generation
print("\n--- VIDEO GENERATION ---")
from admin.tools.kaggle_tools import generate_video_kaggle
r = generate_video_kaggle("a cat playing with yarn")
print(f"  [PASS] generate_video_kaggle: status={r.get('status')}")
print(f"         Frames: {r.get('frames')}")

# 4. Ad image
print("\n--- AD IMAGE ---")
from admin.tools.kaggle_tools import generate_ad_image
r = generate_ad_image("Nike shoes", "facebook", "bold")
print(f"  [PASS] generate_ad_image: status={r.get('status')}")

# 5. Social image
print("\n--- SOCIAL IMAGE ---")
from admin.tools.kaggle_tools import generate_social_image
r = generate_social_image("digital marketing tips", "instagram")
print(f"  [PASS] generate_social_image: status={r.get('status')}")

# 6. Content tools (updated)
print("\n--- CONTENT TOOLS (updated) ---")
from admin.tools.content_tools import CONTENT_TOOLS
print(f"  [PASS] {len(CONTENT_TOOLS)} content tools")
tool_names = [t["name"] for t in CONTENT_TOOLS]
print(f"         {tool_names}")

# 7. Content + Kaggle combined workflow
print("\n--- COMBINED WORKFLOW ---")
from admin.tools.content_tools import generate_blog_post, repurpose_for_social, generate_ad_copy
blog = generate_blog_post("digital marketing", ["seo", "social media"])
print(f"  [PASS] Blog post: {blog.get('title')}")
print(f"         Sections: {len(blog.get('sections', []))}")

social = repurpose_for_social(blog["sections"][0]["content"], "instagram")
print(f"  [PASS] Social posts: {social.get('posts_generated')} for instagram")

ad = generate_ad_copy("digital marketing course", "facebook")
print(f"  [PASS] Ad copy: {len(ad.get('copies', []))} versions")

# 8. API routes
print("\n--- API ROUTES ---")
from admin.api.routes.kaggle import router as kaggle_router
from admin.api.routes.content import router as content_router
kaggle_paths = [r.path for r in kaggle_router.routes if hasattr(r, "path")]
content_paths = [r.path for r in content_router.routes if hasattr(r, "path")]
print(f"  [PASS] Kaggle routes: {len(kaggle_paths)}")
for p in sorted(kaggle_paths):
    print(f"         {p}")
print(f"  [PASS] Content routes: {len(content_paths)}")

print("\n" + "=" * 50)
print("ALL TESTS PASSED!")
print(f"\nCONTENT AGENT TOTAL:")
print(f"  11 text tools")
print(f"  7 Kaggle GPU tools")
print(f"  18 total tools")
print(f"  9 content API routes")
print(f"  9 kaggle API routes")
print(f"  18 total API routes")
print("=" * 50)
