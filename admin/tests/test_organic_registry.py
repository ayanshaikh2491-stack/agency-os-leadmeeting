from admin.tools.organic.registry import CHANNELS, get_channel, list_channels


def test_registry_has_all_phase1_channels():
    for ch in ["reddit", "linkedin", "twitter", "pinterest", "telegram", "gbp", "facebook"]:
        assert ch in CHANNELS, f"missing {ch}"


def test_channel_meta_fields():
    reddit = CHANNELS["reddit"]
    assert reddit["type"] == "api"
    assert "post" in reddit["capabilities"]
    assert "subreddit" in reddit["required_fields"]


def test_facebook_is_browser():
    assert CHANNELS["facebook"]["type"] == "browser"
    assert "groups" in CHANNELS["facebook"]["capabilities"]


def test_get_channel():
    assert get_channel("reddit")["id"] == "reddit"
    assert get_channel("nope") is None


def test_list_channels_returns_list():
    lst = list_channels()
    assert isinstance(lst, list)
    assert len(lst) >= 7
