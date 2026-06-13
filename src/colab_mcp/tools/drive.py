"""Google Drive mount and browse tools."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from fastmcp.tools.tool import Tool

from colab_mcp.tools._runner import run_python, wrap_output

if TYPE_CHECKING:
    from colab_mcp.session_manager import SessionManager


def _gen_mount_code(mount_point: str) -> str:
    body = (
        "import json\n"
        "from google.colab import drive\n"
        "try:\n"
        f"    drive.mount({mount_point!r}, force_remount=False)\n"
        f"    print(json.dumps({{'mounted': True, 'mount_point': {mount_point!r}}}))\n"
        "except Exception as e:\n"
        "    print(json.dumps({'mounted': False, 'needs_consent': True, 'error': str(e)}))\n"
    )
    return wrap_output(body)


def _gen_unmount_code() -> str:
    body = (
        "import json\n"
        "from google.colab import drive\n"
        "drive.flush_and_unmount()\n"
        "print(json.dumps({'unmounted': True}))\n"
    )
    return wrap_output(body)


def _gen_list_drive_code(path: str) -> str:
    body = (
        "import json, os\n"
        f"p = {path!r}\n"
        "if not os.path.exists(p):\n"
        "    print(json.dumps({'error': 'path not found (is Drive mounted?)', 'path': p}))\n"
        "else:\n"
        "    entries = []\n"
        "    for name in sorted(os.listdir(p)):\n"
        "        fp = os.path.join(p, name)\n"
        "        entries.append({'name': name, 'is_dir': os.path.isdir(fp),\n"
        "                        'size': os.path.getsize(fp) if os.path.isfile(fp) else None})\n"
        "    print(json.dumps({'path': p, 'entries': entries}))\n"
    )
    return wrap_output(body)


def get_drive_tools(session_manager: SessionManager) -> list[Tool]:
    async def mount_drive(mount_point: str = "/content/drive",
                          session_id: str | None = None) -> str:
        """Mount Google Drive in the Colab VM.

        First mount may require UI consent; if so the result has
        needs_consent=True - use complete_drive_mount_consent (headless sessions).

        Args:
            mount_point: Where to mount. Default /content/drive.
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON with mount status.
        """
        session = session_manager.resolve_session(session_id)
        return json.dumps(await run_python(session, _gen_mount_code(mount_point)))

    async def unmount_drive(session_id: str | None = None) -> str:
        """Flush and unmount Google Drive.

        Args:
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON with unmount status.
        """
        session = session_manager.resolve_session(session_id)
        return json.dumps(await run_python(session, _gen_unmount_code()))

    async def list_drive_files(path: str = "/content/drive/MyDrive",
                               session_id: str | None = None) -> str:
        """List files under a mounted Drive path.

        Args:
            path: Directory to list. Default /content/drive/MyDrive.
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON with directory entries.
        """
        session = session_manager.resolve_session(session_id)
        return json.dumps(await run_python(session, _gen_list_drive_code(path)))

    return [
        Tool.from_function(fn=mount_drive, name="mount_drive",
                           description="Mount Google Drive in the Colab VM."),
        Tool.from_function(fn=unmount_drive, name="unmount_drive",
                           description="Flush and unmount Google Drive."),
        Tool.from_function(fn=list_drive_files, name="list_drive_files",
                           description="List files under a mounted Drive path."),
    ]
