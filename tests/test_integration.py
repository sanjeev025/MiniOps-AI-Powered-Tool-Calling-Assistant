import asyncio
import json
from unittest.mock import MagicMock

import pytest

from hermes_plugin import register
from hermes_plugin.discovery import discover_tools
from hermes_plugin.schemas import FALLBACK_SCHEMAS
from hermes_plugin.tools import handle_get_recent_events, handle_get_service_status

UNREACHABLE = "http://127.0.0.1:59999/utcp"


def _registered(mock_ctx):
    return {c.kwargs["name"]: c.kwargs for c in mock_ctx.register_tool.call_args_list}


def test_register_discovers_tools_from_manual(live_server, monkeypatch):
    """register(ctx) registers whatever the live UTCP manual lists, including input params."""
    monkeypatch.setenv("UTCP_MANUAL_URL", f"{live_server}/utcp")
    mock_ctx = MagicMock()
    register(mock_ctx)

    tools = _registered(mock_ctx)
    assert set(tools) == {"get_service_status", "get_recent_events"}
    for kw in tools.values():
        assert kw["toolset"] == "demo_ops"
        assert kw["is_async"] is True
        assert kw["schema"]["parameters"]["type"] == "object"

    params = tools["get_recent_events"]["schema"]["parameters"]
    assert params["properties"]["limit"]["type"] == "integer"


def test_register_falls_back_when_manual_unreachable(monkeypatch):
    monkeypatch.setenv("UTCP_MANUAL_URL", UNREACHABLE)
    mock_ctx = MagicMock()
    register(mock_ctx)

    tools = _registered(mock_ctx)
    assert set(tools) == {s["name"] for s in FALLBACK_SCHEMAS}


def test_discovered_schema_matches_fallback(live_server):
    """Fallback schemas stay in sync with the live manual."""
    discovered = {t["name"]: t["parameters"] for t in discover_tools(f"{live_server}/utcp")}
    fallback = {s["name"]: s["parameters"] for s in FALLBACK_SCHEMAS}
    assert discovered == fallback


@pytest.mark.asyncio
async def test_handlers_against_live_service(live_server, monkeypatch):
    """Async handlers invoke the live FastAPI endpoints through UTCP."""
    monkeypatch.setenv("UTCP_MANUAL_URL", f"{live_server}/utcp")

    status_data = json.loads(await handle_get_service_status({}))
    assert status_data["service"] == "demo-api"
    assert status_data["status"] == "healthy"

    events_data = json.loads(await handle_get_recent_events({"limit": 1}))
    assert len(events_data["events"]) == 1


def test_handlers_survive_fresh_event_loops(live_server, monkeypatch):
    """Hermes may run each handler call in a new event loop; the shared client must keep working."""
    monkeypatch.setenv("UTCP_MANUAL_URL", f"{live_server}/utcp")

    first = json.loads(asyncio.run(handle_get_service_status({})))
    second = json.loads(asyncio.run(handle_get_service_status({})))
    assert first.get("status") == "healthy"
    assert second.get("status") == "healthy", second


def test_failed_registration_is_not_cached(live_server, monkeypatch):
    """A failure (service down) must not poison the cache once the service is reachable."""

    async def scenario():
        monkeypatch.setenv("UTCP_MANUAL_URL", UNREACHABLE)
        err = json.loads(await handle_get_service_status({}))
        monkeypatch.setenv("UTCP_MANUAL_URL", f"{live_server}/utcp")
        ok = json.loads(await handle_get_service_status({}))
        return err, ok

    err, ok = asyncio.run(scenario())
    assert err.get("error") is True
    assert ok.get("status") == "healthy", ok


@pytest.mark.asyncio
async def test_handler_error_handling(monkeypatch):
    """Handlers catch exceptions and return structured error JSON."""
    monkeypatch.setenv("UTCP_MANUAL_URL", UNREACHABLE)

    err_data = json.loads(await handle_get_service_status({}))
    assert err_data.get("error") is True
    assert "message" in err_data
    assert err_data.get("tool") == "get_service_status"
