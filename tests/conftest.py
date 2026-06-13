"""Shared test fixtures: a fake Colab session whose proxy returns canned output."""
from __future__ import annotations

import pytest
from mcp.types import TextContent


class FakeClient:
    """Records the last execute_code call and returns a canned result."""

    def __init__(self, canned: str = ""):
        self.canned = canned
        self.calls: list[tuple[str, dict]] = []

    async def call_tool(self, name: str, params: dict):
        self.calls.append((name, params))
        return [TextContent(type="text", text=self.canned)]


class FakeProxyClient:
    def __init__(self, client: FakeClient):
        self._client = client

    def client_factory(self):
        return self._client


class FakeSession:
    def __init__(self, canned: str = "", connected: bool = True, session_id: str = "s1"):
        self.session_id = session_id
        self._connected = connected
        self.client = FakeClient(canned)
        self.proxy_client = FakeProxyClient(self.client)

    def is_connected(self) -> bool:
        return self._connected


@pytest.fixture
def fake_session():
    def _make(canned: str = "", connected: bool = True):
        return FakeSession(canned=canned, connected=connected)
    return _make
