"""Hermes Agent UTCP Plugin entrypoint.

Discovers tools from the live UTCP manual (``UTCP_MANUAL_URL``) and registers each one
with the Hermes runtime. Adding an endpoint to the manual is enough to expose it to the
agent; no plugin changes needed.
"""

from .discovery import discover_tools
from .tools import make_handler

TOOLSET = "demo_ops"

_TAG_EMOJI = {"status": "🔍", "health": "🔍", "events": "📋", "audit": "📋"}


def _emoji_for(tags):
    return next((_TAG_EMOJI[t] for t in tags if t in _TAG_EMOJI), "🔧")


def register(ctx):
    """Register every tool from the UTCP manual with Hermes Agent."""
    for tool in discover_tools():
        schema = {k: tool[k] for k in ("name", "description", "parameters")}
        ctx.register_tool(
            name=tool["name"],
            toolset=TOOLSET,
            schema=schema,
            handler=make_handler(tool["name"]),
            is_async=True,
            description=tool["description"],
            emoji=_emoji_for(tool["tags"]),
        )
