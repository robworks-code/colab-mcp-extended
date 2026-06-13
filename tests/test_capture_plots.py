import inspect
import json

import pytest

from colab_mcp.tools.execution import (
    _gen_capture_plots_suffix,
    get_execution_tools,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_capture_suffix_valid_and_base64():
    code = _gen_capture_plots_suffix()
    compile(code, "<gen>", "exec")
    assert "savefig" in code or "to_png" in code or "base64" in code
    assert "get_fignums" in code


class _Client:
    def __init__(self, text):
        self.text = text

    def client_factory(self):
        return self

    async def call_tool(self, name, params):
        return self.text


class _Sess:
    def __init__(self, text):
        self.session_id = "s1"
        self.proxy_client = _Client(text)

    def is_connected(self):
        return True


class _SM:
    def __init__(self, text="plain output"):
        self._text = text

    def resolve_session(self, sid=None):
        return _Sess(self._text)


def test_execute_code_has_capture_plots_param():
    tools = {t.name: t for t in get_execution_tools(_SM())}
    sig = inspect.signature(tools["execute_code"].fn)
    assert "capture_plots" in sig.parameters


@pytest.mark.anyio
async def test_no_capture_returns_plain_json():
    tools = {t.name: t for t in get_execution_tools(_SM("hello"))}
    out = await tools["execute_code"].fn(code="print('hello')")
    # default path returns a JSON string, not a list
    assert isinstance(out, str)
    parsed = json.loads(out)
    assert "hello" in json.dumps(parsed)
