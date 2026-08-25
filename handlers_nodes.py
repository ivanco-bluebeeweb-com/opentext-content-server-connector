"""Node (folder/document listing) handlers for OpenText Content Server Connector."""
from __future__ import annotations

from imperal_sdk import ActionResult

import content_server_client as cs
from app import chat
from handlers_connection import _client_for, _resolve_connection
from schemas import (
    ContentServerNode, CreateFolderParams, DeleteNodeParams, DeleteResult,
    ListNodeChildrenParams, NodeIdParams, NodeList, RenameOrMoveNodeParams,
)


def _node_entity(n: dict) -> ContentServerNode:
    return ContentServerNode(
        node_id=str(n.get("id", "")),
        name=n.get("name", ""),
        node_type=str(n.get("type_name", n.get("type", ""))),
        parent_id=str(n.get("parent_id", "")) if n.get("parent_id") is not None else "",
        size_bytes=int(n.get("size", 0) or 0),
        modify_date=n.get("modify_date", "") or "",
    )


@chat.function(
    "get_node",
    action_type="read",
    event="content-server-connector.get_node",
    data_model=ContentServerNode,
    description="Read one Content Server node's (folder or document) metadata in full.",
)
async def fn_get_node(ctx, params: NodeIdParams) -> ActionResult:
    """Read one Content Server node's metadata."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", f"/nodes/{params.node_id}")
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    node = (data or {}).get("results", {}).get("data", {}).get("properties", data.get("data", data))
    return ActionResult.success(data=_node_entity(node).model_dump(), summary=f"Node '{node.get('name', '')}' loaded.")


@chat.function(
    "list_node_children",
    action_type="read",
    event="content-server-connector.list_node_children",
    data_model=NodeList,
    description="List files and subfolders directly inside a Content Server node (folder).",
)
async def fn_list_node_children(ctx, params: ListNodeChildrenParams) -> ActionResult:
    """List the contents of a Content Server folder node."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", f"/nodes/{params.node_id}/nodes", query={"limit": params.limit})
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    entries = (data or {}).get("results", [])
    nodes = [_node_entity(e.get("data", {}).get("properties", e)) for e in entries]
    return ActionResult.success(data=NodeList(nodes=nodes).model_dump(), summary=f"{len(nodes)} item(s) found.")


@chat.function(
    "create_folder",
    action_type="write",
    event="content-server-connector.create_folder",
    data_model=ContentServerNode,
    description="Create a new folder inside a parent node.",
)
async def fn_create_folder(ctx, params: CreateFolderParams) -> ActionResult:
    """Create a new Content Server folder."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    body = {"type": "0", "parent_id": params.parent_id, "name": params.name}
    try:
        data = await client.request("POST", "/nodes", api_version="v1", form_body=body)
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    node = (data or {}).get("results", {}).get("data", {}).get("properties", data)
    return ActionResult.success(data=_node_entity(node).model_dump(), summary=f"Folder '{params.name}' created.")


@chat.function(
    "rename_or_move_node",
    action_type="write",
    event="content-server-connector.rename_or_move_node",
    data_model=ContentServerNode,
    description="Rename a node and/or move it to a different parent folder.",
)
async def fn_rename_or_move_node(ctx, params: RenameOrMoveNodeParams) -> ActionResult:
    """Rename and/or move a Content Server node."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    body: dict = {}
    if params.name:
        body["name"] = params.name
    if params.new_parent_id:
        body["parent_id"] = params.new_parent_id
    if not body:
        return ActionResult.error("Provide at least one of name or new_parent_id.")
    try:
        data = await client.request("PUT", f"/nodes/{params.node_id}", api_version="v1", form_body=body)
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    node = (data or {}).get("results", {}).get("data", {}).get("properties", data)
    return ActionResult.success(data=_node_entity(node).model_dump(), summary="Node updated.")


@chat.function(
    "delete_node",
    action_type="write",
    event="content-server-connector.delete_node",
    data_model=DeleteResult,
    description="Permanently delete a node (folder or document). Cannot be undone.",
)
async def fn_delete_node(ctx, params: DeleteNodeParams) -> ActionResult:
    """Delete a Content Server node."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        await client.request("DELETE", f"/nodes/{params.node_id}")
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=DeleteResult(deleted=True, item_id=params.node_id).model_dump(), summary="Node deleted.")
