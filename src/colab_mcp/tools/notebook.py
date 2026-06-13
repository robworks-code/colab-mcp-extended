"""MCP tools for notebook cell management in Colab sessions."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from fastmcp.tools.tool import Tool

from colab_mcp.browser.base import NotSupportedError

if TYPE_CHECKING:
    from colab_mcp.session_manager import SessionManager


def get_notebook_tools(session_manager: SessionManager) -> list[Tool]:
    """Create notebook management tools bound to the given SessionManager."""

    async def list_cells(
        session_id: str | None = None,
    ) -> str:
        """List all cells in the current notebook.

        Args:
            session_id: Target session ID. Uses active session if not specified.

        Returns:
            JSON array of cell info objects with cell_id, type, and content preview.
        """
        session = session_manager.resolve_session(session_id)
        if not session.is_connected():
            return json.dumps({"error": f"Session {session.session_id} is not connected"})

        try:
            client = session.proxy_client.client_factory()
            result = await client.call_tool("list_cells", {})
            return json.dumps({"cells": str(result), "session_id": session.session_id})
        except Exception as e:
            return json.dumps({"error": str(e), "session_id": session.session_id})

    async def get_cell(
        cell_id: str,
        session_id: str | None = None,
    ) -> str:
        """Get the full content and output of a specific cell.

        Args:
            cell_id: The ID of the cell to retrieve.
            session_id: Target session ID. Uses active session if not specified.

        Returns:
            JSON with cell content, type, and latest output.
        """
        session = session_manager.resolve_session(session_id)
        if not session.is_connected():
            return json.dumps({"error": f"Session {session.session_id} is not connected"})

        try:
            client = session.proxy_client.client_factory()
            result = await client.call_tool("get_cell", {"cell_id": cell_id})
            return json.dumps({"cell": str(result), "session_id": session.session_id})
        except Exception as e:
            return json.dumps({"error": str(e), "session_id": session.session_id})

    async def add_cell(
        cell_type: str = "code",
        content: str = "",
        after_cell_id: str | None = None,
        session_id: str | None = None,
    ) -> str:
        """Add a new cell to the notebook.

        Args:
            cell_type: Type of cell - "code" or "markdown". Defaults to "code".
            content: Initial content for the cell.
            after_cell_id: Insert after this cell. If None, appends to end.
            session_id: Target session ID. Uses active session if not specified.

        Returns:
            JSON with the new cell's ID.
        """
        session = session_manager.resolve_session(session_id)
        if not session.is_connected():
            return json.dumps({"error": f"Session {session.session_id} is not connected"})

        try:
            client = session.proxy_client.client_factory()
            params = {"cell_type": cell_type, "content": content}
            if after_cell_id:
                params["after_cell_id"] = after_cell_id
            result = await client.call_tool("add_cell", params)
            return json.dumps({"result": str(result), "session_id": session.session_id})
        except Exception as e:
            return json.dumps({"error": str(e), "session_id": session.session_id})

    async def edit_cell(
        cell_id: str,
        content: str,
        session_id: str | None = None,
    ) -> str:
        """Edit the content of an existing cell.

        Args:
            cell_id: The ID of the cell to edit.
            content: New content for the cell.
            session_id: Target session ID. Uses active session if not specified.

        Returns:
            Confirmation message.
        """
        session = session_manager.resolve_session(session_id)
        if not session.is_connected():
            return json.dumps({"error": f"Session {session.session_id} is not connected"})

        try:
            client = session.proxy_client.client_factory()
            result = await client.call_tool(
                "edit_cell", {"cell_id": cell_id, "content": content}
            )
            return json.dumps({"result": str(result), "session_id": session.session_id})
        except Exception as e:
            return json.dumps({"error": str(e), "session_id": session.session_id})

    async def delete_cell(
        cell_id: str,
        session_id: str | None = None,
    ) -> str:
        """Delete a cell from the notebook.

        Args:
            cell_id: The ID of the cell to delete.
            session_id: Target session ID. Uses active session if not specified.

        Returns:
            Confirmation message.
        """
        session = session_manager.resolve_session(session_id)
        if not session.is_connected():
            return json.dumps({"error": f"Session {session.session_id} is not connected"})

        try:
            client = session.proxy_client.client_factory()
            result = await client.call_tool("delete_cell", {"cell_id": cell_id})
            return json.dumps({"result": str(result), "session_id": session.session_id})
        except Exception as e:
            return json.dumps({"error": str(e), "session_id": session.session_id})

    async def change_runtime_type(accelerator: str = "T4 GPU",
                                  session_id: str | None = None) -> str:
        """Change the runtime hardware accelerator (CPU / T4 GPU / A100 / TPU).

        Requires a headless/Playwright session.

        Args:
            accelerator: Accelerator label as shown in Colab (e.g. 'T4 GPU').
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON with change status or {error}.
        """
        session = session_manager.resolve_session(session_id)
        if not session.is_connected():
            return json.dumps({"error": f"Session {session.session_id} is not connected"})
        try:
            return json.dumps(await session.backend.change_runtime_type(accelerator))
        except NotSupportedError as e:
            return json.dumps({"error": str(e)})

    async def connect_runtime(session_id: str | None = None) -> str:
        """Click Connect to attach a compute runtime. Requires Playwright session.

        Args:
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON with connect status or {error}.
        """
        session = session_manager.resolve_session(session_id)
        if not session.is_connected():
            return json.dumps({"error": f"Session {session.session_id} is not connected"})
        try:
            return json.dumps(await session.backend.connect_runtime())
        except NotSupportedError as e:
            return json.dumps({"error": str(e)})

    async def factory_reset_runtime(session_id: str | None = None) -> str:
        """Disconnect and delete the runtime (factory reset). Requires Playwright.

        Args:
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON with reset status or {error}.
        """
        session = session_manager.resolve_session(session_id)
        if not session.is_connected():
            return json.dumps({"error": f"Session {session.session_id} is not connected"})
        try:
            return json.dumps(await session.backend.factory_reset_runtime())
        except NotSupportedError as e:
            return json.dumps({"error": str(e)})

    async def save_notebook(session_id: str | None = None) -> str:
        """Save the notebook (Ctrl/Cmd+S). Requires Playwright session.

        Args:
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON with save status or {error}.
        """
        session = session_manager.resolve_session(session_id)
        if not session.is_connected():
            return json.dumps({"error": f"Session {session.session_id} is not connected"})
        try:
            return json.dumps(await session.backend.save_notebook())
        except NotSupportedError as e:
            return json.dumps({"error": str(e)})

    async def complete_drive_mount_consent(session_id: str | None = None) -> str:
        """Click through the Drive mount consent popup. Requires Playwright session.

        Use after mount_drive returns needs_consent=True.

        Args:
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON with consent status or {error}.
        """
        session = session_manager.resolve_session(session_id)
        if not session.is_connected():
            return json.dumps({"error": f"Session {session.session_id} is not connected"})
        try:
            return json.dumps(await session.backend.complete_drive_mount_consent())
        except NotSupportedError as e:
            return json.dumps({"error": str(e)})

    return [
        Tool.from_function(
            fn=list_cells,
            name="list_cells",
            description="List all cells in the current Colab notebook with their IDs and content previews.",
        ),
        Tool.from_function(
            fn=get_cell,
            name="get_cell",
            description="Get the full content and output of a specific notebook cell.",
        ),
        Tool.from_function(
            fn=add_cell,
            name="add_cell",
            description="Add a new code or markdown cell to the Colab notebook.",
        ),
        Tool.from_function(
            fn=edit_cell,
            name="edit_cell",
            description="Edit the content of an existing notebook cell.",
        ),
        Tool.from_function(
            fn=delete_cell,
            name="delete_cell",
            description="Delete a cell from the Colab notebook.",
        ),
        Tool.from_function(fn=change_runtime_type, name="change_runtime_type",
                           description="Change the runtime hardware accelerator (CPU/GPU/TPU)."),
        Tool.from_function(fn=connect_runtime, name="connect_runtime",
                           description="Click Connect to attach a compute runtime."),
        Tool.from_function(fn=factory_reset_runtime, name="factory_reset_runtime",
                           description="Disconnect and delete the runtime (factory reset)."),
        Tool.from_function(fn=save_notebook, name="save_notebook",
                           description="Save the notebook."),
        Tool.from_function(fn=complete_drive_mount_consent, name="complete_drive_mount_consent",
                           description="Click through the Drive mount consent popup."),
    ]
