"""Kernel namespace inspection tools."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from fastmcp.tools.tool import Tool

from colab_mcp.tools._runner import run_python, wrap_output

if TYPE_CHECKING:
    from colab_mcp.session_manager import SessionManager


def _gen_list_vars_code() -> str:
    body = r'''
import json
out = []
for _k, _v in list(globals().items()):
    if _k.startswith('_'):
        continue
    if callable(_v) or type(_v).__name__ == 'module':
        continue
    _entry = {"name": _k, "type": type(_v).__name__}
    _shape = getattr(_v, "shape", None)
    if _shape is not None:
        _entry["shape"] = str(tuple(_shape))
    _dtype = getattr(_v, "dtype", None)
    if _dtype is not None:
        _entry["dtype"] = str(_dtype)
    out.append(_entry)
print(json.dumps({"variables": out}))
'''
    return wrap_output(body)


def _gen_inspect_var_code(name: str) -> str:
    body = (
        "import json\n"
        f"if {name!r} not in globals():\n"
        f"    print(json.dumps({{'error': 'not defined', 'name': {name!r}}}))\n"
        "else:\n"
        f"    _v = globals()[{name!r}]\n"
        f"    _info = {{'name': {name!r}, 'type': type(_v).__name__, 'repr': repr(_v)[:2000]}}\n"
        "    _shape = getattr(_v, 'shape', None)\n"
        "    if _shape is not None: _info['shape'] = str(tuple(_shape))\n"
        "    _dtype = getattr(_v, 'dtype', None)\n"
        "    if _dtype is not None: _info['dtype'] = str(_dtype)\n"
        "    _head = getattr(_v, 'head', None)\n"
        "    if callable(_head):\n"
        "        try: _info['head'] = _v.head().to_string()\n"
        "        except Exception: pass\n"
        "    print(json.dumps(_info))\n"
    )
    return wrap_output(body)


def get_inspect_tools(session_manager: SessionManager) -> list[Tool]:
    async def list_variables(session_id: str | None = None) -> str:
        """List user-defined kernel variables with type + shape/dtype.

        Filters out underscore-prefixed names, callables and modules. Great for seeing loaded
        tensors/arrays/DataFrames during ML work.

        Args:
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON list of {name, type, shape?, dtype?}.
        """
        session = session_manager.resolve_session(session_id)
        return json.dumps(await run_python(session, _gen_list_vars_code()))

    async def inspect_variable(name: str, session_id: str | None = None) -> str:
        """Inspect one kernel variable: repr, type, shape/dtype, DataFrame head.

        Args:
            name: Variable name in the kernel namespace.
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON with details or {error: 'not defined'}.
        """
        session = session_manager.resolve_session(session_id)
        return json.dumps(await run_python(session, _gen_inspect_var_code(name)))

    return [
        Tool.from_function(fn=list_variables, name="list_variables",
                           description="List user-defined kernel variables with type and shape/dtype."),
        Tool.from_function(fn=inspect_variable, name="inspect_variable",
                           description="Inspect one kernel variable: repr, type, shape/dtype, DataFrame head."),
    ]
