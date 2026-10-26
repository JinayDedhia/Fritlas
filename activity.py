"""Low-latency, opt-in foreground activity collection for Windows."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path
import threading

import storage


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


def idle_seconds() -> int:
    info = LASTINPUTINFO(ctypes.sizeof(LASTINPUTINFO), 0)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info))
    # GetTickCount is a 32-bit timer; masking keeps the calculation correct across wraparound.
    now = ctypes.windll.kernel32.GetTickCount() & 0xFFFFFFFF
    return ((now - info.dwTime) & 0xFFFFFFFF) // 1000


def foreground_window() -> tuple[str, str]:
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    length = user32.GetWindowTextLengthW(hwnd)
    title = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, title, length + 1)
    process_id = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, process_id.value)
    app_name = f"process-{process_id.value}"
    if handle:
        try:
            size = wintypes.DWORD(32768)
            path = ctypes.create_unicode_buffer(size.value)
            if ctypes.windll.kernel32.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)):
                app_name = Path(path.value).name
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    return app_name, title.value or "Untitled window"


def category_for(app_name: str) -> str:
    name = app_name.lower()
    if name in {"code.exe", "devenv.exe", "pycharm64.exe", "notepad.exe"}:
        return "focus"
    if name in {"slack.exe", "teams.exe", "outlook.exe", "discord.exe"}:
        return "communication"
    if name in {"chrome.exe", "msedge.exe", "firefox.exe"}:
        return "browser"
    return "other"


class ActivityTracker:
    """Writes only meaningful state changes, so a one-second poll stays lightweight."""

    def __init__(self, interval: float = 1.0, idle_threshold: int = 300):
        self.interval = interval
        self.idle_threshold = idle_threshold
        self.paused = False
        self.running = False
        self.current_app = "Waiting for activity"
        self._last: tuple[str, str, bool] | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        self.running = True
        threading.Thread(target=self._loop, daemon=True, name="fritlas-activity").start()

    def stop(self) -> None:
        self.running = False
        self._stop.set()

    def toggle_pause(self) -> bool:
        self.paused = not self.paused
        self._last = None
        return self.paused

    def _loop(self) -> None:
        while not self._stop.is_set():
            if not self.paused:
                app_name, title = foreground_window()
                idle = idle_seconds()
                is_idle = idle >= self.idle_threshold
                self.current_app = "Idle" if is_idle else app_name
                current = (app_name, title, is_idle)
                if current != self._last:
                    storage.add_event(
                        datetime.now(timezone.utc).isoformat(),
                        "Idle" if is_idle else app_name,
                        "Away from keyboard" if is_idle else title,
                        category="idle" if is_idle else category_for(app_name),
                        idle_seconds=idle,
                    )
                    self._last = current
            self._stop.wait(self.interval)
