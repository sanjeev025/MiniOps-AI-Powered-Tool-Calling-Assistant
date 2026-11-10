import subprocess
import sys
import time
import httpx
import pytest
import pytest_asyncio
from utcp.utcp_client import UtcpClient
from utcp_http.http_call_template import HttpCallTemplate


TEST_PORT = 8005
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"


@pytest.fixture(scope="module")
def live_server():
    """Start the FastAPI service in a background subprocess for UTCP client tests."""
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "demo_api.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(TEST_PORT),
            "--log-level",
            "warning",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Poll until the server is ready
    ready = False
    for _ in range(30):
        try:
            r = httpx.get(f"{BASE_URL}/api/status", timeout=1.0)
            if r.status_code == 200:
                ready = True
                break
        except Exception:
            time.sleep(0.1)

    if not ready:
        proc.terminate()
        raise RuntimeError("FastAPI test server failed to start within 3 seconds.")

    yield BASE_URL

    proc.terminate()
    proc.wait()


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

    # Register manual from the live endpoint
    reg_results = await client.register_manual(template)
    assert reg_results is not None

    # Discover registered tools
    tools = await client.search_tools("")
    tool_names = [t.name for t in tools]
    assert "demo_api.get_service_status" in tool_names
    assert "demo_api.get_recent_events" in tool_names

    # Invoke get_service_status
    status_res = await client.call_tool("demo_api.get_service_status", {})
    assert isinstance(status_res, dict)
    assert status_res.get("service") == "demo-api"
    assert status_res.get("status") == "healthy"
    assert status_res.get("version") == "1.0.2"
    assert status_res.get("uptime_seconds") == 86400

    # Invoke get_recent_events
    events_res = await client.call_tool("demo_api.get_recent_events", {})
    assert isinstance(events_res, dict)
    assert "events" in events_res
    assert len(events_res["events"]) == 2
    assert events_res["events"][0]["event"] == "Application restarted"

    await client.close()
