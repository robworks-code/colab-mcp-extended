from abc import ABC, abstractmethod


class NotSupportedError(RuntimeError):
    """Raised when a backend cannot perform a UI action (e.g. webbrowser backend)."""


class BrowserBackend(ABC):
    """Abstract interface for browser backends that open and maintain Colab sessions."""

    @abstractmethod
    async def open(self, url: str) -> None:
        """Open the given URL in the browser."""

    @abstractmethod
    async def close(self) -> None:
        """Close the browser page/tab."""

    @abstractmethod
    async def is_alive(self) -> bool:
        """Check whether the browser page is still active."""

    @abstractmethod
    async def keepalive(self) -> None:
        """Perform a keepalive action to prevent Colab session timeout."""

    # UI-driving actions. These are concrete (not abstract) so backends that
    # cannot drive the DOM (e.g. webbrowser) inherit the NotSupportedError
    # default rather than being forced to implement them.
    async def change_runtime_type(self, accelerator: str) -> dict:
        raise NotSupportedError("change_runtime_type requires the Playwright backend")

    async def connect_runtime(self) -> dict:
        raise NotSupportedError("connect_runtime requires the Playwright backend")

    async def factory_reset_runtime(self) -> dict:
        raise NotSupportedError("factory_reset_runtime requires the Playwright backend")

    async def save_notebook(self) -> dict:
        raise NotSupportedError("save_notebook requires the Playwright backend")

    async def complete_drive_mount_consent(self) -> dict:
        raise NotSupportedError("complete_drive_mount_consent requires the Playwright backend")
