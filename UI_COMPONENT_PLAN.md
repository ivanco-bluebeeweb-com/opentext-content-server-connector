# OpenText Content Server Connector -- UI Component Plan

Follows the recorded platform-wide UI standard (see WEBBEE.md / SharePoint & Box
UI_COMPONENT_PLAN.md): every input has an explicit label above it via a `_field()`
wrapper, placeholders are contextual (never generic "enter value"), the sidebar form
container is forced to the full width of the left sidebar with its contents stretched
inside it, `ui.Input`/`ui.Password` use `param_name=` (not `name=`), `ui.Button` never
uses `type="submit"`, and setup instructions live ONLY in the "How do I connect?" overlay
-- never duplicated in the sidebar itself.

## Sidebar (`panels.py`, slot="left")
Not connected:
- One ghost button: "Как подключить?" -> opens `content_server_connect_help` overlay
  (all instructions -- base_url shape, credentials needed -- live there, not in the sidebar).
- `ui.Form(action="connect_content_server", submit_label="Подключить")` containing a
  `ui.Stack` (full width, gap=3) with:
  - _field("Название (необязательно)", Input(param_name="label", placeholder="например, Acme OTCS"))
  - _field("Base URL", Input(param_name="base_url", placeholder="https://otcs.acme.com/otcs/cs.exe"))
  - _field("Имя пользователя", Input(param_name="username", placeholder="ваш логин Content Server"))
  - _field("Пароль", Password(param_name="password", placeholder="ваш пароль Content Server"))

Connected:
- "App settings" secondary button -> `content_server_settings` overlay.
- Quick actions: "Browse" -> `content_server_browse` overlay (root Enterprise Workspace),
  "Content audit" -> `content_server_audit` overlay.

## Center overlays (`panels_center.py`)
- `content_server_browse`: DataTable of node children (name, type, id) for a given
  `node_id` (default 2000, the fixed Enterprise Workspace root); ui.Empty when folder empty.
- `content_server_audit`: renders `audit_content_health` findings as a DataTable
  (finding_type, item_name, detail); ui.Empty when no findings.

## Settings overlay (`panels_settings.py`)
- List of connected instances (label + base_url host) each with a "Отключить"
  destructive button calling `disconnect_content_server`.

## Connect-help overlay (`panels.py`, separate panel fn)
- Explains: get your Content Server base URL from your browser's address bar while in
  the CS web UI (strip anything after `/cs.exe`); use the same username/password you use
  to log into that web UI; no admin API key or OAuth app registration needed.
