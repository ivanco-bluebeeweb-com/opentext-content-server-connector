"""Permissions and member lookup handlers for OpenText Content Server Connector."""
from __future__ import annotations

from imperal_sdk import ActionResult

import content_server_client as cs
from app import chat
from handlers_connection import _client_for, _resolve_connection
from schemas import (
    ContentServerMember, ContentServerPermission, DeleteResult,
    GrantPermissionParams, ListMembersParams, ListPermissionsParams,
    MemberList, PermissionList, RevokePermissionParams,
)


@chat.function(
    "list_permissions",
    action_type="read",
    event="content-server-connector.list_permissions",
    data_model=PermissionList,
    description="List the permission grants (who can see/modify/delete) on a node.",
)
async def fn_list_permissions(ctx, params: ListPermissionsParams) -> ActionResult:
    """List permission grants on a Content Server node."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", f"/nodes/{params.node_id}/permissions", api_version="v2")
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    entries = (data or {}).get("results", []) or (data or {}).get("data", {}).get("custom_permissions", [])
    perms = [
        ContentServerPermission(
            member_id=str(p.get("right_id", "")),
            member_name=p.get("name", "") or "",
            member_type=p.get("type", "") or "",
            permissions=p.get("permissions", []) or [],
        )
        for p in entries
    ]
    return ActionResult.success(data=PermissionList(permissions=perms).model_dump(), summary=f"{len(perms)} permission grant(s) found.")


@chat.function(
    "grant_permission",
    action_type="write",
    event="content-server-connector.grant_permission",
    data_model=ContentServerPermission,
    description="Grant a user or group a set of permissions on a node.",
)
async def fn_grant_permission(ctx, params: GrantPermissionParams) -> ActionResult:
    """Grant permissions to a member on a Content Server node."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    body = {"right_id": int(params.member_id), "permissions": params.permissions}
    try:
        await client.request("POST", f"/nodes/{params.node_id}/permissions/custom", api_version="v2", json_body=body)
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(
        data=ContentServerPermission(member_id=params.member_id, permissions=params.permissions).model_dump(),
        summary="Permission granted.",
    )


@chat.function(
    "revoke_permission",
    action_type="write",
    event="content-server-connector.revoke_permission",
    data_model=DeleteResult,
    description="Revoke a member's custom permissions on a node.",
)
async def fn_revoke_permission(ctx, params: RevokePermissionParams) -> ActionResult:
    """Revoke a member's permissions on a Content Server node."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        await client.request(
            "DELETE",
            f"/nodes/{params.node_id}/permissions/custom/{params.member_id}",
            api_version="v2",
        )
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=DeleteResult(deleted=True, item_id=params.member_id).model_dump(), summary="Permission revoked.")


@chat.function(
    "list_members",
    action_type="read",
    event="content-server-connector.list_members",
    data_model=MemberList,
    description="List users and groups (members) on the connected Content Server instance, optionally filtered by name.",
)
async def fn_list_members(ctx, params: ListMembersParams) -> ActionResult:
    """List Content Server members (users/groups)."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    query = {"limit": params.limit}
    if params.query:
        query["where_name"] = params.query
    try:
        data = await client.request("GET", "/members", api_version="v2", query=query)
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    entries = (data or {}).get("results", []) or (data or {}).get("data", [])
    members = [
        ContentServerMember(
            member_id=str(m.get("id", "")),
            name=m.get("name", ""),
            member_type=str(m.get("type", "")),
        )
        for m in entries
    ]
    return ActionResult.success(data=MemberList(members=members).model_dump(), summary=f"{len(members)} member(s) found.")
