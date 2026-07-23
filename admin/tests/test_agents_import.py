"""Test all workspace agent imports."""
import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

agents = [
    ("SEO", "admin.workspace.agents.seo", "SEOAgent"),
    ("Ads", "admin.workspace.agents.ads", "AdsAgent"),
    ("Website", "admin.workspace.agents.website", "WebsiteAgent"),
    ("Social", "admin.workspace.agents.social", "SocialAgent"),
    ("Content", "admin.workspace.agents.content", "ContentAgent"),
]

errors = []
for name, module_path, class_name in agents:
    try:
        import importlib
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        instance = cls(workspace_name="Test Workspace", client_name="Test Client")
        print(f"  OK - {name} Agent ({class_name}) created")
    except Exception as e:
        errors.append(f"{name}: {e}")
        print(f"  FAIL - {name}: {e}")

print()
if errors:
    print(f"FAILED: {len(errors)} errors")
    for e in errors:
        print(f"  - {e}")
else:
    print("ALL 5 WORKSPACE AGENTS IMPORTED OK!")
    print("\nAgent Summary:")
    print("  SEO Agent     - Full-stack SEO, monitoring, auto-learning")
    print("  Ads Agent     - Meta + Google Ads, auto-optimization")
    print("  Website Agent - Design, dev, hosting, 24/7 monitoring")
    print("  Social Agent  - Strategy only (Instagram, LinkedIn, X)")
    print("  Content Agent - Visual execution only (images, videos)")
