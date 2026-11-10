"""Hermes Agent UTCP Plugin entrypoint.

Registers custom operational tools (get_service_status, get_recent_events)
with the Hermes runtime context.
"""

from .schemas import GET_SERVICE_STATUS_SCHEMA, GET_RECENT_EVENTS_SCHEMA
from .tools import handle_get_service_status, handle_get_recent_events


def register(ctx):
    """Register UTCP operational tools with Hermes Agent."""
    ctx.register_tool(
        name="get_service_status",
        toolset="demo_ops",
        schema=GET_SERVICE_STATUS_SCHEMA,
        handler=handle_get_service_status,
        is_async=True,
        description="Retrieve the current operational health, version, and uptime of the demo API service.",
        emoji="🔍",
    )

    ctx.register_tool(
        name="get_recent_events",
        toolset="demo_ops",
        schema=GET_RECENT_EVENTS_SCHEMA,
        handler=handle_get_recent_events,
        is_async=True,
        description="Retrieve a list of recent application events such as service restarts or configuration updates.",
        emoji="📋",
    )
