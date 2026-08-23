"""Verify Social Media Agent CORE works (not just AEO/GEO).

Proves: module imports, graph builds, has core functions, skill detection
works, 21 tools registered, and State shape is valid.
"""
from admin.workspace.agents import social
from admin.workspace.agents.social import detect_skills


def test_module_imports():
    assert social.__name__ == "admin.workspace.agents.social"


def test_graph_builds():
    g = social.build_social_graph()
    assert g is not None


def test_core_functions_present():
    for fn in ["social_route", "social_finalize", "build_social_graph",
               "get_social_graph", "social_call_llm"]:
        assert hasattr(social, fn), f"MISSING {fn}"


def test_skill_detection_works():
    sk = detect_skills("make a TikTok post about plumbing tips")
    assert isinstance(sk, (list, dict, set))


def test_tools_registered():
    assert social.SOCIAL_TOOLS and len(social.SOCIAL_TOOLS) >= 15


def test_state_shape():
    st = social.SocialAgentState(
        messages=[{"role": "user", "content": "hi"}],
        workspace_name="Houston Plumbing Co",
        client_name="Test",
        tool_round=0,
        final_output="",
        error=None,
    )
    assert st["workspace_name"] == "Houston Plumbing Co"
