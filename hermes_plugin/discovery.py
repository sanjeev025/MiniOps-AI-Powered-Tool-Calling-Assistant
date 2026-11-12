"""Discover tools from the UTCP manual and turn them into Hermes tool schemas."""

import copy
import logging
import os
from typing import Any, Dict, List

import httpx
import utcp_http  # noqa: F401  (registers the "http" call-template type for manual validation)
from utcp.data.utcp_manual import UtcpManual

from .schemas import FALLBACK_SCHEMAS

logger = logging.getLogger("hermes.plugins.utcp")

DEFAULT_MANUAL_URL = "http://127.0.0.1:8000/utcp"


def manual_url() -> str:
    return os.getenv("UTCP_MANUAL_URL", DEFAULT_MANUAL_URL)


def _to_parameters(inputs: Any) -> Dict[str, Any]:
    params = inputs.model_dump(exclude_none=True, by_alias=True) if inputs is not None else {}
    params.setdefault("type", "object")
    params.setdefault("properties", {})
    params.setdefault("required", [])
    return params


def discover_tools(url: str | None = None, timeout: float = 3.0) -> List[Dict[str, Any]]:
    """Fetch the UTCP manual and return OpenAI-style tool schemas plus tags.

    Each entry: ``{"name", "description", "parameters", "tags"}``. Falls back to the
    static ``FALLBACK_SCHEMAS`` if the manual is unreachable or invalid.
    """
    url = url or manual_url()
    try:
        resp = httpx.get(url, timeout=timeout)
        resp.raise_for_status()
        manual = UtcpManual.model_validate(resp.json())
    except Exception as exc:
        logger.warning("UTCP discovery from %s failed (%s); using fallback tool schemas.", url, exc)
        return [dict(copy.deepcopy(s), tags=[]) for s in FALLBACK_SCHEMAS]

    tools = [
        {
            "name": tool.name,
            "description": tool.description,
            "parameters": _to_parameters(tool.inputs),
            "tags": list(tool.tags or []),
        }
        for tool in manual.tools
    ]
    logger.info("Discovered %d UTCP tools from %s: %s", len(tools), url, [t["name"] for t in tools])
    return tools
