"""Tests for per-agent Supabase persistence (memory, messages, data,
LangGraph checkpoints). All REST calls mocked — no live DB."""
import json
import unittest
from unittest import mock

from admin.agency import agent_persistence as ap
from admin.agency.workspace_provision import schema_for


def _mock_resp(raw: bytes):
    resp = mock.MagicMock()
    resp.read.return_value = raw
    resp.__enter__.return_value = resp
    return resp


def _header(req, name: str):
    low = name.lower()
    for k, v in req.headers.items():
        if k.lower() == low:
            return v
    return None


class MemoryTests(unittest.TestCase):
    def test_save_memory_uses_workspace_schema_and_agent(self):
        with mock.patch.object(ap, "get_config", return_value=("http://x:8050", "key")), \
             mock.patch("urllib.request.urlopen") as m:
            m.return_value = _mock_resp(b'[{"agent_name": "seo", "memory_key": "learned", "value": {"a": 1}}]')
            out = ap.save_memory("Agency", "seo", "learned", {"a": 1})
            self.assertEqual(out["value"], {"a": 1})
            req = m.call_args[0][0]
            self.assertEqual(_header(req, "Content-Profile"), schema_for("Agency"))
            body = json.loads(req.data)
            self.assertEqual(body["agent_name"], "seo")
            self.assertEqual(body["memory_key"], "learned")
            self.assertIn("on_conflict=agent_name,memory_key", req.full_url)

    def test_get_memory_returns_value(self):
        with mock.patch.object(ap, "get_config", return_value=("http://x:8050", "key")), \
             mock.patch("urllib.request.urlopen") as m:
            m.return_value = _mock_resp(b'[{"value": {"x": 2}}]')
            val = ap.get_memory("Agency", "sba", "notes")
            self.assertEqual(val, {"x": 2})
            req = m.call_args[0][0]
            self.assertEqual(_header(req, "Accept-Profile"), schema_for("Agency"))
            self.assertIn("agent_name=eq.sba", req.full_url)
            self.assertIn("memory_key=eq.notes", req.full_url)

    def test_list_and_delete(self):
        with mock.patch.object(ap, "get_config", return_value=("http://x:8050", "key")), \
             mock.patch("urllib.request.urlopen") as m:
            m.return_value = _mock_resp(b'[]')
            self.assertEqual(ap.list_memory("Agency", "ads"), [])
            self.assertTrue(ap.delete_memory("Agency", "ads", "k"))
            reqs = [c[0][0] for c in m.call_args_list]
            self.assertEqual(_header(reqs[0], "Accept-Profile"), schema_for("Agency"))
            self.assertEqual(_header(reqs[1], "Accept-Profile"), schema_for("Agency"))


class MessageTests(unittest.TestCase):
    def test_append_and_get(self):
        with mock.patch.object(ap, "get_config", return_value=("http://x:8050", "key")), \
             mock.patch("urllib.request.urlopen") as m:
            m.return_value = _mock_resp(b'[{"id": 1}]')
            ap.append_message("Agency", "social", "user", "hello", {"x": 1})
            ap.get_messages("Agency", "social", limit=5)
            reqs = [c[0][0] for c in m.call_args_list]
            self.assertEqual(_header(reqs[0], "Content-Profile"), schema_for("Agency"))
            body = json.loads(reqs[0].data)
            self.assertEqual(body["role"], "user")
            self.assertEqual(body["content"], "hello")
            self.assertIn("order=created_at.desc", reqs[1].full_url)
            self.assertIn("limit=5", reqs[1].full_url)

    def test_clear_messages(self):
        with mock.patch.object(ap, "get_config", return_value=("http://x:8050", "key")), \
             mock.patch("urllib.request.urlopen") as m:
            m.return_value = _mock_resp(b"")
            self.assertTrue(ap.clear_messages("Agency", "content"))
            req = m.call_args[0][0]
            self.assertEqual(req.get_method(), "DELETE")


class DataTests(unittest.TestCase):
    def test_save_get_data(self):
        with mock.patch.object(ap, "get_config", return_value=("http://x:8050", "key")), \
             mock.patch("urllib.request.urlopen") as m:
            m.return_value = _mock_resp(b'[{"payload": {"brand": "acme"}}]')
            ap.save_data("Agency", "content", "brand", {"brand": "acme"})
            val = ap.get_data("Agency", "content", "brand")
            self.assertEqual(val, {"brand": "acme"})
            reqs = [c[0][0] for c in m.call_args_list]
            self.assertIn("on_conflict=agent_name,data_key", reqs[0].full_url)


class SupabaseSaverTests(unittest.TestCase):
    def setUp(self):
        self.saver = ap.SupabaseSaver("Agency", "seo")
        self.cfg = ("http://x:8050", "key")

    def test_storage_put_and_get(self):
        with mock.patch.object(ap, "get_config", return_value=self.cfg), \
             mock.patch("urllib.request.urlopen") as m:
            m.side_effect = [_mock_resp(b'[{"id": 1}]'), _mock_resp(b'[{"checkpoint": {"v": 1}, "metadata": {}, "parent_checkpoint_id": "", "checkpoint_id": "c1"}]')]
            self.assertTrue(self.saver._storage_put("t1", "c1", {"v": 1}, {}))
            row = self.saver._storage_get("t1", "c1")
            self.assertEqual(row["checkpoint"], {"v": 1})
            reqs = [c[0][0] for c in m.call_args_list]
            self.assertEqual(_header(reqs[0], "Content-Profile"), schema_for("Agency"))
            self.assertIn("thread_id=eq.t1", reqs[1].full_url)
            self.assertIn("checkpoint_id=eq.c1", reqs[1].full_url)

    def test_storage_writes_roundtrip(self):
        with mock.patch.object(ap, "get_config", return_value=self.cfg), \
             mock.patch("urllib.request.urlopen") as m:
            m.side_effect = [_mock_resp(b'[{"id": 1}]'), _mock_resp(b'[{"writes": [{"k": "v"}]}]')]
            self.assertTrue(self.saver._storage_put_writes("t1", "c1", "task1", [{"k": "v"}]))
            out = self.saver._storage_get_writes("t1", "c1")
            self.assertEqual(out, [{"k": "v"}])
            req = m.call_args_list[0][0][0]
            self.assertIn("on_conflict=agent_name,thread_id,checkpoint_id,task_id", req.full_url)

    def test_storage_list(self):
        with mock.patch.object(ap, "get_config", return_value=self.cfg), \
             mock.patch("urllib.request.urlopen") as m:
            m.return_value = _mock_resp(b'[{"checkpoint_id": "c1", "checkpoint": {}, "metadata": {}, "parent_checkpoint_id": ""}]')
            rows = self.saver._storage_list("t1", 5)
            self.assertEqual(len(rows), 1)
            req = m.call_args[0][0]
            self.assertIn("order=created_at.desc", req.full_url)
            self.assertIn("limit=5", req.full_url)

    def test_available_flag(self):
        with mock.patch.object(ap, "get_config", return_value=("http://x:8050", "key")):
            self.assertTrue(self.saver.available)
        with mock.patch.object(ap, "get_config", return_value=None):
            self.assertFalse(self.saver.available)


class GetCheckpointerTests(unittest.TestCase):
    def test_returns_supabase_when_configured(self):
        with mock.patch.object(ap, "get_config", return_value=("http://x:8050", "key")):
            cp = ap.get_checkpointer("Agency", "seo")
            self.assertIsInstance(cp, ap.SupabaseSaver)

    def test_falls_back_to_memory_saver(self):
        with mock.patch.object(ap, "get_config", return_value=None), \
             mock.patch("langgraph.checkpoint.memory.MemorySaver") as MS:
            ap.get_checkpointer("Agency", "seo")
            MS.assert_called_once()


if __name__ == "__main__":
    unittest.main()
