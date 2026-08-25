"""Connection management for OpenText Content Server Connector."""
from __future__ import annotations

import json
import uuid

from imperal_sdk import ActionResult

import content_server_client as cs
from app import chat, ext
from schemas import (
    ConnectContentServerParams, ConnectionList, ContentServerConnection,
    DisconnectContentServerParams, NoParams,
)

_SECRET_NAME = "content_server_connections"


async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET_NAME)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


async def _save_connections(ctx, connections: list[dict]) -> None:
    await ctx.secrets.set(_SECRET_NAME, json.dumps(connections))


def _connection_entity(c: dict) -> ContentServerConnection:
    return ContentServerConnection(
        connection_id=c.get("id", ""),
        label=c.get("label") or c.get("base_url", ""),
        base_url=c.get("base_url", ""),
    )


def _client_for(c: dict) -> cs.ContentServerClient:
    return cs.ContentServerClient(
        base_url=c.get("base_url", ""),
        username=c.get("username", ""),
        password=c.get("password", ""),
    )


async def _resolve_connection(ctx, connection_id: str) -> dict:
    connections = await _load_connections(ctx)
    if not connections:
        raise cs.ContentServerError("No Content Server instance connected yet. Use connect_content_server first.")
    if connection_id:
        for c in connections:
            if c.get("id") == connection_id:
                return c
        raise cs.ContentServerError(f"No connection found with id '{connection_id}'.")
    return connections[0]


@chat.function(
    "connect_content_server",
    action_type="write",
    event="content-server-connector.connect_content_server",
    data_model=ContentServerConnection,
    description="Connect your own OpenText Content Server instance with its base URL, username, and password.",
)
async def fn_connect_content_server(ctx, params: ConnectContentServerParams) -> ActionResult:
    """Validate and save a new Content Server connection."""
    client = cs.ContentServerClient(
        base_url=params.base_url,
        username=params.username,
        password=params.password,
    )
    try:
        await client.request("GET", "/members", api_version="v1", query={"where_type": 0, "limit": 1})
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    connections = await _load_connections(ctx)
    record = {
        "id": str(uuid.uuid4()),
        "label": params.label or params.base_url,
        "base_url": params.base_url.strip().rstrip("/"),
        "username": params.username,
        "password": params.password,
    }
    connections.append(record)
    await _save_connections(ctx, connections)
    return ActionResult.success(
        data=_connection_entity(record).model_dump(),
        summary=f"Content Server instance '{record['label']}' connected.",
    )


@chat.function(
    "disconnect_content_server",
    action_type="write",
    event="content-server-connector.disconnect_content_server",
    data_model=NoParams,
    description="Disconnect a saved Content Server instance and delete its stored credentials.",
)
async def fn_disconnect_content_server(ctx, params: DisconnectContentServerParams) -> ActionResult:
    """Remove a saved Content Server connection."""
    connections = await _load_connections(ctx)
    remaining = [c for c in connections if c.get("id") != params.connection_id]
    if len(remaining) == len(connections):
        return ActionResult.error(f"No connection found with id '{params.connection_id}'.")
    await _save_connections(ctx, remaining)
    return ActionResult.success(data={}, summary="Content Server instance disconnected.")


@chat.function(
    "list_connections",
    action_type="read",
    event="content-server-connector.list_connections",
    data_model=ConnectionList,
    description="List the connected OpenText Content Server instances.",
)
async def fn_list_connections(ctx, params: NoParams) -> ActionResult:
    """List saved Content Server connections."""
    connections = await _load_connections(ctx)
    return ActionResult.success(
        data=ConnectionList(connections=[_connection_entity(c) for c in connections]).model_dump(),
        summary=f"{len(connections)} instance(s) connected.",
    )
