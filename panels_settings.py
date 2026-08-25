"""OpenText Content Server Connector -- App settings panel."""
from __future__ import annotations

from imperal_sdk import ui

import handlers_connection as h
from app import ext


@ext.panel("content_server_settings", slot="center", title="Content Server settings", icon="Settings", center_overlay=True)
async def content_server_settings(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Text("Ни один Content Server ещё не подключён.", variant="body")
    rows = []
    for c in connections:
        rows.append(ui.Stack(direction="h", gap=2, align="center", children=[
            ui.Text(f"{c.get('label') or c.get('base_url', '')}", variant="body"),
            ui.Button("Отключить", variant="destructive", on_click=ui.Call("disconnect_content_server", {"connection_id": c.get("id", "")})),
        ]))
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Подключённые инстансы", level=2),
        *rows,
    ])
