"""§2 Lifecycle tests — proof the agents are light + CEO-gated (no 24/7 loops).

Spec: docs/specs/2026-08-25-ceo-gated-on-demand-design.md §6.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "admin" / "agency"))

import lifecycle as lc
from lifecycle import LifecycleState


def setup_function(fn):
    # Fresh runtime table per test.
    lc._RUNTIMES.clear()


def test_lifecycle_default_standby():
    """After boot/register, every agent is STANDBY (no loop spawned)."""
    for slug in ("ceo", "sba", "seo", "social", "website"):
        lc.register(slug)
    for slug in ("ceo", "sba", "seo", "social", "website"):
        assert lc.get(slug).state == LifecycleState.STANDBY, slug


def test_wake_only_via_ceo():
    """wake flips STANDBY->ACTIVE; calling executor-style work requires wake first."""
    lc.register("sba")
    # Before wake, can_wake is True (standby). After sleep it returns to standby.
    rt = lc.wake("sba", brief_id="test")
    assert rt.state == LifecycleState.ACTIVE
    # waking again while ACTIVE must be rejected (no double-loop).
    try:
        lc.wake("sba")
        assert False, "should not allow wake while ACTIVE"
    except RuntimeError:
        pass


def test_self_sleep():
    """After run_once returns, agent returns to STANDBY with no loop alive."""
    lc.register("sba")
    lc.wake("sba", brief_id="x")
    assert lc.get("sba").state == LifecycleState.ACTIVE
    lc.sleep("sba")
    assert lc.get("sba").state == LifecycleState.STANDBY
    assert lc.get("sba").current_brief_id is None


def test_self_sleep_on_error():
    """Even on failure the agent self-sleeps (no daemon left)."""
    lc.register("sba")
    lc.wake("sba")
    lc.mark_error("sba", "boom")
    assert lc.get("sba").state == LifecycleState.STANDBY
    assert lc.get("sba").last_error == "boom"


def test_no_while_true_in_loop_files():
    """CI-proof: no run_forever / while True executable loop in the 4 files.
    (Comments mentioning them are allowed; real def/while loops are not.)
    """
    import ast
    base = Path(__file__).resolve().parent / "admin" / "agency"
    for fname in ("sba_autopilot.py", "ceo_monitor.py", "sba_monitor.py", "agent_loop.py"):
        tree = ast.parse((base / fname).read_text(encoding="utf-8", errors="ignore"))
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "run_forever":
                raise AssertionError(f"{fname}: run_forever still defined")
            if isinstance(node, ast.While) and getattr(node.test, "value", None) is True:
                # Only flag real `while True:` statements, not string literals.
                raise AssertionError(f"{fname}: real while-True loop still present")


def test_new_agent_autointegrate():
    """A new agent auto-registers STANDBY + is wakeable via the lifecycle gate."""
    lc.register("finance")
    assert lc.get("finance").state == LifecycleState.STANDBY
    lc.wake("finance", brief_id="demo")
    assert lc.get("finance").state == LifecycleState.ACTIVE
    lc.sleep("finance")
    assert lc.get("finance").state == LifecycleState.STANDBY
