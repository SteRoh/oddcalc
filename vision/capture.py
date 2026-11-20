from __future__ import annotations

import ctypes
import logging
from ctypes import wintypes
from dataclasses import dataclass
from typing import Self

import mss
import numpy as np


@dataclass(frozen=True)
class WindowInfo:
    hwnd: int
    title: str
    left: int
    top: int
    width: int
    height: int


class WindowCapture:
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._server: mss.MSS | None = None
        self._user32_api: ctypes.WinDLL | None = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self._server is not None:
            self._server.close()
            self._server = None

    def enable_dpi_awareness(self) -> None:
        """Request per-monitor DPI coordinates before enumerating windows."""
        user32 = self._user32()
        try:
            set_dpi_context = user32.SetProcessDpiAwarenessContext
        except AttributeError:
            self._logger.warning("Per-monitor DPI awareness is unavailable.")
            return

        set_dpi_context.argtypes = [ctypes.c_void_p]
        set_dpi_context.restype = wintypes.BOOL
        if not set_dpi_context(ctypes.c_void_p(-4)):
            self._logger.warning(
                "Could not enable per-monitor DPI awareness (Win32 error %d).",
                ctypes.get_last_error(),
            )

    def _user32(self) -> ctypes.WinDLL:
        if self._user32_api is not None:
            return self._user32_api
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.IsWindowVisible.restype = wintypes.BOOL
        user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        user32.GetWindowTextLengthW.restype = ctypes.c_int
        user32.GetWindowTextW.argtypes = [
            wintypes.HWND,
            wintypes.LPWSTR,
            ctypes.c_int,
        ]
        user32.GetWindowTextW.restype = ctypes.c_int
        user32.GetWindowRect.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(wintypes.RECT),
        ]
        user32.GetWindowRect.restype = wintypes.BOOL
        user32.IsWindow.argtypes = [wintypes.HWND]
        user32.IsWindow.restype = wintypes.BOOL
        self._user32_api = user32
        return user32

    def list_windows(self) -> list[WindowInfo]:
        user32 = self._user32()
        windows: list[WindowInfo] = []
        callback_type = ctypes.WINFUNCTYPE(
            wintypes.BOOL,
            wintypes.HWND,
            wintypes.LPARAM,
        )
        enum_windows = user32.EnumWindows
        enum_windows.argtypes = [callback_type, wintypes.LPARAM]
        enum_windows.restype = wintypes.BOOL

        @callback_type
        def callback(hwnd: int, *_: int) -> bool:
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value.strip()
            if not title:
                return True

            rect = wintypes.RECT()
            if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return True
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            if width > 0 and height > 0:
                windows.append(WindowInfo(hwnd, title, rect.left, rect.top, width, height))
            return True

        enum_windows(callback, 0)
        return windows

    def refresh_window(self, window: WindowInfo) -> WindowInfo:
        user32 = self._user32()
        if not user32.IsWindow(window.hwnd):
            raise RuntimeError(f"Selected window is no longer available: {window.title}")

        rect = wintypes.RECT()
        if not user32.GetWindowRect(window.hwnd, ctypes.byref(rect)):
            raise ctypes.WinError(ctypes.get_last_error())
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        if width <= 0 or height <= 0:
            raise RuntimeError(f"Selected window has invalid dimensions: {window.title}")

        return WindowInfo(
            hwnd=window.hwnd,
            title=window.title,
            left=rect.left,
            top=rect.top,
            width=width,
            height=height,
        )

    def capture_window(self, window: WindowInfo) -> np.ndarray:
        if window.width <= 0 or window.height <= 0:
            raise ValueError("Window dimensions must be positive.")
        if self._server is None:
            self._server = mss.mss()
        monitor = {
            "left": window.left,
            "top": window.top,
            "width": window.width,
            "height": window.height,
        }
        shot = np.asarray(self._server.grab(monitor))
        # MSS returns BGRA; OpenCV uses BGR.
        return shot[:, :, :3]
