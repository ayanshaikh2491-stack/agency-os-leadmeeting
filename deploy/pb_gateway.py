"""
PocketBase Supabase Gateway
===========================
Acts like a Supabase REST endpoint (/rest/v1/*) in front of PocketBase so the
existing backend code keeps working unchanged.

Backend sends:
  GET    /rest/v1/leads?select=*&order=created_at.asc
  POST   /rest/v1/leads            headers: apikey, Authorization, Prefer, Content-Profile
  PATCH  /rest/v1/leads?id=eq.5    body: {...}
  DELETE /rest/v1/leads?agent_name=eq.x

Gateway translates to PocketBase:
  GET    /api/collections/{table}/records
  POST   /api/collections/{table}/records
  PATCH  /api/collections/{table}/records/{id}
  DELETE /api/collections/{table}/records/{id}

Design:
  * collection name = "{profile}__{table}" when a workspace profile is sent,
    else "{table}" (so ws_agency and public stay isolated).
  * service key auth: the apikey / Bearer header must equal SERVICE_KEY env.
  * upsert (on_conflict + Prefer resolution=merge-duplicates) is emulated:
    find a row by the conflict columns, PATCH it, else POST.
  * generic collections: missing fields are auto-added (json type) so any
    backend payload works without schema changes.
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI(title="PocketBase Supabase Gateway")


def _read_env_key(path: str, name: str) -> str | None:
    """Read a KEY=VALUE pair from a dotenv-style file (no deps)."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith(name + "="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:  # noqa: BLE001
        pass
    return None


PB_URL = os.getenv("PB_URL", "http://127.0.0.1:8090")
PB_ADMIN_EMAIL = os.getenv("PB_ADMIN_EMAIL", "admin@tagsagency.local")
PB_ADMIN_PASS = os.getenv("PB_ADMIN_PASS", "pb-admin-2026-x9")
SERVICE_KEY = os.getenv("SERVICE_KEY") or _read_env_key(
    os.getenv("PB_ENV_FILE", "/home/ubuntu/sba-backend/.env"), "SUPABASE_SERVICE_KEY"
) or "sb-service-key-local"

# Common columns across agent tables (always present on collections we own).
_COMMON_FIELDS = [
    "agent_name", "thread_id", "checkpoint_id", "task_id",
    "memory_key", "data_key", "role", "content",
    "parent_checkpoint_id", "name", "email", "status", "phone",
    "category", "website", "workspace_name", "city_state", "address",
    "href", "text", "mode", "website_status", "email_provenance",
    "client_id", "has_website", "created_at", "updated_at",
]

_token: dict = {"value": None, "exp": 0}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _pb(method: str, path: str, body: dict | None = None, raw: bool = False):
    """Call PocketBase API with an admin token (auto-refresh)."""
    global _token
    if not _token["value"] or _token["exp"] < time.time() + 60:
        req = urllib.request.Request(
            PB_URL + "/api/collections/_superusers/auth-with-password",
            data=json.dumps({"identity": PB_ADMIN_EMAIL, "password": PB_ADMIN_PASS}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode())
            _token = {"value": data.get("token", ""), "exp": time.time() + 24 * 3600}
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"PocketBase auth failed: {e}")

    headers = {"Authorization": "Bearer " + _token["value"]}
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    else:
        data = None
    req = urllib.request.Request(PB_URL + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw_body = r.read().decode()
            if r.status == 204 or not raw_body:
                return None
            return json.loads(raw_body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()[:400]
        raise RuntimeError(f"PocketBase {method} {path} -> {e.code}: {err_body}")


def _collection_exists(name: str) -> bool:
    try:
        _pb("GET", f"/api/collections/{urllib.parse.quote(name)}")
        return True
    except Exception:
        return False


def _ensure_collection(name: str, body_keys: list[str] | None = None):
    """Create (or extend) a collection so all payload columns exist."""
    wanted = list(_COMMON_FIELDS)
    for k in body_keys or []:
        # "id" is a PocketBase system field; never add it as a data field.
        if k not in wanted and k != "id":
            wanted.append(k)

    if not _collection_exists(name):
        fields = []
        for f in wanted:
            fields.append(_field_spec(f, "json"))
        _pb("POST", "/api/collections", {
            "name": name, "type": "base", "fields": fields,
            "indexes": [], "listRule": "", "viewRule": "", "createRule": "",
            "updateRule": "", "deleteRule": "",
        })
        return

    # extend with missing fields (v0.23+ collection key is "fields")
    try:
        col = _pb("GET", f"/api/collections/{urllib.parse.quote(name)}")
    except Exception:
        return
    have = {f["name"] for f in col.get("fields", [])}
    missing = [f for f in wanted if f not in have and f not in ("id", "created", "updated")]
    if not missing:
        return
    fields = list(col.get("fields", []))
    for f in missing:
        fields.append(_field_spec(f, "json"))
    _pb("PATCH", f"/api/collections/{urllib.parse.quote(name)}", {
        "name": name, "type": "base", "fields": fields, "indexes": col.get("indexes", []),
        "listRule": "", "viewRule": "", "createRule": "", "updateRule": "", "deleteRule": "",
    })


def _field_spec(name: str, ftype: str) -> dict:
    spec = {"name": name, "type": ftype, "required": False, "system": False}
    if ftype == "json":
        spec["maxSize"] = 4000000
    if ftype == "text":
        spec["max"] = 0
    return spec


# ── PostgREST query translation ────────────────────────────────────────────

def _parse_filter_value(raw: str):
    """Decode a PostgREST filter value like in.(a,b,c), eq.x, ilike.%x%."""
    raw = urllib.parse.unquote(raw)
    return raw


def _build_filter(query) -> str:
    parts = []
    for key, vals in query.multi_items():
        if key in ("select", "order", "limit", "offset", "on_conflict", "prefer", "columns", "count"):
            continue
        # multi_items yields (key, value) tuples; value is a str (or a list
        # for repeated params). Never iterate a str by hand.
        items = vals if isinstance(vals, list) else [vals]
        for v in items:
            if "." not in v:
                continue
            op, _, val = v.partition(".")
            val = _parse_filter_value(val)
            if op == "eq":
                parts.append(f"{key} = {_sql_str(val)}")
            elif op == "neq":
                parts.append(f"{key} != {_sql_str(val)}")
            elif op == "gt":
                parts.append(f"{key} > {_sql_str(val)}")
            elif op == "gte":
                parts.append(f"{key} >= {_sql_str(val)}")
            elif op == "lt":
                parts.append(f"{key} < {_sql_str(val)}")
            elif op == "lte":
                parts.append(f"{key} <= {_sql_str(val)}")
            elif op == "ilike":
                # ilike.%x% -> PocketBase ~ (case-insensitive contains)
                parts.append(f"{key} ~ {_sql_str(val.strip('%'))}")
            elif op == "like":
                parts.append(f"{key} ~ {_sql_str(val.strip('%'))}")
            elif op == "is":
                if val.lower() == "null":
                    parts.append(f"({key} = '' || {key} = null)")
                else:
                    parts.append(f"{key} = {_sql_str(val)}")
            elif op == "in":
                items = [x.strip().strip("'\"") for x in val.strip("()").split(",")]
                if items:
                    parts.append(f"({key} in ({', '.join(_sql_str(x) for x in items)}))")
    return " && ".join(parts) if parts else ""


def _sql_str(v: str) -> str:
    return "'" + v.replace("'", "''") + "'"


def _build_sort(query) -> str:
    order = query.get("order") or ""
    out = []
    for part in order.split(","):
        part = part.strip()
        if not part:
            continue
        if part.endswith(".desc"):
            out.append("-" + part[:-5])
        else:
            out.append(part.replace(".asc", ""))
    return ",".join(out)


def _build_limit(query) -> int | None:
    """PostgREST semantics: no `limit` param => None (return ALL rows).
    `limit=N` => at most N rows. Invalid values fall back to all rows."""
    raw = query.get("limit")
    if not raw:
        return None
    try:
        return max(int(raw), 1)
    except ValueError:
        return None


def _fetch_page(collection: str, page: int, per: int, filter_s: str, sort: str, fields: str) -> list:
    params = {"page": str(page), "perPage": str(per)}
    if filter_s:
        params["filter"] = filter_s
    if sort:
        params["sort"] = sort
    if fields:
        params["fields"] = fields
    qs = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    data = _pb("GET", f"/api/collections/{urllib.parse.quote(collection)}/records?{qs}")
    return data.get("items", []) if isinstance(data, dict) else []


def _list_records(collection: str, query) -> list:
    """List records honoring PostgREST `limit` semantics: no limit => ALL rows
    (page through PocketBase, whose perPage caps at 200)."""
    filter_s = _build_filter(query)
    try:
        page = int(query.get("page") or "1")
    except ValueError:
        page = 1
    limit = _build_limit(query)
    sort = _build_sort(query)
    fields = _build_fields(query)
    out: list = []
    if limit is None:
        cur = page
        while True:
            rows = _fetch_page(collection, cur, 200, filter_s, sort, fields)
            if not rows:
                break
            out.extend(rows)
            cur += 1
            if len(rows) < 200:
                break
    else:
        remaining = limit
        cur = page
        while remaining > 0:
            per = min(200, remaining)
            rows = _fetch_page(collection, cur, per, filter_s, sort, fields)
            if not rows:
                break
            out.extend(rows)
            remaining -= len(rows)
            cur += 1
            if len(rows) < per:
                break
    return out


def _build_fields(query) -> str:
    sel = query.get("select") or "*"
    if sel == "*":
        return ""
    return ",".join(x.strip() for x in sel.split(",") if x.strip())


def _find_by_filter(collection: str, query) -> list:
    """Return ALL records matching PostgREST filter query (pages through
    PocketBase, whose perPage caps at 200)."""
    filter_s = _build_filter(query)
    if not filter_s:
        return []
    out: list = []
    cur = 1
    while True:
        params = {"page": str(cur), "perPage": "200", "filter": filter_s}
        qs = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        print(f"[gw] find filter={filter_s!r} page={cur}", flush=True)
        data = _pb("GET", f"/api/collections/{urllib.parse.quote(collection)}/records?{qs}")
        items = data.get("items", []) if isinstance(data, dict) else []
        out.extend(items)
        if len(items) < 200:
            break
        cur += 1
    return out


def _record_out(rec: dict | None) -> dict | None:
    """Map a PocketBase record to Supabase-ish shape (id stays, drop extras)."""
    if rec is None:
        return None
    out = dict(rec)
    out.pop("collectionId", None)
    out.pop("collectionName", None)
    return out


def _is_pb_id(v) -> bool:
    """PocketBase ids are exactly 15 chars [a-z0-9]. UUIDs/ints are not."""
    return isinstance(v, str) and len(v) == 15 and v.isalnum() and v.islower()


def _sanitize_payload(payload: dict) -> dict:
    """Move a non-PocketBase 'id' (Supabase UUID/int) to 'legacy_id' so
    PocketBase generates its own id instead of 400ing."""
    out = dict(payload)
    if "id" in out and not _is_pb_id(out["id"]):
        out["legacy_id"] = out.pop("id")
    return out


# ── HTTP handlers ─────────────────────────────────────────────────────────

def _check_auth(request: Request) -> Response | None:
    key = request.headers.get("apikey") or ""
    bearer = request.headers.get("authorization") or ""
    if bearer.startswith("Bearer "):
        key = key or bearer[7:]
    if key != SERVICE_KEY:
        return JSONResponse({"code": "401", "message": "Invalid API key", "hint": "check SERVICE_KEY"}, status_code=401)
    return None


def _collection_name(request: Request, table: str) -> str:
    profile = request.headers.get("content-profile") or request.headers.get("accept-profile") or "public"
    if profile in ("public", ""):
        return table
    return f"{profile}__{table}"


@app.api_route("/rest/v1/{table}", methods=["GET", "POST", "PATCH", "DELETE"])
async def rest_v1(table: str, request: Request):
    auth = _check_auth(request)
    if auth:
        return auth
    collection = _collection_name(request, table)
    prefer = request.headers.get("prefer", "")
    on_conflict = request.query_params.get("on_conflict", "")

    # ── GET: list ──
    if request.method == "GET":
        _ensure_collection(collection)
        try:
            rows = _list_records(collection, request.query_params)
            return JSONResponse([_record_out(r) for r in rows])
        except Exception as e:  # noqa: BLE001
            return JSONResponse({"error": str(e)}, status_code=500)

    # ── body ──
    try:
        body = await request.json() if await request.body() else {}
    except Exception:
        body = {}

    # ── POST: create (or upsert when on_conflict + merge-duplicates) ──
    if request.method == "POST":
        payload = _sanitize_payload(dict(body))
        _ensure_collection(collection, list(payload.keys()))
        ts = _now_iso()
        if on_conflict and "merge-duplicates" in prefer:
            conflict_q = []
            for col in on_conflict.split(","):
                col = col.strip()
                if col in body:
                    conflict_q.append(f"{col} = {_sql_str(str(body[col]))}")
            if conflict_q:
                fq = " && ".join(conflict_q)
                qs = urllib.parse.urlencode({"page": "1", "perPage": "10", "filter": fq})
                try:
                    data = _pb("GET", f"/api/collections/{urllib.parse.quote(collection)}/records?{qs}")
                    existing = data.get("items", []) if isinstance(data, dict) else []
                    if existing:
                        rec = existing[0]
                        merged = _sanitize_payload({**rec, **body, "updated_at": ts})
                        merged.pop("id", None)
                        merged.pop("created", None)
                        merged.pop("updated", None)
                        upd = _pb("PATCH", f"/api/collections/{urllib.parse.quote(collection)}/records/{rec['id']}", merged)
                        return JSONResponse([_record_out(upd)])
                except Exception:  # noqa: BLE001
                    pass  # fall through to create
        payload.setdefault("created_at", ts)
        payload.setdefault("updated_at", ts)
        try:
            rec = _pb("POST", f"/api/collections/{urllib.parse.quote(collection)}/records", payload)
            if "return=representation" in prefer:
                return JSONResponse([_record_out(rec)])
            return JSONResponse(_record_out(rec) or {}, status_code=201)
        except Exception as e:  # noqa: BLE001
            return JSONResponse({"error": str(e)}, status_code=500)

    # ── PATCH: update by filter ──
    if request.method == "PATCH":
        payload = _sanitize_payload(dict(body))
        payload.pop("id", None)
        _ensure_collection(collection, list(payload.keys()))
        try:
            targets = _find_by_filter(collection, request.query_params)
            updated = []
            ts = _now_iso()
            for rec in targets:
                payload["updated_at"] = ts
                upd = _pb("PATCH", f"/api/collections/{urllib.parse.quote(collection)}/records/{rec['id']}", payload)
                updated.append(_record_out(upd))
            return JSONResponse(updated)
        except Exception as e:  # noqa: BLE001
            return JSONResponse({"error": str(e)}, status_code=500)

    # ── DELETE: delete by filter ──
    if request.method == "DELETE":
        try:
            targets = _find_by_filter(collection, request.query_params)
            for rec in targets:
                _pb("DELETE", f"/api/collections/{urllib.parse.quote(collection)}/records/{rec['id']}")
            return Response(status_code=204)
        except Exception as e:  # noqa: BLE001
            return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/rest/v1/{table}/{rid}")
async def rest_v1_row(table: str, rid: str, request: Request):
    auth = _check_auth(request)
    if auth:
        return auth
    collection = _collection_name(request, table)
    _ensure_collection(collection)
    try:
        rec = _pb("GET", f"/api/collections/{urllib.parse.quote(collection)}/records/{rid}")
        return JSONResponse(_record_out(rec))
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=404)


@app.get("/health")
@app.get("/api/health")
async def health():
    return {"ok": True, "service": "pb-supabase-gateway", "pb": PB_URL}
