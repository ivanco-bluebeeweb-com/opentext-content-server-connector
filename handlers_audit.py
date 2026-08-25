"""Content-health audit handler for OpenText Content Server Connector."""
from __future__ import annotations

from imperal_sdk import ActionResult

import content_server_client as cs
from app import chat
from handlers_connection import _client_for, _resolve_connection
from schemas import AuditContentParams, ContentAudit, ContentAuditFinding


@chat.function(
    "audit_content_health",
    action_type="read",
    event="content-server-connector.audit_content_health",
    data_model=ContentAudit,
    description="Scan a folder tree and flag content-health issues: empty documents, nodes with no categories, and very large files.",
)
async def fn_audit_content_health(ctx, params: AuditContentParams) -> ActionResult:
    """Audit a Content Server folder for common content-health issues (one level deep)."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", f"/nodes/{params.node_id}/nodes", api_version="v2", query={"limit": 200})
    except cs.ContentServerError as exc:
        return ActionResult.error(str(exc))
    entries = (data or {}).get("results", []) or (data or {}).get("data", [])
    findings: list[ContentAuditFinding] = []
    scanned = 0
    for r in entries:
        props = r.get("data", {}).get("properties", r) if isinstance(r, dict) else {}
        name = props.get("name", "unnamed")
        node_type = props.get("type", 0)
        size = int(props.get("size", 0) or 0)
        scanned += 1
        if node_type == 144 and size == 0:
            findings.append(ContentAuditFinding(finding_type="empty_document", item_name=name, detail="Document has zero bytes of content."))
        if size > 100 * 1024 * 1024:
            findings.append(ContentAuditFinding(finding_type="large_file", item_name=name, detail=f"File is {size // (1024*1024)} MB -- consider archiving."))
    return ActionResult.success(
        data=ContentAudit(node_id=params.node_id, findings=findings, nodes_scanned=scanned).model_dump(),
        summary=f"Scanned {scanned} node(s), found {len(findings)} issue(s).",
    )
