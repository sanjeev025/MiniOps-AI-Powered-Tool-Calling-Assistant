import pytest
from fastapi.testclient import TestClient
from demo_api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_status_endpoint(client):
    """GET /api/status returns 200 and healthy service data."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "demo-api"
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.2"
    assert data["uptime_seconds"] == 86400


def test_events_endpoint(client):
    """GET /api/events returns 200 with recent events list."""
    response = client.get("/api/events")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert isinstance(data["events"], list)
    assert len(data["events"]) == 2
    assert data["events"][0]["event"] == "Application restarted"
    assert data["events"][0]["time"] == "10:30 AM"
    assert data["events"][1]["event"] == "Configuration updated"
    assert data["events"][1]["time"] == "11:15 AM"


def test_utcp_manual_endpoint(client):
    """GET /utcp returns a valid UTCP manual containing both operational tools."""
    response = client.get("/utcp")
    assert response.status_code == 200
    manual = response.json()
    assert manual["utcp_version"] == "1.0.1"
    assert manual["manual_version"] == "1.0.0"
    assert "tools" in manual
    assert len(manual["tools"]) == 2

    tool_names = [t["name"] for t in manual["tools"]]
    assert "get_service_status" in tool_names
    assert "get_recent_events" in tool_names

    for tool in manual["tools"]:
        assert "tool_call_template" in tool
        template = tool["tool_call_template"]
        assert template["call_template_type"] == "http"
        assert template["http_method"] == "GET"
        assert template["url"].startswith("http://")
