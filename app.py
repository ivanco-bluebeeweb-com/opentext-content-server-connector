"""OpenText Content Server Connector extension declaration.

Content Server (OTCS) is managed via its own REST API (v1/v2, under
/otcs/cs.exe/api/*) using ticket-based session auth: POST /api/v1/auth
with username+password returns an opaque ticket sent as the OTCSTicket
header. There is no refresh token, so the connector stores the
username/password to silently re-authenticate whenever the ticket
expires (see content_server_client.py).
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "opentext-content-server-connector",
    version="0.1.0",
    display_name="OpenText Content Server",
    description=(
        "Connect your own OpenText Content Server (OTCS) instance to "
        "browse and manage Nodes (folders/documents), Versions, "
        "Permissions, Members, Categories (metadata), and run a "
        "content-health audit."
    ),
    icon="icon.svg",
    capabilities=["content-server:read", "content-server:write"],
    actions_explicit=True,
    system=False,
)

chat = ChatExtension(
    ext,
    tool_name="content_server",
    description=(
        "OpenText Content Server Connector — manage Nodes, Versions, "
        "Permissions, Members, and Categories in a connected Content "
        "Server instance."
    ),
)

ext.secret(
    "content_server_connections",
    "JSON list of connected Content Server instances and their username/password (needed to silently re-authenticate expired session tickets). Managed only through connect_content_server and disconnect_content_server.",
    required=True,
    write_mode="both",
    max_bytes=65536,
    rotation_hint_days=90,
)(lambda: None)


@ext.health_check
async def health_check(ctx) -> dict:
    """Report whether at least one Content Server connection is saved."""
    import json

    raw = await ctx.secrets.get("content_server_connections")
    connections = []
    if raw:
        try:
            connections = json.loads(raw)
        except (TypeError, ValueError):
            connections = []
    ok = bool(connections)
    return {
        "ok": ok,
        "message": (
            f"{len(connections)} Content Server instance(s) connected"
            if ok else "No Content Server instance connected yet"
        ),
    }
