"""Thin external PocketBase client for key Agency OS state.

Owner rule: PocketBase is THE database for key agency state (workspaces, custom
agents, agent outputs, CEO lifecycle/error state) so it survives an App Runner
container restart (the local SQLite/file state does not).

This module is ADDITIVE and config-driven: when POCKETBASE_URL is empty, nothing
is touched and the app keeps its current local behaviour. When set, callers may
mirror writes to PocketBase. All PB calls are best-effort: failures are logged
and never raised, so local runs are never broken.

Uses the `pocketbase` PyPI SDK when importable; otherwise falls back to a thin
`requests` wrapper around the PocketBase REST API.
"""
from __future__ import annotations

import json
import logging
import threading
from typing import Any, Optional

import requests

try:  # pragma: no cover - optional dependency
    from pocketbase import PocketBase as _PBSdk
    _HAS_PB_SDK = True
except Exception:  # noqa: BLE001
    _PBSdk = None
    _HAS_PB_SDK = False

logger = logging.getLogger(__name__)

# Collection names used by the Agency OS mirror.
COL_WORKSPACES = "workspaces"
COL_CUSTOM_AGENTS = "custom_agents"
COL_AGENT_OUTPUTS = "agent_outputs"
COL_CEO_LIFECYCLE = "ceo_lifecycle"


def _json_default(o: Any) -> Any:
    if hasattr(o, "isoformat"):
        return o.isoformat()
    return str(o)


class PocketBaseClient:
    """Admin-auth PocketBase client with get_collection/upsert/list helpers."""

    def __init__(self, url: str, email: str = "", password: str = "",
                 timeout: int = 10) -> None:
        self.url = (url or "").rstrip("/")
        self.email = email or ""
        self.password = password or ""
        self.timeout = timeout
        self._token: Optional[str] = None
        self._authed: bool = False
        self._lock = threading.Lock()
        self._sdk = None
        if _HAS_PB_SDK and self.url:
            try:
                self._sdk = _PBSdk(self.url)
            except Exception:  # noqa: BLE001
                self._sdk = None

    # ── config ──────────────────────────────────────────────────────────
    def is_configured(self) -> bool:
        return bool(self.url)

    # ── auth ────────────────────────────────────────────────────────────
    def auth(self) -> bool:
        """Authenticate as admin (or mark public if no creds). Idempotent."""
        if not self.url:
            return False
        if self._authed:
            return True
        # Prefer SDK auth when available.
        if self._sdk is not None and self.email and self.password:
            try:
                self._sdk.admins.auth_with_password(self.email, self.password)
                self._authed = True
                return True
            except Exception as exc:  # noqa: BLE001
                logger.warning("PocketBase SDK auth failed, trying REST: %s", exc)
                self._sdk = None
        if self.email and self.password:
            try:
                # PocketBase >= 0.23 moved admin auth under /api/collections/
                # _superusers; older servers still expose /api/admins. Try both.
                last_status = 0
                for path in (
                    "/api/collections/_superusers/auth-with-password",
                    "/api/admins/auth-with-password",
                ):
                    r = requests.post(
                        f"{self.url}{path}",
                        json={"identity": self.email, "password": self.password},
                        timeout=self.timeout,
                    )
                    if r.status_code == 200:
                        self._token = r.json().get("token")
                        self._authed = True
                        return True
                    last_status = r.status_code
                logger.warning(
                    "PocketBase admin auth failed (%s)", last_status)
                return False
            except Exception as exc:  # noqa: BLE001
                logger.warning("PocketBase admin auth error: %s", exc)
                return False
        # No creds: assume a publicly-writable collection / gateway passthrough.
        self._authed = True
        return True

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self._token:
            h["Authorization"] = self._token
        return h

    # ── source-of-truth helpers (REST-only, predictable shapes) ───────────
    def _rest_list(self, collection: str, filters: str = "",
                   per_page: int = 200) -> list[dict]:
        """Raw REST list — always returns plain dicts (SDK shapes vary)."""
        if not self.auth():
            return []
        params: dict[str, Any] = {"perPage": per_page}
        if filters:
            params["filter"] = filters
        try:
            r = requests.get(
                f"{self.url}/api/collections/{collection}/records",
                headers=self._headers(), params=params, timeout=self.timeout)
            if r.status_code == 200:
                return list(r.json().get("items", []))
        except Exception as exc:  # noqa: BLE001
            logger.debug("PocketBase rest_list failed (%s): %s", collection, exc)
        return []

    def upsert_by_key(self, collection: str, key_field: str,
                      data: dict) -> Optional[dict]:
        """Create-or-update a record matched on `key_field`.

        Our local ids (e.g. 'ws_default') do NOT fit PocketBase's 15-char
        record-id pattern, so we store them in a dedicated `key_field`
        column and match on that instead of the PB record id.
        """
        kv = str(data.get(key_field, "") or "")
        if not kv or not self.auth():
            return None
        payload = {k: v for k, v in data.items()
                   if k not in ("id", key_field)}
        payload[key_field] = kv
        existing = self._rest_list(
            collection, filters=f'{key_field}="{kv}"', per_page=1)
        try:
            if existing:
                rid = existing[0].get("id")
                r = requests.patch(
                    f"{self.url}/api/collections/{collection}/records/{rid}",
                    json=payload, headers=self._headers(), timeout=self.timeout)
            else:
                r = requests.post(
                    f"{self.url}/api/collections/{collection}/records",
                    json=payload, headers=self._headers(), timeout=self.timeout)
            if r.status_code in (200, 201):
                return r.json()
            logger.warning("PocketBase upsert_by_key %s/%s failed (%s): %s",
                           collection, kv, r.status_code, r.text[:200])
        except Exception as exc:  # noqa: BLE001
            logger.warning("PocketBase upsert_by_key error: %s", exc)
        return None

    def delete_by_key(self, collection: str, key_field: str, key_value: str) -> bool:
        """Delete the record whose `key_field` matches (best-effort)."""
        existing = self._rest_list(
            collection, filters=f'{key_field}="{key_value}"', per_page=1)
        if not existing:
            return True  # nothing to delete counts as success
        rid = existing[0].get("id")
        try:
            r = requests.delete(
                f"{self.url}/api/collections/{collection}/records/{rid}",
                headers=self._headers(), timeout=self.timeout)
            return r.status_code in (200, 204)
        except Exception as exc:  # noqa: BLE001
            logger.warning("PocketBase delete_by_key error: %s", exc)
            return False

    def ensure_collection(self, name: str,
                          fields: dict[str, str]) -> bool:
        """Best-effort auto-create a collection with text/json fields.

        Tries both the legacy (`schema`) and newer (`fields`) PocketBase
        collection formats so it works across PB versions. Returns True if
        the collection exists afterwards.
        """
        if self.get_collection(name):
            return True
        if not self.auth():
            return False
        entries_old = [{"name": k, "type": t} for k, t in fields.items()]
        body_variants = [
            {"name": name, "schema": entries_old},
            {"name": name, "fields": [
                {"name": k, "type": t} for k, t in fields.items()]},
        ]
        for body in body_variants:
            try:
                r = requests.post(f"{self.url}/api/collections",
                                  json=body, headers=self._headers(),
                                  timeout=self.timeout)
                if r.status_code in (200, 201):
                    logger.info("PocketBase collection '%s' created", name)
                    return True
            except Exception as exc:  # noqa: BLE001
                logger.debug("PocketBase ensure_collection error: %s", exc)
        logger.warning(
            "PocketBase collection '%s' missing and auto-create failed — "
            "create it manually in the PB admin UI.", name)
        return False

    def pull_all(self, collection: str, per_page: int = 500) -> list[dict]:
        """Fetch every record (plain dicts) — used at boot to seed local."""
        return self._rest_list(collection, filters="", per_page=per_page)

    def get_collection(self, name: str) -> Optional[dict]:
        """Return collection metadata, or None if missing/unreachable."""
        if not self.auth():
            return None
        if self._sdk is not None:
            try:
                return self._sdk.collections.get_one(name)
            except Exception:  # noqa: BLE001
                self._sdk = None
        try:
            r = requests.get(f"{self.url}/api/collections/{name}",
                             headers=self._headers(), timeout=self.timeout)
            if r.status_code == 200:
                return r.json()
        except Exception:  # noqa: BLE001
            pass
        return None

    def list(self, collection: str, filters: Optional[str] = None,
             per_page: int = 200) -> list[dict]:
        """List records in a collection (optional PocketBase filter string)."""
        if not self.auth():
            return []
        params = {"perPage": per_page}
        if filters:
            params["filter"] = filters
        if self._sdk is not None:
            try:
                res = self._sdk.collection(collection).get_list(
                    1, per_page, {"filter": filters or ""})
                return list(res.items)
            except Exception:  # noqa: BLE001
                self._sdk = None
        try:
            r = requests.get(f"{self.url}/api/collections/{collection}/records",
                             headers=self._headers(), params=params,
                             timeout=self.timeout)
            if r.status_code == 200:
                return r.json().get("items", [])
        except Exception:  # noqa: BLE001
            pass
        return []

    def upsert(self, collection: str, data: dict) -> Optional[dict]:
        """Create or update a record. If `data['id']` is present, update-or-create."""
        if not self.auth():
            return None
        rid = data.get("id")
        if self._sdk is not None:
            try:
                if rid:
                    try:
                        return self._sdk.collection(collection).update(rid, data)
                    except Exception:  # noqa: BLE001
                        return self._sdk.collection(collection).create(data)
                return self._sdk.collection(collection).create(data)
            except Exception as exc:  # noqa: BLE001
                logger.warning("PocketBase SDK upsert failed, trying REST: %s", exc)
                self._sdk = None
        # REST path
        try:
            if rid:
                r = requests.patch(
                    f"{self.url}/api/collections/{collection}/records/{rid}",
                    json=data, headers=self._headers(), timeout=self.timeout)
                if r.status_code == 200:
                    return r.json()
                # not found -> create with explicit id
                r = requests.post(
                    f"{self.url}/api/collections/{collection}/records",
                    json=data, headers=self._headers(), timeout=self.timeout)
                if r.status_code in (200, 201):
                    return r.json()
                logger.warning("PocketBase upsert failed (%s)", r.status_code)
                return None
            r = requests.post(
                f"{self.url}/api/collections/{collection}/records",
                json=data, headers=self._headers(), timeout=self.timeout)
            if r.status_code in (200, 201):
                return r.json()
            logger.warning("PocketBase create failed (%s)", r.status_code)
            return None
        except Exception as exc:  # noqa: BLE001
            logger.warning("PocketBase upsert error: %s", exc)
            return None


_client: Optional[PocketBaseClient] = None
_client_lock = threading.Lock()


def get_pb_client() -> Optional[PocketBaseClient]:
    """Return a cached client driven by settings (None if not configured)."""
    global _client
    if _client is not None:
        return _client
    with _client_lock:
        if _client is not None:
            return _client
        try:
            from admin.config import settings as _s
            url = getattr(_s, "POCKETBASE_URL", "")
            email = getattr(_s, "POCKETBASE_ADMIN_EMAIL", "")
            password = getattr(_s, "POCKETBASE_ADMIN_PASSWORD", "")
        except Exception:  # noqa: BLE001
            url = email = password = ""
        if not url:
            _client = None
            return None
        _client = PocketBaseClient(url, email, password)
    return _client
