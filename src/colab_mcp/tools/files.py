"""MCP tools for file operations and environment management in Colab sessions."""

from __future__ import annotations

import json
import shlex
from typing import TYPE_CHECKING

from fastmcp.tools.tool import Tool
from mcp.types import TextContent

from colab_mcp.tools._runner import wrap_output, run_python

if TYPE_CHECKING:
    from colab_mcp.session_manager import SessionManager

# Unique delimiters to isolate our output from other kernel noise
_OUTPUT_START = "___COLAB_MCP_OUTPUT_START___"
_OUTPUT_END = "___COLAB_MCP_OUTPUT_END___"


def _extract_text(result) -> str:
    """Extract text content from an MCP tool result."""
    if isinstance(result, list):
        return "".join(c.text for c in result if isinstance(c, TextContent))
    return str(result)


def _extract_delimited(raw: str) -> str:
    """Extract content between output delimiters, ignoring surrounding noise."""
    start = raw.find(_OUTPUT_START)
    end = raw.find(_OUTPUT_END)
    if start != -1 and end != -1:
        return raw[start + len(_OUTPUT_START):end].strip()
    # Fallback: return stripped raw text
    return raw.strip()


def _gen_list_vm_code(path: str) -> str:
    body = (
        "import json, os\n"
        f"p = {path!r}\n"
        "if not os.path.exists(p):\n"
        "    print(json.dumps({'error': 'path not found', 'path': p}))\n"
        "else:\n"
        "    entries = []\n"
        "    for name in sorted(os.listdir(p)):\n"
        "        fp = os.path.join(p, name)\n"
        "        entries.append({'name': name, 'is_dir': os.path.isdir(fp),\n"
        "                        'size': os.path.getsize(fp) if os.path.isfile(fp) else None})\n"
        "    print(json.dumps({'path': p, 'entries': entries}))\n"
    )
    return wrap_output(body)


def _gen_read_vm_code(path: str, max_bytes: int) -> str:
    body = (
        "import json\n"
        f"p = {path!r}\n"
        f"n = {int(max_bytes)}\n"
        "try:\n"
        "    with open(p, 'r', errors='replace') as f:\n"
        "        data = f.read(n + 1)\n"
        "    truncated = len(data) > n\n"
        "    print(json.dumps({'path': p, 'content': data[:n], 'truncated': truncated}))\n"
        "except Exception as e:\n"
        "    print(json.dumps({'error': str(e), 'path': p}))\n"
    )
    return wrap_output(body)


def _gen_write_vm_code(path: str, content: str) -> str:
    # Embed content as a JSON literal so quotes/newlines survive intact.
    encoded = json.dumps(content)
    body = (
        "import json\n"
        f"p = {path!r}\n"
        f"content = json.loads({encoded!r})\n"
        "try:\n"
        "    with open(p, 'w') as f:\n"
        "        f.write(content)\n"
        "    print(json.dumps({'written': True, 'path': p, 'bytes': len(content)}))\n"
        "except Exception as e:\n"
        "    print(json.dumps({'written': False, 'error': str(e)}))\n"
    )
    return wrap_output(body)


def _gen_delete_vm_code(path: str) -> str:
    body = (
        "import json, os, shutil\n"
        f"p = {path!r}\n"
        "try:\n"
        "    if os.path.isdir(p):\n"
        "        shutil.rmtree(p)\n"
        "    else:\n"
        "        os.remove(p)\n"
        "    print(json.dumps({'deleted': True, 'path': p}))\n"
        "except Exception as e:\n"
        "    print(json.dumps({'deleted': False, 'error': str(e)}))\n"
    )
    return wrap_output(body)


def get_file_tools(session_manager: SessionManager) -> list[Tool]:
    """Create file and environment management tools bound to the given SessionManager."""

    async def install_package(
        package: str,
        session_id: str | None = None,
    ) -> str:
        """Install a Python package in the Colab session using pip.

        Args:
            package: Package specifier (e.g. "pandas", "torch>=2.0", "git+https://...").
            session_id: Target session ID. Uses active session if not specified.

        Returns:
            JSON with installation output.
        """
        session = session_manager.resolve_session(session_id)
        if not session.is_connected():
            return json.dumps({"error": f"Session {session.session_id} is not connected"})

        try:
            client = session.proxy_client.client_factory()
            code = f"!pip install {shlex.quote(package)}"
            result = await client.call_tool("execute_code", {"code": code})
            return json.dumps({
                "installed": package,
                "output": _extract_text(result),
                "session_id": session.session_id,
            })
        except Exception as e:
            return json.dumps({"error": str(e), "session_id": session.session_id})

    async def get_runtime_info(
        session_id: str | None = None,
    ) -> str:
        """Get information about the Colab runtime environment.

        Returns GPU type, available RAM, disk space, and Python version.

        Args:
            session_id: Target session ID. Uses active session if not specified.

        Returns:
            JSON with runtime environment details.
        """
        session = session_manager.resolve_session(session_id)
        if not session.is_connected():
            return json.dumps({"error": f"Session {session.session_id} is not connected"})

        code = """
import json, sys, os, subprocess
info = {"python_version": sys.version}
try:
    result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], capture_output=True, text=True)
    if result.returncode == 0:
        info["gpu"] = result.stdout.strip()
    else:
        info["gpu"] = None
except FileNotFoundError:
    info["gpu"] = None
import shutil
disk = shutil.disk_usage("/")
info["disk_total_gb"] = round(disk.total / (1024**3), 1)
info["disk_free_gb"] = round(disk.free / (1024**3), 1)
import psutil
mem = psutil.virtual_memory()
info["ram_total_gb"] = round(mem.total / (1024**3), 1)
info["ram_available_gb"] = round(mem.available / (1024**3), 1)
print(json.dumps(info))
"""
        try:
            client = session.proxy_client.client_factory()
            result = await client.call_tool("execute_code", {"code": code})
            return json.dumps({
                "runtime_info": _extract_text(result),
                "session_id": session.session_id,
            })
        except Exception as e:
            return json.dumps({"error": str(e), "session_id": session.session_id})

    async def upload_file(
        local_path: str,
        remote_path: str | None = None,
        session_id: str | None = None,
    ) -> str:
        """Upload a local file to the Colab VM filesystem.

        Args:
            local_path: Path to the local file to upload.
            remote_path: Destination path on the Colab VM. Defaults to /content/{filename}.
            session_id: Target session ID. Uses active session if not specified.

        Returns:
            JSON with the remote file path.
        """
        session = session_manager.resolve_session(session_id)
        if not session.is_connected():
            return json.dumps({"error": f"Session {session.session_id} is not connected"})

        import base64
        from pathlib import Path

        local = Path(local_path)
        if not local.exists():
            return json.dumps({"error": f"Local file not found: {local_path}"})

        dest = remote_path or f"/content/{local.name}"
        file_bytes = local.read_bytes()
        data = base64.b64encode(file_bytes).decode()

        # Use json.dumps for safe string escaping to prevent code injection
        code = f"""
import base64
dest = {json.dumps(dest)}
data = base64.b64decode("{data}")
with open(dest, "wb") as f:
    f.write(data)
print(f"Uploaded {{len(data)}} bytes to {{dest}}")
"""
        try:
            client = session.proxy_client.client_factory()
            result = await client.call_tool("execute_code", {"code": code})
            return json.dumps({
                "uploaded": dest,
                "size_bytes": len(file_bytes),
                "output": _extract_text(result),
                "session_id": session.session_id,
            })
        except Exception as e:
            return json.dumps({"error": str(e), "session_id": session.session_id})

    async def download_file(
        remote_path: str,
        local_path: str,
        session_id: str | None = None,
    ) -> str:
        """Download a file from the Colab VM to the local filesystem.

        Args:
            remote_path: Path to the file on the Colab VM.
            local_path: Local destination path.
            session_id: Target session ID. Uses active session if not specified.

        Returns:
            JSON with the local file path and size.
        """
        session = session_manager.resolve_session(session_id)
        if not session.is_connected():
            return json.dumps({"error": f"Session {session.session_id} is not connected"})

        # Use delimiters to isolate base64 output from any kernel noise
        code = f"""
import base64
path = {json.dumps(remote_path)}
with open(path, "rb") as f:
    data = base64.b64encode(f.read()).decode()
print("{_OUTPUT_START}")
print(data)
print("{_OUTPUT_END}")
"""
        try:
            client = session.proxy_client.client_factory()
            result = await client.call_tool("execute_code", {"code": code})

            import base64
            from pathlib import Path

            raw = _extract_text(result)
            result_str = _extract_delimited(raw)
            file_data = base64.b64decode(result_str)
            dest = Path(local_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(file_data)

            return json.dumps({
                "downloaded": local_path,
                "size_bytes": len(file_data),
                "session_id": session.session_id,
            })
        except Exception as e:
            return json.dumps({"error": str(e), "session_id": session.session_id})

    async def list_vm_files(path: str = ".", session_id: str | None = None) -> str:
        """List files in a VM directory.

        Args:
            path: Directory path. Default current dir.
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON with entries.
        """
        session = session_manager.resolve_session(session_id)
        return json.dumps(await run_python(session, _gen_list_vm_code(path)))

    async def read_vm_file(path: str, max_bytes: int = 100_000,
                           session_id: str | None = None) -> str:
        """Read a text file from the VM (truncated to max_bytes).

        Args:
            path: File path.
            max_bytes: Max bytes to return. Default 100000.
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON with content and truncated flag.
        """
        session = session_manager.resolve_session(session_id)
        return json.dumps(await run_python(session, _gen_read_vm_code(path, max_bytes)))

    async def write_vm_file(path: str, content: str,
                            session_id: str | None = None) -> str:
        """Write text to a VM file (overwrites).

        Args:
            path: File path.
            content: Text content.
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON with written status.
        """
        session = session_manager.resolve_session(session_id)
        return json.dumps(await run_python(session, _gen_write_vm_code(path, content)))

    async def delete_vm_file(path: str, session_id: str | None = None) -> str:
        """Delete a VM file or directory.

        Args:
            path: File or directory path.
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON with deleted status.
        """
        session = session_manager.resolve_session(session_id)
        return json.dumps(await run_python(session, _gen_delete_vm_code(path)))

    return [
        Tool.from_function(
            fn=install_package,
            name="install_package",
            description="Install a Python package in the Colab session using pip.",
        ),
        Tool.from_function(
            fn=get_runtime_info,
            name="get_runtime_info",
            description=(
                "Get Colab runtime environment info: GPU type, RAM, disk space, Python version."
            ),
        ),
        Tool.from_function(
            fn=upload_file,
            name="upload_file",
            description="Upload a local file to the Colab VM filesystem.",
        ),
        Tool.from_function(
            fn=download_file,
            name="download_file",
            description="Download a file from the Colab VM to the local filesystem.",
        ),
        Tool.from_function(fn=list_vm_files, name="list_vm_files",
                           description="List files in a VM directory."),
        Tool.from_function(fn=read_vm_file, name="read_vm_file",
                           description="Read a text file from the VM (truncated)."),
        Tool.from_function(fn=write_vm_file, name="write_vm_file",
                           description="Write text to a VM file (overwrites)."),
        Tool.from_function(fn=delete_vm_file, name="delete_vm_file",
                           description="Delete a VM file or directory."),
    ]
