"""UTCP bridge handlers for Hermes Agent.

Every discovered tool gets a handler built by ``make_handler`` that invokes the
underlying endpoint through the UTCP Python client, observed via Langfuse.
"""

import json
import logging
import os
import threading
from typing import Any, Awaitable, Callable, Dict, Optional

from langfuse import observe
from utcp.utcp_client import UtcpClient
from utcp_http.http_call_template import HttpCallTemplate

from .discovery import manual_url

logger = logging.getLogger("hermes.plugins.utcp")

MANUAL_NAME = "demo_api"

# One process-wide client. utcp_http opens a fresh aiohttp session per request, so the
# client is safe to reuse across the fresh event loops Hermes may run handlers in.
# A threading.Lock (not asyncio.Lock) guards the slot, because asyncio locks bind to one loop.
_cache_lock = threading.Lock()
_utcp_client: Optional[UtcpClient] = None


def get_active_llm_info() -> Dict[str, str]:
    """Retrieve current LLM provider and model configured via environment."""
    provider = os.getenv("HERMES_INFERENCE_PROVIDER") or os.getenv("LLM_PROVIDER", "openai-api")
    model = os.getenv("HERMES_MODEL") or os.getenv("LLM_MODEL", "gpt-4o-mini")
    return {"provider": provider, "model": model}


def reset_client_cache() -> None:
    global _utcp_client
    with _cache_lock:
        _utcp_client = None


async def get_or_create_utcp_client(url: Optional[str] = None) -> UtcpClient:
    """Return the shared UTCP client, registering the manual on first use.

    A failed registration (e.g. the demo API isn't up yet) is never cached, so the
    next call retries instead of failing with "Tool not found" for the process lifetime.
    """
    global _utcp_client
    with _cache_lock:
        if _utcp_client is not None:
            return _utcp_client

    client = await UtcpClient.create()
    template = HttpCallTemplate(
        name=MANUAL_NAME,
        call_template_type="http",
        url=url or manual_url(),
        http_method="GET",
    )
    result = await client.register_manual(template)
    if not result.success:
        await client.close()
        raise RuntimeError(f"UTCP manual registration failed: {result.errors}")

    with _cache_lock:
        if _utcp_client is None:
            _utcp_client = client
        return _utcp_client


async def call_utcp_tool(tool_name: str, params: Optional[Dict[str, Any]] = None) -> str:
    """Invoke a UTCP tool by its unprefixed name and return a JSON string for the LLM."""
    llm_info = get_active_llm_info()
    logger.debug("Executing %s under provider=%s model=%s", tool_name, llm_info["provider"], llm_info["model"])
    try:
        client = await get_or_create_utcp_client()
        result = await client.call_tool(f"{MANUAL_NAME}.{tool_name}", params or {})
        return json.dumps(result)
    except Exception as exc:
        logger.error("Error executing %s via UTCP: %s", tool_name, exc)
        return json.dumps({
            "error": True,
            "message": str(exc),
            "tool": tool_name,
            "provider": llm_info["provider"],
        })


def make_handler(tool_name: str) -> Callable[..., Awaitable[str]]:
    """Build a Langfuse-observed async Hermes handler for one UTCP tool."""

    @observe(name=tool_name)
    async def handler(args: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        return await call_utcp_tool(tool_name, args)

    handler.__name__ = f"handle_{tool_name}"
    return handler


# Named handlers for the known demo tools (kept for direct use and tests).
handle_get_service_status = make_handler("get_service_status")
handle_get_recent_events = make_handler("get_recent_events")
