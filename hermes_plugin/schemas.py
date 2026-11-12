"""Fallback tool schemas for the hermes-utcp plugin.

Normally tools are discovered from the live UTCP manual (see ``discovery.py``).
These schemas are only used when the manual can't be fetched at plugin load time
(e.g. the demo API isn't running yet), so the agent still starts with known tools.
"""

GET_SERVICE_STATUS_SCHEMA = {
    "name": "get_service_status",
    "description": "Retrieve the current operational health, version, and uptime of the demo API service.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

GET_RECENT_EVENTS_SCHEMA = {
    "name": "get_recent_events",
    "description": "Retrieve a list of recent application events such as service restarts or configuration changes.",
    "parameters": {
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
}

FALLBACK_SCHEMAS = [GET_SERVICE_STATUS_SCHEMA, GET_RECENT_EVENTS_SCHEMA]
