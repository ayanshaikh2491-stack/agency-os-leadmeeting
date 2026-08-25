"""Agency-wide LLM rate limiter (OpenCode Zen RPM cap), enforced in code.

Boss rule: any agent may fire LLM calls freely - this limiter keeps ALL of
them under the provider's RPM ceiling (default 38, margin below 40) so 429s
never happen, even during CEO parallel blasts.

How: installs an httpx request-hook into every `openai.AsyncOpenAI(...)`
construction (via a one-time __init__ patch in main lifespan), so each LLM
request awaits a sliding-window slot before hitting the wire. Call sites stay
untouched; future agents inherit the cap automatically.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from collections import deque

logger = logging.getLogger(__name__)

RPM = max(1, int(os.getenv("AGENCY_LLM_RPM", "38")))
_WINDOW = 60.0

_lock = asyncio.Lock()
_hits: deque[float] = deque()


async def acquire() -> None:
    """Await until a request slot frees up under the sliding RPM window."""
    while True:
        async with _lock:
            now = time.monotonic()
            while _hits and now - _hits[0] >= _WINDOW:
                _hits.popleft()
            if len(_hits) < RPM:
                _hits.append(now)
                return
            wait = _WINDOW - (now - _hits[0])
        logger.debug("LLM rate limit reached, waiting %.1fs", wait)
        await asyncio.sleep(min(max(wait, 0.05), 5.0))


def install() -> bool:
    """Patch openai.AsyncOpenAI so every new client shares a throttled pool.

    Idempotent. Returns False quietly when openai/httpx are unavailable.
    """
    try:
        import httpx
        import openai
    except ImportError:  # noqa: BLE001
        return False
    if getattr(openai.AsyncOpenAI, "_tags_throttled", False):
        return True

    async def _hook(request: httpx.Request) -> None:
        await acquire()

    shared_http = httpx.AsyncClient(
        timeout=120.0, event_hooks={"request": [_hook]})
    orig_init = openai.AsyncOpenAI.__init__

    def patched(self, *args, **kwargs):  # noqa: ANN002, ANN003
        kwargs.setdefault("http_client", shared_http)
        orig_init(self, *args, **kwargs)

    openai.AsyncOpenAI.__init__ = patched
    openai.AsyncOpenAI._tags_throttled = True  # type: ignore[attr-defined]
    logger.info("LLM rate limiter installed (%d RPM shared pool)", RPM)
    return True
