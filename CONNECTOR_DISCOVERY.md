# OpenText Content Server Connector -- Discovery

## Product
OpenText Content Server (OTCS) -- enterprise ECM platform (on-prem or OpenText Cloud).
REST API: `/otcs/cs.exe/api/v1` and `/api/v2` (v2 adds richer categories/permissions/workflow
endpoints; v1 remains for auth, nodes, versions, members).

## Auth model
Ticket-based session auth (not OAuth2):
1. `POST {base_url}/api/v1/auth` with form-encoded `username` + `password`.
2. Response: `{"ticket": "<opaque-string>"}`.
3. Every subsequent call sends header `OTCSTicket: <ticket>`.
4. Tickets expire (default ~2 hours idle, configurable server-side) -- no refresh endpoint;
   just re-authenticate with the stored username/password when a call returns 401.
   This matches the token-cache-with-reauth-on-401 pattern already used in Splunk/Box/SharePoint
   connectors (Vikunja #2356 lineage): cache the ticket in memory per BoxClient-equivalent
   instance, re-mint transparently on 401.

Stored per connection: `base_url`, `username`, `password` (password is required to
re-authenticate on ticket expiry -- OTCS has no refresh-token concept). This mirrors how
Jira/Zendesk-style Basic-Auth-style connectors store credentials directly (no separate
"long-lived token" issued by OTCS itself for REST use outside of OAuth-enabled Cloud tenants).

## Core resources (v1/v2)
- **Nodes** -- the universal object model: every folder, document, compound doc, etc. is a
  "node" with a numeric `id`, `type` (0=folder, 144=document, ...), `parent_id`.
  `GET /v2/nodes/{id}`, `GET /v2/nodes/{id}/nodes` (children), `POST /v2/nodes` (create folder),
  `PUT /v2/nodes/{id}` (rename/move), `DELETE /v2/nodes/{id}`.
- **Document content** -- `GET /v1/nodes/{id}/content` (download), `POST /v1/nodes` multipart
  (create document with file), `PUT /v1/nodes/{id}/versions` multipart (new version).
- **Versions** -- `GET /v2/nodes/{id}/versions`, `GET /v2/nodes/{id}/versions/{version}`,
  `POST .../versions/{version}/promote` (~ no true "promote"; OTCS keeps version history
  linearly -- "promote" here means fetching a prior version's content and re-uploading as new).
- **Search** -- `GET /v2/search?where=...` (OTCS query syntax) or simple `where_name` param.
- **Permissions** -- `GET /v2/nodes/{id}/permissions`, `POST/PUT .../permissions/custom`
  (assign a right_id to a member with allow/deny bit flags: see, see_contents, modify, delete...).
- **Categories (metadata)** -- OTCS's metadata-template equivalent. `GET /v2/nodes/{id}/categories`,
  `POST /v2/nodes/{id}/categories/{category_id}` to attach + set attribute values.
- **Members (users/groups)** -- `GET /v2/members?where_type=0` (users) / `where_type=1` (groups),
  used to resolve names to `right_id` for permission grants.
- **Workflows** -- `GET /v2/workflows`, `POST /v2/workflows/{id}/actions` (start/approve/reject
  a step) -- OTCS workflow maps document lifecycle approvals.
- **Records Management (if module licensed)** -- retention/classification; out of scope for v1
  of this connector (advanced module, license-gated -- would 403 for most tenants).

## Design decisions for this connector
- Ticket auth client mirrors Box's client-credentials pattern: mint on first call, cache,
  auto-remint on 401, never leak ticket/password in errors.
- Node-centric verbs (folders are just nodes of type 0) -- keep folder and document handlers
  separate for chat ergonomics even though OTCS models them identically.
- Content-health audit modeled after Box/SharePoint precedent: flag documents with no version
  history beyond original, folders with excessive size, permissions granted to "Public Access".
