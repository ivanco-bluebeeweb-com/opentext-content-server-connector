"""Thin OpenText Content Server (OTCS) REST client.

Auth model: ticket-based session auth (POST /api/v1/auth with username+password
returns an opaque ticket sent as the OTCSTicket header on every subsequent call).
There is no refresh token -- on a 401 we transparently re-authenticate with the
stored username/password and retry once, the same resilience pattern already
used across the portfolio's client-credentials connectors (Vikunja #2356 lineage).
"""
from __future__ import annotations

from typing import Any

import httpx


class ContentServerError(RuntimeError):
    """A safe provider-facing error; never includes credentials."""

    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class ContentServerClient:
    """REST client for one OpenText Content Server instance."""

    ROOT_NODE_ID = "2000"  # Enterprise Workspace, fixed OTCS root id.

    def __init__(self, base_url: str, username: str, password: str, *, timeout: float = 30.0):
        base = (base_url or "").strip().rstrip("/")
        if not base:
            raise ContentServerError("Base URL is required.")
        if not username or not password:
            raise ContentServerError("Username and password are required.")
        self.base_url = base
        self.username = username
        self.password = password
        self.timeout = timeout
        self._ticket: str | None = None

    async def _authenticate(self) -> str:
        url = f"{self.base_url}/api/v1/auth"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(url, data={"username": self.username, "password": self.password})
            except httpx.RequestError as exc:
                raise ContentServerError(f"Could not reach Content Server: {exc}", retryable=True) from exc
        if resp.status_code == 401:
            raise ContentServerError("Invalid username or password.")
        if resp.status_code >= 400:
            raise ContentServerError(f"Content Server auth error {resp.status_code}: {resp.text[:300]}")
        try:
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            raise ContentServerError("Content Server returned an unexpected auth response.") from exc
        ticket = data.get("ticket")
        if not ticket:
            raise ContentServerError("Content Server did not return a session ticket.")
        self._ticket = ticket
        return ticket

    async def request(
        self,
        method: str,
        path: str,
        *,
        api_version: str = "v2",
        query: dict | None = None,
        json_body: dict | None = None,
        form_body: dict | None = None,
        _retried: bool = False,
    ) -> Any:
        """Make an OTCS REST request. path is relative, e.g. '/nodes/2000/nodes'."""
        if self._ticket is None:
            await self._authenticate()
        url = f"{self.base_url}/api/{api_version}{path}"
        headers = {"OTCSTicket": self._ticket or ""}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                if form_body is not None:
                    resp = await client.request(method, url, params=query, data=form_body, headers=headers)
                else:
                    resp = await client.request(method, url, params=query, json=json_body, headers=headers)
            except httpx.RequestError as exc:
                raise ContentServerError(f"Could not reach Content Server: {exc}", retryable=True) from exc
        if resp.status_code == 401 and not _retried:
            self._ticket = None
            await self._authenticate()
            return await self.request(
                method, path, api_version=api_version, query=query,
                json_body=json_body, form_body=form_body, _retried=True,
            )
        if resp.status_code == 429:
            raise ContentServerError("Rate limited by Content Server. Try again shortly.", retryable=True)
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:  # noqa: BLE001
                detail = resp.text[:300]
            raise ContentServerError(f"Content Server error {resp.status_code}: {detail}")
        if resp.status_code == 204 or not resp.content:
            return {}
        try:
            return resp.json()
        except Exception:  # noqa: BLE001
            return {}

    async def download(self, node_id: str) -> bytes:
        """Download a document node's raw content."""
        if self._ticket is None:
            await self._authenticate()
        url = f"{self.base_url}/api/v1/nodes/{node_id}/content"
        headers = {"OTCSTicket": self._ticket or ""}
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                resp = await client.get(url, headers=headers)
            except httpx.RequestError as exc:
                raise ContentServerError(f"Could not reach Content Server: {exc}", retryable=True) from exc
        if resp.status_code == 401:
            self._ticket = None
            await self._authenticate()
            headers = {"OTCSTicket": self._ticket or ""}
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
        if resp.status_code >= 400:
            raise ContentServerError(f"Content Server error {resp.status_code}: {resp.text[:300]}")
        return resp.content

    async def upload(self, name: str, parent_id: str, content: bytes) -> dict:
        """Upload a new document into a folder (multipart, v1)."""
        if self._ticket is None:
            await self._authenticate()
        url = f"{self.base_url}/api/v1/nodes"
        headers = {"OTCSTicket": self._ticket or ""}
        files = {"file": (name, content, "application/octet-stream")}
        data = {"type": "144", "parent_id": str(parent_id), "name": name}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(url, headers=headers, data=data, files=files)
            except httpx.RequestError as exc:
                raise ContentServerError(f"Could not reach Content Server: {exc}", retryable=True) from exc
        if resp.status_code >= 400:
            raise ContentServerError(f"Content Server upload error {resp.status_code}: {resp.text[:300]}")
        try:
            return resp.json()
        except Exception:  # noqa: BLE001
            return {}

    async def upload_version(self, node_id: str, content: bytes, filename: str = "") -> dict:
        """Upload a new version of an existing document (multipart, v1)."""
        if self._ticket is None:
            await self._authenticate()
        url = f"{self.base_url}/api/v1/nodes/{node_id}/versions"
        headers = {"OTCSTicket": self._ticket or ""}
        files = {"file": (filename or "version", content, "application/octet-stream")}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(url, headers=headers, files=files)
            except httpx.RequestError as exc:
                raise ContentServerError(f"Could not reach Content Server: {exc}", retryable=True) from exc
        if resp.status_code >= 400:
            raise ContentServerError(f"Content Server error {resp.status_code}: {resp.text[:300]}")
        try:
            return resp.json()
        except Exception:  # noqa: BLE001
            return {}
