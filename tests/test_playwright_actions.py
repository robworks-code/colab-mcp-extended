import inspect

import pytest

pytest.importorskip("playwright")

from colab_mcp.browser.playwright_backend import PlaywrightBackend
from colab_mcp.browser.base import BrowserBackend


def test_playwright_has_ui_action_methods():
    for name in ("change_runtime_type", "connect_runtime",
                 "factory_reset_runtime", "save_notebook",
                 "complete_drive_mount_consent"):
        m = getattr(PlaywrightBackend, name, None)
        assert m is not None, f"missing {name}"
        assert inspect.iscoroutinefunction(m), f"{name} must be async"


def test_playwright_overrides_base_raisers():
    # The methods must be real overrides, not the inherited default-raising ones.
    for name in ("change_runtime_type", "connect_runtime",
                 "factory_reset_runtime", "save_notebook",
                 "complete_drive_mount_consent"):
        assert getattr(PlaywrightBackend, name) is not getattr(BrowserBackend, name), \
            f"{name} not overridden"
