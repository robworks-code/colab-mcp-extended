import json
import pytest
from colab_mcp.browser.base import NotSupportedError
from colab_mcp.tools import notebook as nb


@pytest.fixture
def anyio_backend():
    return "asyncio"


class _FakeBackendOK:
    async def change_runtime_type(self, accelerator):
        return {"changed": True, "accelerator": accelerator}
    async def save_notebook(self):
        return {"saved": True}


class _FakeBackendNoUI:
    async def change_runtime_type(self, accelerator):
        raise NotSupportedError("nope")


class _Sess:
    def __init__(self, backend, connected=True):
        self.session_id = "s1"
        self.backend = backend
        self._c = connected
    def is_connected(self):
        return self._c


def _tool(tools, name):
    t = {x.name: x for x in tools}[name]
    return t  # has .fn callable (verify attribute during implementation)


@pytest.mark.anyio
async def test_change_runtime_type_success():
    class _SM:
        def resolve_session(self, sid=None):
            return _Sess(_FakeBackendOK())
    tools = nb.get_notebook_tools(_SM())
    fn = _tool(tools, "change_runtime_type").fn
    out = json.loads(await fn(accelerator="T4 GPU"))
    assert out["changed"] is True


@pytest.mark.anyio
async def test_change_runtime_type_no_ui_returns_error():
    class _SM:
        def resolve_session(self, sid=None):
            return _Sess(_FakeBackendNoUI())
    tools = nb.get_notebook_tools(_SM())
    fn = _tool(tools, "change_runtime_type").fn
    out = json.loads(await fn(accelerator="T4 GPU"))
    assert "error" in out
