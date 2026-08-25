"""Document content handlers (upload/download/new version/search) for OpenText Content Server Connector."""
from __future__ import annotations

import base64

from imperal_sdk import ActionResult

import content_server_client as cs
from app import chat
from handlers_connection import _client_for, _resolve_connection
from handlers_nodes import _node_entity
from schemas import (
    ContentServerNode, DownloadDocumentParams, DownloadResult, NodeList,
    SearchNodesParams, UploadDocumentParams, UploadResult, UploadVersionParams,
)


@chat.function(
    "download_document",
    action_type="read",
    event="content-server-connector.download_document",
    data_model=DownloadResult,
    description="Download a document's content, base64-encoded.",
)
async def fn_download_document(ctx, params: DownloadDocumentParams) -> ActionResult:
    """Download a Content Server document's raw content."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        meta = await client.request("GET", f"/nodes/{params.node_id}")
        content = await client.download(params.node_id)
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    node = (meta or {}).get("results", {}).get("data", {}).get("properties", meta.get("data", meta))
    name = node.get("name", "") if isinstance(node, dict) else ""
    return ActionResult.success(
        data=DownloadResult(name=name, content_base64=base64.b64encode(content).decode()).model_dump(),
        summary=f"Downloaded '{name}' ({len(content)} bytes).",
    )


@chat.function(
    "upload_document",
    action_type="write",
    event="content-server-connector.upload_document",
    data_model=UploadResult,
    description="Upload a new document (base64-encoded content) into a folder.",
)
async def fn_upload_document(ctx, params: UploadDocumentParams) -> ActionResult:
    """Upload a new document into a Content Server folder."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        raw = base64.b64decode(params.content_base64)
    except Exception:
        return ActionResult.error("content_base64 is not valid base64.")
    try:
        data = await client.upload(params.name, params.parent_id, raw)
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    node_id = str((data or {}).get("results", {}).get("data", {}).get("properties", {}).get("id", "")) or str((data or {}).get("id", ""))
    return ActionResult.success(
        data=UploadResult(node_id=node_id, name=params.name).model_dump(),
        summary=f"'{params.name}' uploaded.",
    )


@chat.function(
    "upload_document_version",
    action_type="write",
    event="content-server-connector.upload_document_version",
    data_model=UploadResult,
    description="Upload a new version of an existing document.",
)
async def fn_upload_document_version(ctx, params: UploadVersionParams) -> ActionResult:
    """Upload a new version of an existing Content Server document."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        raw = base64.b64decode(params.content_base64)
    except Exception:
        return ActionResult.error("content_base64 is not valid base64.")
    try:
        await client.upload_version(params.node_id, raw, filename=params.filename)
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(
        data=UploadResult(node_id=params.node_id, name=params.filename or params.node_id).model_dump(),
        summary="New version uploaded.",
    )


@chat.function(
    "search_nodes",
    action_type="read",
    event="content-server-connector.search_nodes",
    data_model=NodeList,
    description="Search for nodes (folders and documents) by free-text query.",
)
async def fn_search_nodes(ctx, params: SearchNodesParams) -> ActionResult:
    """Search Content Server nodes by free-text query."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", "/search", api_version="v2", query={"where": params.query, "limit": params.limit})
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    results = (data or {}).get("results", [])
    nodes = [_node_entity(r.get("data", {}).get("properties", r)) for r in results]
    return ActionResult.success(data=NodeList(nodes=nodes).model_dump(), summary=f"{len(nodes)} result(s) found.")
