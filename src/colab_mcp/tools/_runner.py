"""Shared helpers for execute_code-composed tools."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from mcp.types import TextContent

if TYPE_CHECKING:
    from colab_mcp.session import ColabSession

OUTPUT_START = "___COLAB_MCP_OUTPUT_START___"
OUTPUT_END = "___COLAB_MCP_OUTPUT_END___"


def extract_text(result) -> str:
    """Flatten an MCP tool result into plain text."""
    if isinstance(result, list):
        return "".join(c.text for c in result if isinstance(c, TextContent))
    return str(result)


def extract_delimited(raw: str) -> str:
    """Return the payload between output markers, ignoring surrounding kernel noise."""
    start = raw.find(OUTPUT_START)
    end = raw.find(OUTPUT_END)
    if start != -1 and end != -1:
        return raw[start + len(OUTPUT_START):end].strip()
    return raw.strip()


def wrap_output(body: str) -> str:
    """Wrap a code body so its delimited region is isolatable.

    `body` must itself print the JSON payload. This adds the delimiter prints
    around it on their own lines.
    """
    return (
        f'print("{OUTPUT_START}")\n'
        f"{body}\n"
        f'print("{OUTPUT_END}")\n'
    )


async def run_python(session, code: str) -> dict:
    """Execute generated Python in the session kernel and parse delimited JSON.

    Returns the parsed dict, or {"error": ...} if not connected / parse fails.
    """
    if not session.is_connected():
        return {"error": f"Session {session.session_id} is not connected",
                "session_id": session.session_id}
    try:
        client = session.proxy_client.client_factory()
        result = await client.call_tool("execute_code", {"code": code})
        payload = extract_delimited(extract_text(result))
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return {"raw": payload, "session_id": session.session_id}
    except Exception as e:  # noqa: BLE001 - surface any kernel/transport error
        return {"error": str(e), "session_id": session.session_id}
