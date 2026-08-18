"""Offline tests for the real-tool runtime layer.

These run WITHOUT any API keys (E2B/COMPOSIO unset) and verify the layer is
key-gated and never crashes. They also sanity-check behavior when keys are
faked (sandbox fallback, integration unavailable).
"""

import os
import sys

import pytest

# Ensure project root on path so `admin` resolves.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from admin.runtime import (
    AgentRuntime,
    AgentSandbox,
    SpendPolicy,
    WorkspaceIntegrations,
    get_agent_runtime,
)
from admin.runtime.spend_policy import RiskLevel


def test_sandbox_local_fallback_without_key():
    """No E2B key -> local backend, real exec works, no crash."""
    os.environ.pop("E2B_API_KEY", None)
    sb = AgentSandbox("sba", "ws_offline_test", force_local=True)
    assert sb.backend_kind == "local"
    res = sb.exec("echo hello-from-sandbox")
    assert res.exit_code == 0
    assert "hello-from-sandbox" in res.stdout
    assert res.backend == "local"


def test_sandbox_write_read_roundtrip():
    sb = AgentSandbox("sba", "ws_offline_test", force_local=True)
    sb.write_file("/tmp/lead_data.txt", "lead-1,hot\nlead-2,warm\n")
    content = sb.read_file("/tmp/lead_data.txt")
    assert "lead-1,hot" in content


def test_sandbox_python_exec():
    sb = AgentSandbox("sba", "ws_offline_test", force_local=True)
    res = sb.python("print(2 + 3 * 4)")
    assert res.exit_code == 0
    assert "14" in res.stdout


def test_integrations_unavailable_without_key():
    os.environ.pop("COMPOSIO_API_KEY", None)
    integ = WorkspaceIntegrations("ws_offline_test")
    assert integ.available is False
    # execute must return a clean dict, not raise
    out = integ.execute("GMAIL_SEND_EMAIL", {"to": "x@y.z", "subject": "hi", "body": "yo"})
    assert out["status"] == "unavailable"
    assert "error" in out
    assert integ.list_tool_slugs() == []


def test_spend_policy_defaults_allow_low_medium_block_high():
    policy = SpendPolicy()
    low = policy.evaluate("run_sandbox_code", RiskLevel.LOW)
    med = policy.evaluate("send_one_email", RiskLevel.MEDIUM)
    high = policy.evaluate("bulk_delete", RiskLevel.HIGH)
    assert low.allow is True
    assert med.allow is True
    assert high.allow is False


def test_spend_policy_cap_enforced():
    policy = SpendPolicy()
    policy.config.max_external_per_window = 2
    assert policy.evaluate("e1", RiskLevel.MEDIUM).allow is True
    assert policy.evaluate("e2", RiskLevel.MEDIUM).allow is True
    # Third exceeds cap
    third = policy.evaluate("e3", RiskLevel.MEDIUM)
    assert third.allow is False
    assert "cap" in third.reason.lower()


def test_spend_policy_explicit_deny():
    policy = SpendPolicy()
    policy.config.deny.add("forbidden_action")
    dec = policy.evaluate("forbidden_action", RiskLevel.LOW)
    assert dec.allow is False
    assert "denied" in dec.reason.lower()


def test_registry_caches_and_bundles_runtime():
    rt1 = get_agent_runtime("seo", "ws_cache_test")
    rt2 = get_agent_runtime("seo", "ws_cache_test")
    assert rt1 is rt2  # cached
    assert isinstance(rt1.sandbox, AgentSandbox)
    assert isinstance(rt1.integrations, WorkspaceIntegrations)
    assert isinstance(rt1.policy, SpendPolicy)
    status = rt1.status()
    assert status["agent_type"] == "seo"
    assert "sandbox" in status and "integrations" in status


def test_agent_runtime_status_shape():
    rt = AgentRuntime("content", "ws_status_test")
    s = rt.status()
    assert s["sandbox"]["backend"] in ("local", "e2b")
    assert "external_remaining" in s


def test_route_to_agent_imports_clean():
    """route_to_agent must import + call without error even offline.

    We only test that importing the workspace manager and constructing the
    runtime path works; full routing needs a DB-backed workspace, which the
    offline suite avoids. This guards against syntax/import regressions in
    the wiring we added.
    """
    from admin.workspace import manager as mgr  # noqa: F401
    assert hasattr(mgr, "route_to_agent")
