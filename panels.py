"""OpenText Content Server Connector -- left sidebar panel.

Follows the recorded UI standard: no decorated cards in the sidebar,
every input has an explicit label via _field(), the form container
stretches to the sidebar's full width with contents stretched inside
it, and no setup instructions are duplicated between the sidebar and
the "How do I connect?" overlay.
"""
from __future__ import annotations

from imperal_sdk import ui

import handlers_connection as h
from app import ext


def _field(label: str, node: ui.UINode) -> ui.UINode:
    return ui.Stack(direction="v", gap=1, align="stretch", children=[
        ui.Text(label, variant="caption"),
        node,
    ])


def _settings_button() -> ui.UINode:
    return ui.Button(
        "App settings", variant="secondary", size="sm", icon="Settings", on_click=ui.Call("__panel__content_server_settings"),
    )


@ext.panel("content_server_sidebar", slot="left", title="OpenText Content Server")
async def content_server_sidebar(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Stack(direction="v", gap=3, align="stretch", children=[
            ui.Button("Как подключить?", variant="ghost", size="sm", icon="HelpCircle",
                      on_click=ui.Call("__panel__content_server_connect_help")),
            ui.Button("Sign in with OpenText (SSO / OTDS)", variant="primary", size="sm", icon="login"),
            ui.Divider(),
            ui.Text("Or connect via Content Server Login", variant="caption"),
            ui.Form(action="connect_content_server", submit_label="Подключить", children=[
                ui.Stack(direction="v", gap=3, align="stretch", children=[
                    _field("Название (необязательно)", ui.Input(param_name="label", placeholder="например, Acme Content Server")),
                    _field("Base URL", ui.Input(param_name="base_url", placeholder="https://otcs.acme.com/otcs/cs.exe")),
                    _field("Имя пользователя", ui.Input(param_name="username", placeholder="ваш логин Content Server")),
                    _field("Пароль", ui.Password(param_name="password", placeholder="ваш пароль Content Server")),
                ]),
            ]),
        ])
    c = connections[0]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Stack(direction="v", gap=1, align="stretch", children=[
            ui.Text(c.get("label") or c.get("base_url", ""), variant="body"),
            ui.Text(c.get("base_url", ""), variant="caption"),
        ]),
        ui.Button("Обзор контента", variant="secondary", size="sm", icon="Folder",
                  on_click=ui.Call("__panel__content_server_browse")),
        ui.Button("Аудит контента", variant="secondary", size="sm", icon="ShieldCheck",
                  on_click=ui.Call("__panel__content_server_audit")),
        _settings_button(),
    ])


@ext.panel("content_server_connect_help", slot="overlay", title="Как подключить Content Server")
async def content_server_connect_help(ctx, **kwargs) -> ui.UINode:
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Text("1. Узнайте базовый URL вашего Content Server -- это адрес, по которому открывается веб-интерфейс, обычно заканчивается на /otcs/cs.exe (без /api или /llisapi.dll в конце).", variant="body"),
        ui.Text("2. Используйте свой обычный логин и пароль от Content Server -- отдельный API-ключ не нужен.", variant="body"),
        ui.Text("3. У пользователя должен быть доступ к REST API (обычно включён по умолчанию для всех пользователей веб-интерфейса).", variant="body"),
        ui.Text("4. Вставьте Base URL / имя пользователя / пароль в форму слева и подключитесь.", variant="body"),
    ])