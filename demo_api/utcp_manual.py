from typing import Any, Dict
from fastapi import APIRouter, Request
from utcp.data.utcp_manual import UtcpManual
from utcp.data.tool import Tool
from utcp_http.http_call_template import HttpCallTemplate


router = APIRouter(tags=["UTCP"])


def build_utcp_manual(base_url: str = "http://127.0.0.1:8000") -> UtcpManual:
    """Build and return the validated UTCP manual for MiniOps."""
    clean_base = base_url.rstrip("/")
    status_tool = Tool(
        name="get_service_status",
        description="Retrieve the current operational health, version, and uptime of the demo API service.",
        inputs={"type": "object", "properties": {}},
        outputs={
            "type": "object",
            "properties": {
                "service": {"type": "string", "description": "Service name"},
                "status": {"type": "string", "description": "Operational status"},
                "version": {"type": "string", "description": "Current release version"},
                "uptime_seconds": {"type": "integer", "description": "Uptime in seconds"},
            },
        },
        tags=["status", "health", "ops"],
        tool_call_template=HttpCallTemplate(
            name="get_service_status_call",
            call_template_type="http",
            http_method="GET",
            url=f"{clean_base}/api/status",
        ),
    )

    events_tool = Tool(
        name="get_recent_events",
        description="Retrieve a list of recent application events such as service restarts or configuration changes.",
        inputs={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of most recent events to return.",
                    "minimum": 1,
                }
            },
            "required": [],
        },
        outputs={
            "type": "object",
            "properties": {
                "events": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "event": {"type": "string"},
                            "time": {"type": "string"},
                        },
                    },
                }
            },
        },
        tags=["events", "audit", "ops"],
        tool_call_template=HttpCallTemplate(
            name="get_recent_events_call",
            call_template_type="http",
            http_method="GET",
            url=f"{clean_base}/api/events",
        ),
    )

    return UtcpManual(
        utcp_version="1.0.1",
        manual_version="1.0.0",
        tools=[status_tool, events_tool],
    )


@router.get("/utcp")
def get_utcp_manual(request: Request) -> Dict[str, Any]:
    """Expose the UTCP manual for client discovery."""
    base_url = str(request.base_url).rstrip("/")
    manual = build_utcp_manual(base_url=base_url)
    return manual.model_dump(exclude_none=True)
