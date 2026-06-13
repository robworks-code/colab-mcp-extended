import pytest
from colab_mcp.browser.webbrowser_backend import WebbrowserBackend
from colab_mcp.browser.base import NotSupportedError


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_webbrowser_ui_actions_raise_not_supported():
    b = WebbrowserBackend()
    with pytest.raises(NotSupportedError):
        await b.change_runtime_type("T4 GPU")
