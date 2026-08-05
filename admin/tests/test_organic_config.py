# admin/tests/test_organic_config.py
import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")

import tempfile
from pathlib import Path
from unittest.mock import patch

from admin.tools.organic import config as cfg


def test_save_and_get_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "ORGANIC_CONFIG_DIR", tmp_path)
    cfg.save_channel_config("ws1", "reddit", {"subreddits": ["r/test"], "client_id": "abc"})
    data = cfg.get_channel_config("ws1", "reddit")
    assert data["subreddits"] == ["r/test"]
    assert data["client_id"] == "abc"


def test_get_missing_returns_empty(monkeypatch, tmp_path):
    monkeypatch.setattr(cfg, "ORGANIC_CONFIG_DIR", tmp_path)
    assert cfg.get_channel_config("ws1", "telegram") == {}


def test_list_configs(monkeypatch, tmp_path):
    monkeypatch.setattr(cfg, "ORGANIC_CONFIG_DIR", tmp_path)
    cfg.save_channel_config("ws1", "reddit", {"a": 1})
    cfg.save_channel_config("ws1", "telegram", {"b": 2})
    listed = cfg.list_channel_configs("ws1")
    assert "reddit" in listed
    assert "telegram" in listed
