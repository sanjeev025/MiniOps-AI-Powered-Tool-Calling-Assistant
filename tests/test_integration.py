import json
import pytest
from unittest.mock import MagicMock
from hermes_plugin import register
from hermes_plugin.schemas import GET_SERVICE_STATUS_SCHEMA, GET_RECENT_EVENTS_SCHEMA
from hermes_plugin.tools import (
    handle_get_service_status,
    handle_get_recent_events,
    sync_handle_get_service_status,
    sync_handle_get_recent_events,
)
from tests.test_utcp import live_server  # reuse live server fixture


def test_plugin_registration():
    """Verify register(ctx) registers both tools with proper arguments."""
    mock_ctx = MagicMock()
    register(mock_ctx)

    assert mock_ctx.register_tool.call_count == 2
    calls = mock_ctx.register_tool.call_args_list

    names = [call.kwargs["name"] for call in calls]
    assert "get_service_status" in names
    assert "get_recent_events" in names

    for call in calls:
        assert call.kwargs["toolset"] == "demo_ops"
        assert call.kwargs["is_async"] is True
        assert call.kwargs["schema"] in [GET_SERVICE_STATUS_SCHEMA, GET_RECENT_EVENTS_SCHEMA]


@pytest.mark.asyncio
async def test_plugin_handlers_against_live_service(live_server, monkeypatch):
    """Verify async handlers invoke the live FastAPI endpoints through UTCP."""
    monkeypatch.setenv("UTCP_MANUAL_URL", f"{live_server}/utcp")

    # Reset client singleton to pick up the test server URL
    import hermes_plugin.tools as tools_mod
    tools_mod._utcp_client = None

    # Test get_service_status handler
    status_raw = await handle_get_service_status({})
    assert isinstance(status_raw, str)
    status_data = json.loads(status_raw)
    assert status_data["service"] == "demo-api"
    assert status_data["status"] == "healthy"
    assert status_data["version"] == "1.0.2"

    # Test get_recent_events handler
    events_raw = await handle_get_recent_events({})
    assert isinstance(events_raw, str)
    events_data = json.loads(events_raw)
    assert "events" in events_data
    assert len(events_data["events"]) == 2


def test_plugin_sync_handlers_bridge(live_server, monkeypatch):
    """Verify synchronous bridge wrappers function properly without event loop errors."""
    monkeypatch.setenv("UTCP_MANUAL_URL", f"{live_server}/utcp")

    import hermes_plugin.tools as tools_mod
    tools_mod._utcp_client = None

    status_raw = sync_handle_get_service_status({})
    status_data = json.loads(status_raw)
    assert status_data["status"] == "healthy"

    events_raw = sync_handle_get_recent_events({})
    events_data = json.loads(events_raw)
    assert "events" in events_data


@pytest.mark.asyncio
async def test_plugin_handler_error_handling(monkeypatch):
    """Verify handlers catch exceptions gracefully and return structured error JSON."""
    monkeypatch.setenv("UTCP_MANUAL_URL", "http://127.0.0.1:59999/invalid_utcp")

    import hermes_plugin.tools as tools_mod
    tools_mod._utcp_client = None

    err_raw = await handle_get_service_status({})
    err_data = json.loads(err_raw)
    assert err_data.get("error") is True
    assert "message" in err_data
    assert err_data.get("tool") == "get_service_status"
