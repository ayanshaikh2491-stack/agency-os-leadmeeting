import os
import subprocess

ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "agency-frontend")
)


def test_no_paperclip_css_file():
    # Paperclip design file must be removed.
    assert not os.path.exists(os.path.join(ROOT, "src", "app", "paperclip.css")), \
        "paperclip.css still exists — remove the Paperclip design system"


def test_no_paperclip_references():
    # No remaining github.com/paperclipai references anywhere in the frontend.
    out = subprocess.run(
        ["findstr", "/si", "paperclipai"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        shell=True,
    )
    assert out.stdout.strip() == "", (
        f"paperclipai references remain:\n{out.stdout}"
    )


def test_office_tokens_defined():
    # globals.css must define the Agency Office token set.
    globals_path = os.path.join(ROOT, "src", "app", "globals.css")
    with open(globals_path, encoding="utf-8") as f:
        css = f.read()
    for token in ("--office-bg", "--office-accent", "--office-gold"):
        assert token in css, f"{token} missing from globals.css"
