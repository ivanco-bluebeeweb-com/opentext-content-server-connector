# OpenText Content Server Connector -- Ideal Onboarding

## Goal
Get a user from "I have an OpenText Content Server instance" to "Webbee can browse/manage
my content" in under two minutes, with zero surprises.

## Step 1 -- What the user needs before connecting
- Their Content Server base URL, e.g. `https://otcs.acme.com/otcs/cs.exe` (the connector
  appends `/api/v1` / `/api/v2` itself -- user pastes the root URL only).
- A username + password with REST API access (same credentials as the Content Server web UI).
  No API key, no OAuth app registration needed -- this is what makes OTCS onboarding fast
  compared to SharePoint/Box.

## Step 2 -- Connecting (chat or sidebar form)
`connect_content_server(base_url, username, password, label?)`:
1. Connector calls `POST {base_url}/api/v1/auth` with the credentials.
2. On success, stores `base_url` + `username` + `password` (password needed to silently
   re-authenticate when the session ticket expires -- there is no refresh token in OTCS).
3. Confirms by reading `GET /api/v1/members?where_type=0&limit=1` (or the ticket's own user
   info) to prove the ticket actually works end-to-end, not just that auth returned 200.
4. Friendly label defaults to the base_url host if the user leaves it blank.

## Step 3 -- First 60 seconds after connecting
Sidebar surfaces immediately:
- A **Browse** shortcut into the root Enterprise Workspace (node 2000, OTCS's fixed root ID)
  so the user sees their content tree without needing to know any node IDs.
- An **Audit** shortcut (`audit_content_health`) as a one-click "how healthy is my content
  server" report -- same value-add pattern as Box/SharePoint.

## Step 4 -- What could go wrong (and how the connector handles it)
- **Wrong base_url (missing /cs.exe or trailing api segment)**: auth call 404s;
  connector surfaces a plain "Could not reach Content Server at this URL -- check it ends
  where the Content Server web UI itself lives (e.g. .../otcs/cs.exe)."
- **Ticket expiry mid-session**: any call returning 401 triggers one silent re-auth attempt
  with the stored credentials before the error is ever shown to the user.
- **Records Management module not licensed**: retention/classification calls are out of
  scope for v1 entirely, so users on a Content Server without RM never hit a dead end.
- **Permission-denied on write actions**: OTCS returns 403 with a body explaining which
  right is missing (e.g. "WriteMissing") -- surfaced verbatim, since it is actionable
  (the user knows to ask their OTCS admin for that specific permission).

## Non-goals for v1
- Records Management (retention schedules, legal holds) -- license-gated, most tenants don't
  have it; add later if requested.
- Physical Objects / Records Management Classifications -- same reasoning.
- Full workflow *design* (creating new workflow maps) -- only running/approving existing
  workflow instances is in scope.
