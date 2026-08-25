"""Category (metadata template) handlers for OpenText Content Server Connector."""
from __future__ import annotations

import json

from imperal_sdk import ActionResult

import content_server_client as cs
from app import chat
from handlers_connection import _client_for, _resolve_connection
from schemas import (
    CategoryList, CategoryValues, ContentServerCategory, GetCategoryParams,
    ListCategoriesParams, SetCategoryValuesParams,
)


@chat.function(
    "list_categories",
    action_type="read",
    event="content-server-connector.list_categories",
    data_model=CategoryList,
    description="List metadata categories (templates) attached to a node.",
)
async def fn_list_categories(ctx, params: ListCategoriesParams) -> ActionResult:
    """List metadata categories attached to a Content Server node."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", f"/nodes/{params.node_id}/categories", api_version="v2")
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    entries = (data or {}).get("results", []) or (data or {}).get("data", [])
    cats = [
        ContentServerCategory(category_id=str(c.get("id", "")), name=c.get("name", ""))
        for c in entries
    ]
    return ActionResult.success(data=CategoryList(categories=cats).model_dump(), summary=f"{len(cats)} categor(y/ies) found.")


@chat.function(
    "get_category_values",
    action_type="read",
    event="content-server-connector.get_category_values",
    data_model=CategoryValues,
    description="Read a metadata category's current attribute values on a node.",
)
async def fn_get_category_values(ctx, params: GetCategoryParams) -> ActionResult:
    """Read a category's attribute values on a Content Server node."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request(
            "GET",
            f"/nodes/{params.node_id}/categories/{params.category_id}",
            api_version="v2",
        )
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    values = (data or {}).get("results", {}).get("data", data.get("data", {})) or {}
    return ActionResult.success(
        data=CategoryValues(category_id=params.category_id, values=values).model_dump(),
        summary="Category values loaded.",
    )


@chat.function(
    "set_category_values",
    action_type="write",
    event="content-server-connector.set_category_values",
    data_model=CategoryValues,
    description="Set metadata category attribute values on a node.",
)
async def fn_set_category_values(ctx, params: SetCategoryValuesParams) -> ActionResult:
    """Set a category's attribute values on a Content Server node."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        values = json.loads(params.values_json)
    except (TypeError, ValueError):
        return ActionResult.error("values_json is not valid JSON.")
    body = {"category_id": int(params.category_id), **values}
    try:
        await client.request(
            "PUT",
            f"/nodes/{params.node_id}/categories/{params.category_id}",
            api_version="v2",
            form_body={"body": json.dumps(body)},
        )
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(
        data=CategoryValues(category_id=params.category_id, values=values).model_dump(),
        summary="Category values updated.",
    )
