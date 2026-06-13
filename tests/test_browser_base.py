import pytest

from colab_mcp.browser.base import NotSupportedError
from colab_mcp.browser.webbrowser_backend import WebbrowserBackend


def test_webbrowser_ui_actions_raise_not_supported():
    b = WebbrowserBackend()
    with pytest.raises(NotSupportedError):
        b.change_runtime_type_sync_check()
