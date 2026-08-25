"""Pydantic input contracts and SDL result entities for OpenText Content Server Connector."""
from __future__ import annotations

from imperal_sdk import sdl
from pydantic import BaseModel, Field


class NoParams(BaseModel):
    pass


class ConnectionRefParams(BaseModel):
    connection_id: str = Field("", description="Optional saved Content Server connection ID. Omit to use the first connected instance.")


class ConnectContentServerParams(BaseModel):
    label: str = Field("", description="Friendly instance label, e.g. 'Acme Content Server'.")
    base_url: str = Field(..., description="Content Server base URL, e.g. 'https://otcs.acme.com/otcs/cs.exe'.")
    username: str = Field(..., description="Content Server username with REST API access.")
    password: str = Field(..., description="Content Server password for that username.")


class DisconnectContentServerParams(ConnectionRefParams):
    connection_id: str = Field(..., description="Saved Content Server connection ID to remove from Imperal.")


class NodeIdParams(ConnectionRefParams):
    node_id: str = Field("2000", description="Content Server node ID. Use '2000' for the Enterprise Workspace root.")


class ListNodeChildrenParams(NodeIdParams):
    limit: int = Field(100, description="Max child nodes to return (1-500).")


class CreateFolderParams(ConnectionRefParams):
    name: str = Field(..., description="New folder name, e.g. 'Q3 Contracts'.")
    parent_id: str = Field("2000", description="Parent node ID to create the folder inside. Use '2000' for root.")


class RenameOrMoveNodeParams(NodeIdParams):
    name: str = Field("", description="New node name. Leave blank to keep the current name.")
    new_parent_id: str = Field("", description="Destination parent node ID to move into. Leave blank to keep in place.")


class DeleteNodeParams(NodeIdParams):
    pass


class UploadDocumentParams(ConnectionRefParams):
    parent_id: str = Field("2000", description="Folder node ID to upload into. Use '2000' for root.")
    name: str = Field(..., description="Document name to save as, e.g. 'contract.pdf'.")
    content_base64: str = Field(..., description="Base64-encoded file content.")


class DownloadDocumentParams(NodeIdParams):
    pass


class UploadVersionParams(NodeIdParams):
    filename: str = Field("", description="Optional filename for this new version. Leave blank to keep the document's current name.")
    content_base64: str = Field(..., description="Base64-encoded new version content.")


class SearchNodesParams(ConnectionRefParams):
    query: str = Field(..., description="Free-text search query, e.g. 'quarterly report'.")
    limit: int = Field(30, description="Max results to return (1-200).")


class ListVersionsParams(NodeIdParams):
    pass


class PromoteVersionParams(NodeIdParams):
    version_number: int = Field(..., description="Version number to promote to current, from list_versions.")


class DeleteVersionParams(NodeIdParams):
    version_number: int = Field(..., description="Version number to delete, from list_versions.")


class ListPermissionsParams(NodeIdParams):
    pass


class GrantPermissionParams(NodeIdParams):
    member_id: str = Field(..., description="User or group ID to grant access to, from list_members.")
    permissions: list[str] = Field(default_factory=lambda: ["see", "see_contents"], description="Permission flags to grant, e.g. ['see', 'see_contents', 'modify', 'delete'].")


class RevokePermissionParams(NodeIdParams):
    member_id: str = Field(..., description="User or group ID to revoke access from.")


class ListMembersParams(ConnectionRefParams):
    query: str = Field("", description="Optional name filter, e.g. 'jane'.")
    limit: int = Field(50, description="Max members to return (1-200).")


class ListCategoriesParams(NodeIdParams):
    pass


class GetCategoryParams(NodeIdParams):
    category_id: str = Field(..., description="Category (metadata template) ID, from list_categories.")


class SetCategoryValuesParams(GetCategoryParams):
    values_json: str = Field(..., description="JSON object of attribute-name to value pairs matching the category's schema, e.g. '{\"Status\": \"Approved\"}'.")


class AuditContentParams(ConnectionRefParams):
    node_id: str = Field("2000", description="Node ID to audit. Use '2000' for the Enterprise Workspace root.")


# ---- SDL result entities ----

class DeleteResult(sdl.Entity):
    deleted: bool
    item_id: str = ""


class ContentServerConnection(sdl.Entity):
    connection_id: str
    label: str
    base_url: str


class ConnectionList(sdl.Entity):
    connections: list[ContentServerConnection]


class ContentServerNode(sdl.Entity):
    node_id: str
    name: str
    node_type: str = ""
    parent_id: str = ""
    size_bytes: int = 0
    modify_date: str = ""


class NodeList(sdl.Entity):
    nodes: list[ContentServerNode]


class UploadResult(sdl.Entity):
    node_id: str
    name: str


class DownloadResult(sdl.Entity):
    name: str
    content_base64: str
    content_type: str = "application/octet-stream"


class ContentServerVersion(sdl.Entity):
    version_number: int
    size_bytes: int = 0
    modify_date: str = ""
    modified_by: str = ""


class VersionList(sdl.Entity):
    versions: list[ContentServerVersion]


class ContentServerPermission(sdl.Entity):
    member_id: str
    member_name: str = ""
    member_type: str = ""
    permissions: list[str]


class PermissionList(sdl.Entity):
    permissions: list[ContentServerPermission]


class ContentServerMember(sdl.Entity):
    member_id: str
    name: str
    member_type: str = ""


class MemberList(sdl.Entity):
    members: list[ContentServerMember]


class ContentServerCategory(sdl.Entity):
    category_id: str
    name: str


class CategoryList(sdl.Entity):
    categories: list[ContentServerCategory]


class CategoryValues(sdl.Entity):
    category_id: str
    values: dict


class ContentAuditFinding(sdl.Entity):
    finding_type: str
    item_name: str
    detail: str


class ContentAudit(sdl.Entity):
    node_id: str
    findings: list[ContentAuditFinding]
    nodes_scanned: int = 0
