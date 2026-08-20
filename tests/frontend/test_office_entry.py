import os
import subprocess

ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "agency-frontend")
)


def test_office_page_exists():
    p = os.path.join(ROOT, "src", "app", "admin", "office", "page.jsx")
    assert os.path.exists(p), "office page missing"


def test_office_supporting_files_exist():
    for rel in (
        "src/app/admin/office/OfficeFloor.jsx",
        "src/app/admin/office/CeoChat.jsx",
        "src/app/admin/office/SbaLivePanel.jsx",
        "src/hooks/useOfficeSocket.js",
    ):
        assert os.path.exists(os.path.join(ROOT, rel)), f"missing {rel}"


def test_pixi_dependency_listed():
    import json

    pkg = json.load(open(os.path.join(ROOT, "package.json"), encoding="utf-8"))
    assert "pixi.js" in pkg.get("dependencies", {}), "pixi.js not in package.json"
