"""Agency-wide Agent Health Monitor — shared 24/7 construction probe.

Every registered worker agent is probed on a fixed interval to detect
import/compile/missing-dependency/construct failures BEFORE a client hits the
chat box. The probe only builds the agent (module import + class resolve +
instantiate) — it does NOT call the LLM, so it is cheap and catches the
historical failure class (langgraph 4.x removed symbols -> ImportError crashed
all 7 on-demand agents silently until a user chatted).

Wire this into the FastAPI lifespan (see admin.main) via start_monitor() /
stop_monitor(), then read status from get_monitor().get_health().

Probe targets mirror admin.api.routes.agent_aliases.AGENT_SLUG_MAP plus the
SBA autopilot runner. "memory" is intentionally included even though no
module exists, so the monitor surfaces that gap instead of hiding it.
"""
from __future__ import annotations

import asyncio
import importlib
import logging
import traceback
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 5 * 60  # every 5 minutes

# slug -> (module_path, class_name, init_kwargs)
# Mirrors the real routing table in admin.workspace.manager.route_to_agent.
_AGENT_PROBES: dict[str, dict[str, Any]] = {
    "seo": {
        "module": "admin.workspace.agents.seo",
        "class": "SEOAgent",
        "kwargs": {"workspace_name": "HealthCheck", "client_name": "HealthCheck"},
    },
    "ads": {
        "module": "admin.workspace.agents.ads",
        "class": "AdsAgent",
        "kwargs": {"workspace_name": "HealthCheck", "client_name": "HealthCheck"},
    },
    "website": {
        "module": "admin.workspace.agents.website",
        "class": "WebsiteAgent",
        "kwargs": {"workspace_name": "HealthCheck", "client_name": "HealthCheck"},
    },
    "social": {
        "module": "admin.workspace.agents.social",
        "class": "SocialAgent",
        "kwargs": {"workspace_name": "HealthCheck", "client_name": "HealthCheck"},
    },
    "analytics": {
        "module": "admin.workspace.agents.analytics",
        "class": "AnalyticsAgent",
        "kwargs": {"workspace_name": "HealthCheck", "client_name": "HealthCheck"},
    },
    "content": {
        "module": "admin.workspace.agents.content",
        "class": "ContentAgent",
        "kwargs": {
            "workspace_id": "health",
            "workspace_name": "HealthCheck",
            "client_name": "HealthCheck",
        },
    },
    # Intentionally probed: registered in AGENT_SLUG_MAP but no module exists.
    "memory": {
        "module": "admin.workspace.agents.memory",
        "class": "MemoryAgent",
        "kwargs": {"workspace_name": "HealthCheck", "client_name": "HealthCheck"},
    },
    # SBA autopilot runner — the only always-on agent.
    "sba": {
        "module": "admin.agency.sba_autopilot",
        "class": "SBAWorkspaceRunner",
        "kwargs": {},
    },
}


def probe_agent(slug: str, spec: dict[str, Any]) -> dict[str, Any]:
    """Construct the agent and report health. No LLM call.

    Returns a health record: status healthy|down, error, trace (optional).
    """
    now = datetime.now(timezone.utc).isoformat()
    try:
        module = importlib.import_module(spec["module"])
        cls = getattr(module, spec["class"], None)
        if cls is None:
            return {
                "slug": slug,
                "status": "down",
                "error": f"class '{spec['class']}' not found in {spec['module']}",
                "last_checked": now,
            }
        try:
            cls(**spec.get("kwargs", {}))
        except Exception as exc:  # noqa: BLE001 — construction-time failure
            return {
                "slug": slug,
                "status": "down",
                "error": f"instantiation failed: {type(exc).__name__}: {exc}",
                "last_checked": now,
            }
        return {"slug": slug, "status": "healthy", "error": None, "last_checked": now}
    except Exception as exc:  # noqa: BLE001 — import/compile/missing-dep
        return {
            "slug": slug,
            "status": "down",
            "error": f"{type(exc).__name__}: {exc}",
            "trace": traceback.format_exc(limit=3),
            "last_checked": now,
        }


class AgentHealthMonitor:
    """Background monitor that keeps every agent's construction health live."""

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._health: dict[str, dict[str, Any]] = {}
        # Consecutive failure counts per slug (alert only on sustained down).
        self._failures: dict[str, int] = {slug: 0 for slug in _AGENT_PROBES}
        self._alerts: list[dict[str, Any]] = []

    async def start(self) -> None:
        logger.info("Agent Health Monitor started (interval=%ds)", CHECK_INTERVAL_SECONDS)
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            logger.info("Agent Health Monitor stopped")

    async def get_health(self) -> dict[str, Any]:
        async with self._lock:
            if not self._health:
                self._health = {slug: probe_agent(slug, spec) for slug, spec in _AGENT_PROBES.items()}
            down = [s for s, r in self._health.items() if r["status"] == "down"]
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "all_healthy": len(down) == 0,
                "down_count": len(down),
                "agents": self._health,
                "alerts": list(self._alerts),
            }

    def get_alerts(self) -> list[dict[str, Any]]:
        alerts = list(self._alerts)
        self._alerts.clear()
        return alerts

    async def _run_loop(self) -> None:
        while True:
            try:
                results: dict[str, dict[str, Any]] = {}
                for slug, spec in _AGENT_PROBES.items():
                    rec = probe_agent(slug, spec)
                    results[slug] = rec
                    if rec["status"] == "down":
                        self._failures[slug] = self._failures.get(slug, 0) + 1
                        # Alert on first sustained failure (>=2 consecutive checks).
                        if self._failures[slug] == 2:
                            msg = f"Agent '{slug}' is DOWN: {rec['error']}"
                            self._alerts.append({"severity": "critical", "agent": slug, "message": msg})
                            logger.error("AGENT HEALTH [%s]: %s", slug, rec["error"])
                    else:
                        if self._failures.get(slug, 0) >= 2:
                            logger.info("AGENT HEALTH [%s]: recovered", slug)
                        self._failures[slug] = 0

                async with self._lock:
                    self._health = results

                await asyncio.sleep(CHECK_INTERVAL_SECONDS)
            except asyncio.CancelledError:
                break
            except Exception as exc:  # noqa: BLE001
                logger.error("Agent Health Monitor loop error: %s", exc)
                await asyncio.sleep(60)


_monitor: AgentHealthMonitor | None = None


def get_monitor() -> AgentHealthMonitor:
    global _monitor
    if _monitor is None:
        _monitor = AgentHealthMonitor()
    return _monitor


async def start_monitor() -> AgentHealthMonitor:
    """Start the shared monitor (call once in the FastAPI lifespan)."""
    global _monitor
    m = get_monitor()
    await m.start()
    return m


async def stop_monitor() -> None:
    if _monitor is not None:
        await _monitor.stop()
