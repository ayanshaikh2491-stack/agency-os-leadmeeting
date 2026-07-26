"""Test Kaggle GPU tools + updated content agent."""
import sys
sys.path.insert(0, ".")

print("=" * 50)
print("KAGGLE GPU + CONTENT AGENT TEST")
print("=" * 50)

# 1. Kaggle GPU tools
print("\n--- KAGGLE GPU TOOLS ---")
from admin.tools.kaggle_gpu import KAGGLE_TOOLS
print(f"  [PASS] {len(KAGGLE_TOOLS)} Kaggle tools")
for t in KAGGLE_TOOLS:
    print(f"         - {t['name']}: {t['description']}")

# 2. Credentials check
print("\n--- CREDENTIALS ---")
from admin.tools.kaggle_gpu import _check_kaggle, _get_kaggle_creds
cli_ok = _check_kaggle()
creds = _get_kaggle_creds()
print(f"  CLI installed: {cli_ok}")
print(f"  Username: {creds['username'] or '(not set)'}")
print(f"  Key: {'***' if creds['key'] else '(not set)'}")

# 3. Convenience functions
print("\n--- CONVENIENCE FUNCTIONS ---")
from admin.tools.kaggle_gpu import (
    generate_image,
    generate_video,
    generate_ad_image,
    generate_social_image,
    generate_hero_image,
    generate_image_kaggle,
    generate_video_kaggle,
    generate_video_ad,
    batch_generate_images,
    check_status,
)
print("  [PASS] All functions importable")

# 4. Platform sizes
print("\n--- PLATFORM SIZES ---")
from admin.tools.kaggle_gpu import get_platform_size
for p in ["instagram", "facebook", "youtube", "twitter", "linkedin", "blog_hero"]:
    w, h = get_platform_size(p)
    print(f"  {p}: {w}x{h}")

# 5. Content agent pipeline
print("\n--- CONTENT AGENT PIPELINE ---")
from admin.workspace.agents.content import run_content_agent
print("  [PASS] Content agent importable")

print("\n" + "=" * 50)
print("ALL IMPORTS VERIFIED")
print("=" * 50)
print("\nPipeline:")
print("  /api/content/chat -> run_content_agent() -> LangGraph 6-node pipeline")
print("  -> generate node -> kaggle_gpu.generate_image() -> builds notebook")
print("  -> submits to Kaggle GPU -> polls -> downloads -> returns result")
print()
print("  /api/kaggle/image -> kaggle_gpu.generate_image_kaggle()")
print("  -> same flow as above")
