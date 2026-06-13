"""Headless browser backend using Playwright for automated Colab sessions."""

from __future__ import annotations

import logging
from pathlib import Path

from playwright.async_api import async_playwright, BrowserContext, Page

from colab_mcp.browser.base import BrowserBackend
from colab_mcp.browser import colab_selectors as sel

DEFAULT_PROFILE_DIR = Path.home() / ".colab-mcp" / "browser-profile"


class PlaywrightBackend(BrowserBackend):
    """Browser backend using Playwright for headless Chromium automation.

    Uses a persistent browser context (Chromium user data directory) to
    reuse Google auth cookies across sessions. First-time setup requires
    manual login — run with headless=False once, or use:
        playwright open https://accounts.google.com
    to create the browser profile.
    """

    def __init__(self, user_data_dir: str | None = None):
        self.user_data_dir = str(Path(user_data_dir) if user_data_dir else DEFAULT_PROFILE_DIR)
        self._playwright = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    @property
    def page(self) -> Page | None:
        return self._page

    async def open(self, url: str) -> None:
        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)

        self._playwright = await async_playwright().start()

        # Use persistent context for native cookie/auth persistence
        # This survives crashes (unlike storage_state JSON snapshots)
        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=True,
            viewport={"width": 1280, "height": 900},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ],
        )

        self._page = await self._context.new_page()

        logging.info(f"PlaywrightBackend: navigating to {url}")
        await self._page.goto(url, wait_until="domcontentloaded", timeout=60000)
        logging.info("PlaywrightBackend: page loaded")

    async def close(self) -> None:
        if self._page and not self._page.is_closed():
            await self._page.close()
            self._page = None
        if self._context:
            await self._context.close()
            self._context = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def is_alive(self) -> bool:
        if self._page is None or self._page.is_closed():
            return False
        try:
            await self._page.evaluate("document.title")
            return True
        except Exception:
            return False

    async def keepalive(self) -> None:
        """Evaluate a lightweight JS expression to prevent Colab idle timeout."""
        if self._page and not self._page.is_closed():
            try:
                await self._page.evaluate("void(0)")
            except Exception:
                logging.warning("PlaywrightBackend: keepalive failed")

    async def change_runtime_type(self, accelerator: str) -> dict:
        page = self._page
        try:
            await page.click(sel.RUNTIME_MENU_BUTTON)
            await page.click(sel.CHANGE_RUNTIME_TYPE_ITEM)
            await page.click(sel.ACCELERATOR_DROPDOWN)
            await page.click(f'text="{accelerator}"')
            await page.click(sel.SAVE_BUTTON)
            return {"changed": True, "accelerator": accelerator}
        except Exception as e:  # noqa: BLE001
            return {"changed": False, "error": str(e)}

    async def connect_runtime(self) -> dict:
        page = self._page
        await page.click(sel.CONNECT_BUTTON)
        try:
            await page.wait_for_selector(sel.CONNECTED_BADGE, timeout=120_000)
            return {"connected": True}
        except Exception as e:  # noqa: BLE001
            return {"connected": False, "error": str(e)}

    async def factory_reset_runtime(self) -> dict:
        page = self._page
        try:
            await page.click(sel.RUNTIME_MENU_BUTTON)
            await page.click(sel.DISCONNECT_DELETE_ITEM)
            await page.click(sel.CONFIRM_YES_BUTTON)
            return {"reset": True}
        except Exception as e:  # noqa: BLE001
            return {"reset": False, "error": str(e)}

    async def save_notebook(self) -> dict:
        page = self._page
        await page.keyboard.press("Control+s")
        try:
            await page.wait_for_selector(sel.SAVING_DONE_INDICATOR, timeout=30_000)
            return {"saved": True}
        except Exception as e:  # noqa: BLE001
            return {"saved": False, "error": str(e)}

    async def complete_drive_mount_consent(self) -> dict:
        page = self._page
        try:
            await page.click(sel.DRIVE_CONSENT_ALLOW, timeout=30_000)
            return {"consented": True}
        except Exception as e:  # noqa: BLE001
            return {"consented": False, "error": str(e)}
