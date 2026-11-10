"""UTCP bridge handlers for Hermes Agent.

Exposes handlers for `get_service_status` and `get_recent_events` that discover
and invoke the underlying endpoints via the UTCP Python client, observed via Langfuse.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional
from langfuse import observe
from utcp.utcp_client import UtcpClient
from utcp_http.http_call_template import HttpCallTemplate


logger = logging.getLogger("hermes.plugins.utcp")

# Configurable UTCP manual URL
DEFAULT_MANUAL_URL = "http://127.0.0.1:8000/utcp"
_utcp_client: Optional[UtcpClient] = None
_client_lock = asyncio.Lock()


def get_active_llm_info() -> Dict[str, str]:
    """Retrieve current LLM provider and model configured via environment."""
    provider = os.getenv("HERMES_INFERENCE_PROVIDER") or os.getenv("LLM_PROVIDER", "openai-api")
    model = os.getenv("HERMES_MODEL") or os.getenv("LLM_MODEL", "gpt-4o-mini")
    return {"provider": provider, "model": model}


async def get_or_create_utcp_client(manual_url: Optional[str] = None) -> UtcpClient:
    """Lazily initialize and register the UTCP manual template."""
    global _utcp_client
    if _utcp_client is not None:
        return _utcp_client

    async with _client_lock:
        if _utcp_client is not None:
            return _utcp_client

        url = manual_url or os.getenv("UTCP_MANUAL_URL", DEFAULT_MANUAL_URL)
        client = await UtcpClient.create()
        template = HttpCallTemplate(
            name="demo_api",
            call_template_type="http",
            url=url,
            http_method="GET",
        )
        await client.register_manual(template)
        _utcp_client = client
        return _utcp_client


@observe(name="get_service_status")
async def handle_get_service_status(params: Optional[Dict[str, Any]] = None, **kwargs) -> str:
    """Retrieve demo service status via UTCP."""
    llm_info = get_active_llm_info()
    logger.debug(f"Executing get_service_status under provider={llm_info['provider']} model={llm_info['model']}")
    try:
        client = await get_or_create_utcp_client()
        result = await client.call_tool("demo_api.get_service_status", params or {})
        return json.dumps(result)
    except Exception as exc:
        logger.error(f"Error executing get_service_status via UTCP: {exc}")
        return json.dumps({
            "error": True,
            "message": str(exc),
            "tool": "get_service_status",
            "provider": llm_info["provider"],
        })


@observe(name="get_recent_events")
async def handle_get_recent_events(params: Optional[Dict[str, Any]] = None, **kwargs) -> str:
    """Retrieve recent application events via UTCP."""
    llm_info = get_active_llm_info()
    logger.debug(f"Executing get_recent_events under provider={llm_info['provider']} model={llm_info['model']}")
    try:
        client = await get_or_create_utcp_client()
        result = await client.call_tool("demo_api.get_recent_events", params or {})
        return json.dumps(result)
    except Exception as exc:
        logger.error(f"Error executing get_recent_events via UTCP: {exc}")
        return json.dumps({
            "error": True,
            "message": str(exc),
            "tool": "get_recent_events",
            "provider": llm_info["provider"],
        })


# Synchronous entrypoint bridge if Hermes calls synchronously
def sync_handle_get_service_status(params: Optional[Dict[str, Any]] = None, **kwargs) -> str:
    """Synchronous bridge for handle_get_service_status."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, handle_get_service_status(params, **kwargs))
            return future.result()
    else:
        return asyncio.run(handle_get_service_status(params, **kwargs))


def sync_handle_get_recent_events(params: Optional[Dict[str, Any]] = None, **kwargs) -> str:
    """Synchronous bridge for handle_get_recent_events."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, handle_get_recent_events(params, **kwargs))
            return future.result()
    else:
        return asyncio.run(handle_get_recent_events(params, **kwargs))
