"""Live runtime hardware/resource state tools."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from fastmcp.tools.tool import Tool

from colab_mcp.tools._runner import run_python, wrap_output

if TYPE_CHECKING:
    from colab_mcp.session_manager import SessionManager


def _gen_resource_usage_code() -> str:
    body = r'''
import json, subprocess, shutil, psutil
info = {}
try:
    q = ["nvidia-smi",
         "--query-gpu=utilization.gpu,memory.used,memory.total",
         "--format=csv,noheader,nounits"]
    r = subprocess.run(q, capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        util, used, total = [x.strip() for x in r.stdout.strip().splitlines()[0].split(",")]
        info["gpu_util_percent"] = float(util)
        info["gpu_mem_used_mb"] = float(used)
        info["gpu_mem_total_mb"] = float(total)
    else:
        info["gpu"] = None
except FileNotFoundError:
    info["gpu"] = None
mem = psutil.virtual_memory()
info["ram_used_gb"] = round((mem.total - mem.available) / (1024**3), 2)
info["ram_total_gb"] = round(mem.total / (1024**3), 2)
disk = shutil.disk_usage("/")
info["disk_used_gb"] = round((disk.total - disk.free) / (1024**3), 2)
info["disk_total_gb"] = round(disk.total / (1024**3), 2)
print(json.dumps(info))
'''
    return wrap_output(body)


def get_runtime_tools(session_manager: SessionManager) -> list[Tool]:
    async def get_resource_usage(session_id: str | None = None) -> str:
        """Get LIVE resource utilization: GPU util %, GPU/RAM/disk used.

        Complements get_runtime_info (which reports static totals). Use this to
        watch utilization during training.

        Args:
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON with live usage figures.
        """
        session = session_manager.resolve_session(session_id)
        result = await run_python(session, _gen_resource_usage_code())
        return json.dumps(result)

    return [
        Tool.from_function(
            fn=get_resource_usage,
            name="get_resource_usage",
            description="Get LIVE resource utilization: GPU util %, GPU/RAM/disk used.",
        ),
    ]
