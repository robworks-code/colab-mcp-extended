"""MCP tools for code execution in Colab sessions."""

from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING

from fastmcp.tools.tool import Tool

from colab_mcp.tools._runner import run_python, wrap_output

if TYPE_CHECKING:
    from colab_mcp.session_manager import SessionManager


_REGISTRY_BOOTSTRAP = r'''
import threading, io, traceback, time, sys
if "__COLAB_MCP_JOBS__" not in globals():
    __COLAB_MCP_JOBS__ = {}
'''


def _gen_run_async_code(code: str, job_id: str) -> str:
    encoded = json.dumps(code)
    body = (
        _REGISTRY_BOOTSTRAP
        + "import json\n"
        + f"_uc = json.loads({encoded!r})\n"
        + f"_jid = {job_id!r}\n"
        + "_buf = io.StringIO()\n"
        + "__COLAB_MCP_JOBS__[_jid] = {'status': 'running', 'buf': _buf,\n"
        + "    'start': time.time(), 'stop': False, 'result': None, 'error': None}\n"
        + "def _runner(jid=_jid, src=_uc, buf=_buf):\n"
        + "    rec = __COLAB_MCP_JOBS__[jid]\n"
        + "    _old_out, _old_err = sys.stdout, sys.stderr\n"
        + "    sys.stdout = sys.stderr = buf\n"
        + "    try:\n"
        + "        _g = {'__COLAB_MCP_STOP__': lambda: __COLAB_MCP_JOBS__[jid]['stop']}\n"
        + "        exec(compile(src, '<async_job>', 'exec'), globals(), None)\n"
        + "        rec['status'] = 'done'\n"
        + "    except Exception as e:\n"
        + "        rec['status'] = 'error'\n"
        + "        rec['error'] = ''.join(traceback.format_exception(type(e), e, e.__traceback__))\n"
        + "    finally:\n"
        + "        sys.stdout, sys.stderr = _old_out, _old_err\n"
        + "_t = threading.Thread(target=_runner, daemon=True)\n"
        + "__COLAB_MCP_JOBS__[_jid]['thread'] = _t\n"
        + "_t.start()\n"
        + "print(json.dumps({'job_id': _jid, 'status': 'running'}))\n"
    )
    return wrap_output(body)


def _gen_poll_code(job_id: str, since_cursor: int) -> str:
    body = (
        "import json\n"
        f"_jid = {job_id!r}\n"
        f"_cur = {int(since_cursor)}\n"
        "if '__COLAB_MCP_JOBS__' not in globals() or _jid not in __COLAB_MCP_JOBS__:\n"
        "    print(json.dumps({'error': 'unknown job_id', 'job_id': _jid}))\n"
        "else:\n"
        "    _rec = __COLAB_MCP_JOBS__[_jid]\n"
        "    _full = _rec['buf'].getvalue()\n"
        "    _new = _full[_cur:]\n"
        "    print(json.dumps({'job_id': _jid, 'status': _rec['status'],\n"
        "        'new_output': _new, 'cursor': len(_full),\n"
        "        'result': _rec['result'], 'error': _rec['error']}))\n"
    )
    return wrap_output(body)


def _gen_stop_code(job_id: str) -> str:
    body = (
        "import json\n"
        f"_jid = {job_id!r}\n"
        "if '__COLAB_MCP_JOBS__' not in globals() or _jid not in __COLAB_MCP_JOBS__:\n"
        "    print(json.dumps({'error': 'unknown job_id', 'job_id': _jid}))\n"
        "else:\n"
        "    __COLAB_MCP_JOBS__[_jid]['stop'] = True\n"
        "    print(json.dumps({'job_id': _jid, 'stop_requested': True}))\n"
    )
    return wrap_output(body)


def _gen_list_jobs_code() -> str:
    body = (
        "import json, time\n"
        "if '__COLAB_MCP_JOBS__' not in globals():\n"
        "    print(json.dumps({'jobs': []}))\n"
        "else:\n"
        "    _jobs = []\n"
        "    for _jid, _rec in __COLAB_MCP_JOBS__.items():\n"
        "        _jobs.append({'job_id': _jid, 'status': _rec['status'],\n"
        "            'runtime_s': round(time.time() - _rec['start'], 1),\n"
        "            'cursor': len(_rec['buf'].getvalue())})\n"
        "    print(json.dumps({'jobs': _jobs}))\n"
    )
    return wrap_output(body)


def get_execution_tools(session_manager: SessionManager) -> list[Tool]:
    """Create execution tools bound to the given SessionManager."""

    async def execute_code(
        code: str,
        session_id: str | None = None,
    ) -> str:
        """Execute Python code in a Colab session's kernel.

        Runs the given code in the active (or specified) session. The code is
        executed in a temporary cell and the output is returned.

        Args:
            code: Python code to execute.
            session_id: Target session ID. Uses active session if not specified.

        Returns:
            JSON with execution output, errors, and status.
        """
        session = session_manager.resolve_session(session_id)
        if not session.is_connected():
            return json.dumps({"error": f"Session {session.session_id} is not connected"})

        # Proxy to Colab's execute_code tool if available
        try:
            client = session.proxy_client.client_factory()
            result = await client.call_tool("execute_code", {"code": code})
            return json.dumps({"output": str(result), "session_id": session.session_id})
        except Exception as e:
            return json.dumps({"error": str(e), "session_id": session.session_id})

    async def interrupt_kernel(
        session_id: str | None = None,
    ) -> str:
        """Interrupt the currently running execution in a Colab session.

        Args:
            session_id: Target session ID. Uses active session if not specified.

        Returns:
            Confirmation message.
        """
        session = session_manager.resolve_session(session_id)
        if not session.is_connected():
            return json.dumps({"error": f"Session {session.session_id} is not connected"})

        try:
            client = session.proxy_client.client_factory()
            result = await client.call_tool("interrupt_execution", {})
            return json.dumps({"interrupted": True, "session_id": session.session_id})
        except Exception as e:
            return json.dumps({"error": str(e), "session_id": session.session_id})

    async def restart_kernel(
        session_id: str | None = None,
    ) -> str:
        """Restart the Python kernel in a Colab session.

        This clears all variables and state. Use when the kernel is stuck
        or you need a fresh environment.

        Args:
            session_id: Target session ID. Uses active session if not specified.

        Returns:
            Confirmation message.
        """
        session = session_manager.resolve_session(session_id)
        if not session.is_connected():
            return json.dumps({"error": f"Session {session.session_id} is not connected"})

        try:
            client = session.proxy_client.client_factory()
            result = await client.call_tool("restart_kernel", {})
            return json.dumps({"restarted": True, "session_id": session.session_id})
        except Exception as e:
            return json.dumps({"error": str(e), "session_id": session.session_id})

    async def run_async(code: str, session_id: str | None = None) -> str:
        """Start long-running code in a background kernel thread; returns immediately.

        Use for hours-long jobs (training). Poll with poll_execution(job_id).
        The job shares kernel state (loaded models/vars). A pure-Python CPU loop
        contends with polls via the GIL; GPU work and !subprocesses do not.
        Inside the code, call __COLAB_MCP_STOP__() to cooperatively check for a
        stop request.

        Args:
            code: Python to run in the background.
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON with job_id and status 'running'.
        """
        session = session_manager.resolve_session(session_id)
        job_id = "job_" + uuid.uuid4().hex[:12]
        return json.dumps(await run_python(session, _gen_run_async_code(code, job_id)))

    async def poll_execution(job_id: str, since_cursor: int = 0,
                             session_id: str | None = None) -> str:
        """Poll an async job: status + output since the given cursor.

        Args:
            job_id: Job id from run_async.
            since_cursor: Byte offset returned by the previous poll. Start at 0.
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON with status, new_output, cursor, result, error.
        """
        session = session_manager.resolve_session(session_id)
        return json.dumps(await run_python(session, _gen_poll_code(job_id, since_cursor)))

    async def stop_async(job_id: str, session_id: str | None = None) -> str:
        """Request cooperative stop of an async job (best-effort).

        Sets a flag the job can check via __COLAB_MCP_STOP__(). Cannot hard-kill
        a thread; for killable work run a !subprocess inside the job.

        Args:
            job_id: Job id from run_async.
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON with stop_requested.
        """
        session = session_manager.resolve_session(session_id)
        return json.dumps(await run_python(session, _gen_stop_code(job_id)))

    async def list_jobs(session_id: str | None = None) -> str:
        """List async jobs in the kernel with status/runtime/cursor.

        Use to recover job_ids after losing conversation context.

        Args:
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON list of jobs.
        """
        session = session_manager.resolve_session(session_id)
        return json.dumps(await run_python(session, _gen_list_jobs_code()))

    return [
        Tool.from_function(
            fn=execute_code,
            name="execute_code",
            description=(
                "Execute Python code in a Colab session. Returns the output, "
                "including print statements, return values, and errors."
            ),
        ),
        Tool.from_function(
            fn=interrupt_kernel,
            name="interrupt_kernel",
            description="Interrupt the currently running code execution in a Colab session.",
        ),
        Tool.from_function(
            fn=restart_kernel,
            name="restart_kernel",
            description=(
                "Restart the Python kernel in a Colab session. "
                "Clears all variables and state."
            ),
        ),
        Tool.from_function(fn=run_async, name="run_async",
                           description="Start long-running code in a background kernel thread."),
        Tool.from_function(fn=poll_execution, name="poll_execution",
                           description="Poll an async job for status and new output."),
        Tool.from_function(fn=stop_async, name="stop_async",
                           description="Request cooperative stop of an async job."),
        Tool.from_function(fn=list_jobs, name="list_jobs",
                           description="List async jobs in the kernel."),
    ]
