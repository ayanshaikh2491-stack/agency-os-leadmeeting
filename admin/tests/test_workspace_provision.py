"""Tests for workspace-scoped Supabase provisioning + schema-aware bridge.

No live database: REST calls are mocked, so these run anywhere.
"""
import json
import unittest
from unittest import mock

from admin.agency import website_supabase as wsb
from admin.agency.workspace_provision import schema_for, slugify


class SlugifyTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(slugify("My Workspace"), "my_workspace")

    def test_special_chars(self):
        self.assertEqual(slugify("Acme Co, Inc.!"), "acme_co_inc")

    def test_leading_digits_stripped(self):
        self.assertEqual(slugify("123 Agency"), "agency")

    def test_unicode_and_spaces(self):
        self.assertEqual(slugify("  Café & Bakery "), "caf_bakery")

    def test_empty_falls_back(self):
        self.assertEqual(slugify(""), "default")
        self.assertEqual(slugify("!!!"), "default")

    def test_schema_for(self):
        self.assertEqual(schema_for("Agency"), "ws_agency")
        self.assertEqual(schema_for("Default"), "ws_default")


class ClientQueryTests(unittest.TestCase):
    def test_client_q_quotes(self):
        self.assertEqual(wsb._client_q("Acme & Co"), "client_name=eq.Acme%20%26%20Co")


def _header(req, name: str):
    """Case-insensitive header lookup (urllib lowercases header names)."""
    low = name.lower()
    for k, v in req.headers.items():
        if k.lower() == low:
            return v
    return None


class ApiProfileTests(unittest.TestCase):
    def _mock_resp(self, raw: bytes):
        resp = mock.MagicMock()
        resp.read.return_value = raw
        resp.__enter__.return_value = resp
        return resp

    @mock.patch("urllib.request.urlopen")
    def test_post_sends_content_profile(self, m):
        m.return_value = self._mock_resp(b'[{"id": 1}]')
        out = wsb._api(
            "POST", "http://x:8050", "key", "/rest/v1/website_builds",
            {"client_name": "c"}, on_conflict="client_name",
            profile="ws_agency",
        )
        self.assertEqual(out, [{"id": 1}])
        req = m.call_args[0][0]
        self.assertEqual(_header(req, "Content-Profile"), "ws_agency")
        self.assertEqual(_header(req, "Accept-Profile"), "ws_agency")
        self.assertIn("on_conflict=client_name", req.full_url)

    @mock.patch("urllib.request.urlopen")
    def test_get_sends_profile_and_client_query(self, m):
        m.return_value = self._mock_resp(b"[]")
        wsb._api("GET", "http://x:8050", "key", "/rest/v1/website_builds?select=*&client_name=eq.c", profile="ws_default")
        req = m.call_args[0][0]
        self.assertEqual(_header(req, "Accept-Profile"), "ws_default")
        self.assertIn("client_name=eq.c", req.full_url)


class BridgeFunctionTests(unittest.TestCase):
    def _mock_resp(self, raw: bytes):
        resp = mock.MagicMock()
        resp.read.return_value = raw
        resp.__enter__.return_value = resp
        return resp

    def test_upsert_build_uses_workspace_schema(self):
        with mock.patch.object(wsb, "get_config", return_value=("http://x:8050", "key")), \
             mock.patch("urllib.request.urlopen") as m:
            m.return_value = self._mock_resp(b'[{"client_name": "Acme", "status": "building"}]')
            out = wsb.upsert_website_build("My Agency", "Acme", status="building")
            self.assertEqual(out["status"], "building")
            req = m.call_args[0][0]
            self.assertEqual(_header(req, "Content-Profile"), "ws_my_agency")
            body = json.loads(req.data)
            self.assertNotIn("workspace_name", body)
            self.assertEqual(body["client_name"], "Acme")

    def test_save_doc_on_conflict_client_doc_type(self):
        with mock.patch.object(wsb, "get_config", return_value=("http://x:8050", "key")), \
             mock.patch("urllib.request.urlopen") as m:
            m.return_value = self._mock_resp(b'[]')
            wsb.save_website_doc("Agency", "Acme", "business_brief", title="Brief", content="Hi")
            req = m.call_args[0][0]
            self.assertIn("on_conflict=client_name,doc_type", req.full_url)
            self.assertEqual(_header(req, "Content-Profile"), "ws_agency")

    def test_get_website_build_query(self):
        with mock.patch.object(wsb, "get_config", return_value=("http://x:8050", "key")), \
             mock.patch("urllib.request.urlopen") as m:
            m.return_value = self._mock_resp(b'[]')
            wsb.get_website_build("Agency", "Acme & Co")
            req = m.call_args[0][0]
            self.assertEqual(_header(req, "Accept-Profile"), "ws_agency")
            self.assertIn("client_name=eq.Acme%20%26%20Co", req.full_url)


class ProvisionWorkspaceTests(unittest.TestCase):
    @mock.patch("urllib.request.urlopen")
    @mock.patch("admin.agency.website_supabase.get_config", return_value=("http://x:8050", "key"))
    def test_provision_calls_rpc(self, cfg, m):
        resp = mock.MagicMock()
        resp.__enter__.return_value = resp
        m.return_value = resp
        from admin.agency.workspace_provision import provision_workspace
        ok = provision_workspace("Acme Co")
        self.assertTrue(ok)
        req = m.call_args[0][0]
        self.assertIn("/rest/v1/rpc/provision_workspace", req.full_url)
        self.assertEqual(json.loads(req.data), {"ws_name": "Acme Co"})
        self.assertEqual(req.get_header("Authorization"), "Bearer key")

    @mock.patch("admin.agency.website_supabase.get_config", return_value=None)
    def test_provision_disabled_without_key(self, cfg):
        from admin.agency.workspace_provision import provision_workspace
        self.assertFalse(provision_workspace("Acme Co"))


if __name__ == "__main__":
    unittest.main()
