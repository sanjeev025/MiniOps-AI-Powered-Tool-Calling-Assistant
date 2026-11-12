import pytest
from utcp.utcp_client import UtcpClient
from utcp_http.http_call_template import HttpCallTemplate


@pytest.mark.asyncio
async def test_utcp_tool_discovery_and_invocation(live_server):
    """Verify UTCP client can register manual, discover tools, and invoke endpoints."""
    client = await UtcpClient.create()

    template = HttpCallTemplate(
        name="demo_api",
        call_template_type="http",
        url=f"{live_server}/utcp",
        http_method="GET",
    )

    reg_result = await client.register_manual(template)
    assert reg_result.success

    tools = await client.search_tools("")
    tool_names = [t.name for t in tools]
    assert "demo_api.get_service_status" in tool_names
    assert "demo_api.get_recent_events" in tool_names

    status_res = await client.call_tool("demo_api.get_service_status", {})
    assert status_res.get("service") == "demo-api"
    assert status_res.get("status") == "healthy"
    assert status_res.get("version") == "1.0.2"
    assert status_res.get("uptime_seconds") == 86400

    events_res = await client.call_tool("demo_api.get_recent_events", {})
    assert len(events_res["events"]) == 2
    assert events_res["events"][0]["event"] == "Application restarted"

    # Tool inputs are forwarded as query params
    limited = await client.call_tool("demo_api.get_recent_events", {"limit": 1})
    assert len(limited["events"]) == 1
    assert limited["events"][0]["event"] == "Configuration updated"

    await client.close()
