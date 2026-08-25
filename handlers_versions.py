"""Document version handlers for OpenText Content Server Connector."""
from __future__ import annotations

from imperal_sdk import ActionResult

import content_server_client as cs
from app import chat
from handlers_connection import _client_for, _resolve_connection
from schemas import (
    ContentServerVersion, DeleteResult, DeleteVersionParams,
    ListVersionsParams, PromoteVersionParams, VersionList,
)


@chat.function(
    "list_versions",
    action_type="read",
    event="content-server-connector.list_versions",
    data_model=VersionList,
    description="List the saved versions of a document.",
)
async def fn_list_versions(ctx, params: ListVersionsParams) -> ActionResult:
    """List saved versions of a Content Server document."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", f"/nodes/{params.node_id}/versions", api_version="v2")
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    entries = (data or {}).get("results", []) or (data or {}).get("data", [])
    versions = [
        ContentServerVersion(
            version_number=int(v.get("version_number", v.get("id", 0)) or 0),
            size_bytes=int(v.get("file_size", 0) or 0),
            modify_date=v.get("modify_date", "") or "",
            modified_by=v.get("modified_by_name", "") or "",
        )
        for v in entries
    ]
    return ActionResult.success(data=VersionList(versions=versions).model_dump(), summary=f"{len(versions)} version(s) found.")


@chat.function(
    "promote_version",
    action_type="write",
    event="content-server-connector.promote_version",
    data_model=ContentServerVersion,
    description="Promote a previous document version to be the current version.",
)
async def fn_promote_version(ctx, params: PromoteVersionParams) -> ActionResult:
    """Promote an older version of a Content Server document to current."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        await client.request(
            "POST",
            f"/nodes/{params.node_id}/versions/{params.version_number}/promote",
            api_version="v2",
        )
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(
        data=ContentServerVersion(version_number=params.version_number).model_dump(),
        summary=f"Version {params.version_number} promoted to current.",
    )


@chat.function(
    "delete_version",
    action_type="write",
    event="content-server-connector.delete_version",
    data_model=DeleteResult,
    description="Permanently delete a document version. Cannot be undone.",
)
async def fn_delete_version(ctx, params: DeleteVersionParams) -> ActionResult:
    """Delete a version of a Content Server document."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        await client.request(
            "DELETE",
            f"/nodes/{params.node_id}/versions/{params.version_number}",
            api_version="v2",
        )
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(
        data=DeleteResult(deleted=True, item_id=str(params.version_number)).model_dump(),
        summary=f"Version {params.version_number} deleted.",
    )
