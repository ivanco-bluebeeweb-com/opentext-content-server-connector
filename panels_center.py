"""OpenText Content Server Connector -- center panels for Browse and Content Audit."""
from __future__ import annotations

from imperal_sdk import ui

import handlers_connection as h
import handlers_nodes as hn
import handlers_audit as ha
from app import ext
from schemas import AuditContentParams, ListNodeChildrenParams


def _table_or_empty(rows, columns, empty_message, empty_icon):
    if not rows:
        return ui.Empty(message=empty_message, icon=empty_icon)
    return ui.DataTable(rows=rows, columns=columns)


@ext.panel("content_server_browse", slot="center", title="Browse", center_overlay=True)
async def content_server_browse(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="Folder")
    node_id = kwargs.get("node_id", "2000")
    result = await hn.fn_list_node_children(ctx, ListNodeChildrenParams(node_id=node_id))
    if not result.success:
        return ui.Alert(type="error", message=result.error or "Could not load node")
    nodes = (result.data or {}).get("nodes", [])
    rows = [{"name": n["name"], "node_type": n["node_type"], "size_bytes": n["size_bytes"]} for n in nodes]
    columns = [
        ui.DataColumn(key="name", label="Name"),
        ui.DataColumn(key="node_type", label="Type"),
        ui.DataColumn(key="size_bytes", label="Size (bytes)"),
    ]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Content", level=2),
        _table_or_empty(rows, columns, "This folder is empty", "Folder"),
    ])


@ext.panel("content_server_audit", slot="center", title="Content audit", center_overlay=True)
async def content_server_audit(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="ShieldCheck")
    node_id = kwargs.get("node_id", "2000")
    result = await ha.fn_audit_content_health(ctx, AuditContentParams(node_id=node_id))
    if not result.success:
        return ui.Alert(type="error", message=result.error or "Could not run audit")
    findings = (result.data or {}).get("findings", [])
    rows = [{"finding_type": f["finding_type"], "item_name": f["item_name"], "detail": f["detail"]} for f in findings]
    columns = [
        ui.DataColumn(key="finding_type", label="Type"),
        ui.DataColumn(key="item_name", label="Item"),
        ui.DataColumn(key="detail", label="Detail"),
    ]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Content audit", level=2),
        _table_or_empty(rows, columns, "No findings -- content looks healthy", "ShieldCheck"),
    ])
