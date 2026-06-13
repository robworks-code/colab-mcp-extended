"""Colab userdata secret tools."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from fastmcp.tools.tool import Tool

from colab_mcp.tools._runner import run_python, wrap_output

if TYPE_CHECKING:
    from colab_mcp.session_manager import SessionManager


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
        """Copy a Colab secret into an environment variable WITHOUT revealing it.

        The secret value is never returned to the agent - only success/failure.
        Ideal for HF_TOKEN and similar credentials.

        Args:
            secret_name: Name of the Colab secret (Secrets panel key).
            env_var: Environment variable name to set.
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON with {set: bool, env_var}.
        """
        session = session_manager.resolve_session(session_id)
        return json.dumps(await run_python(session, _gen_inject_code(secret_name, env_var)))

    async def get_secret(secret_name: str, session_id: str | None = None) -> str:
        """Read a Colab secret VALUE (sensitive - prefer inject_secret_to_env).

        Returns the plaintext secret to the caller. Only use when the value is
        genuinely needed in the conversation.

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
