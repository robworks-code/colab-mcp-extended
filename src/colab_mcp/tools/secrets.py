"""Colab userdata secret tools."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from fastmcp.tools.tool import Tool

from colab_mcp.tools._runner import run_python, wrap_output

if TYPE_CHECKING:
    from colab_mcp.session_manager import SessionManager


_DANGEROUS_ENV = {
    "LD_PRELOAD", "LD_LIBRARY_PATH", "DYLD_INSERT_LIBRARIES",
    "DYLD_LIBRARY_PATH", "PYTHONPATH", "PATH", "BASH_ENV",
}


def _validate_env_var(env_var: str) -> str | None:
    """Return an error message if env_var is unsafe to set, else None."""
    if not env_var or not env_var.strip():
        return "env_var must be non-empty"
    if env_var in _DANGEROUS_ENV:
        return f"refusing to set sensitive loader variable {env_var}"
    return None


def _gen_inject_code(secret_name: str, env_var: str) -> str:
    body = (
        "import json, os\n"
        "from google.colab import userdata\n"
        "try:\n"
        f"    os.environ[{env_var!r}] = userdata.get({secret_name!r})\n"
        f"    print(json.dumps({{'set': True, 'env_var': {env_var!r}}}))\n"
        "except Exception as e:\n"
        "    print(json.dumps({'set': False, 'error': str(e)}))\n"
    )
    return wrap_output(body)


def _gen_get_secret_code(secret_name: str) -> str:
    body = (
        "import json\n"
        "from google.colab import userdata\n"
        "try:\n"
        f"    print(json.dumps({{'value': userdata.get({secret_name!r})}}))\n"
        "except Exception as e:\n"
        "    print(json.dumps({'error': str(e)}))\n"
    )
    return wrap_output(body)


def get_secret_tools(session_manager: SessionManager) -> list[Tool]:
    async def inject_secret_to_env(secret_name: str, env_var: str,
                                   session_id: str | None = None) -> str:
        """Copy a Colab secret into an environment variable in the kernel.

        This call does not return the secret value. NOTE: the value is still
        reachable - any subsequent execute_code/run_async can read
        os.environ[env_var]. This reduces incidental exposure (the value isn't
        echoed back here) but is not a hard secret boundary. Refuses to set
        loader-sensitive variables (PATH, LD_PRELOAD, etc.).

        Args:
            secret_name: Name of the Colab secret (Secrets panel key).
            env_var: Environment variable name to set.
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON with {set: bool, env_var} or {set: False, error}.
        """
        err = _validate_env_var(env_var)
        if err:
            return json.dumps({"set": False, "error": err})
        session = session_manager.resolve_session(session_id)
        return json.dumps(await run_python(session, _gen_inject_code(secret_name, env_var)))

    async def get_secret(secret_name: str, session_id: str | None = None) -> str:
        """Read a Colab secret VALUE (sensitive - prefer inject_secret_to_env).

        WARNING: the value is printed as kernel cell output to return it, so it
        passes through the notebook output channel and may be persisted by Colab
        autosave. Only use when the plaintext value is genuinely needed.

        Args:
            secret_name: Name of the Colab secret.
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON with {value} or {error}.
        """
        session = session_manager.resolve_session(session_id)
        return json.dumps(await run_python(session, _gen_get_secret_code(secret_name)))

    return [
        Tool.from_function(fn=inject_secret_to_env, name="inject_secret_to_env",
                           description="Copy a Colab secret into an env var without revealing it."),
        Tool.from_function(fn=get_secret, name="get_secret",
                           description="Read a Colab secret value (sensitive)."),
    ]
