"""OpenAI-compatible tool schemas exposed by the hermes-utcp plugin."""

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
    "description": "Retrieve a list of recent application events such as service restarts or configuration updates.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}
