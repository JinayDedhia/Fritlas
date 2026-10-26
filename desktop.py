"""The Windows desktop entry point for Fritlas."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk
import webbrowser

from activity import ActivityTracker
import storage
from tracker import serve


class FritlasApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        storage.initialize()
        self.tracker = ActivityTracker(interval=1.0)
        self.tracker.start()
        self.server = serve()
        threading.Thread(target=self.server.serve_forever, daemon=True, name="fritlas-dashboard").start()

        self.title("Fritlas")
        self.geometry("440x305")
        self.resizable(False, False)
        self.configure(bg="#111311")
        self.protocol("WM_DELETE_WINDOW", self.close)
        self._build()
        self.refresh()

    def _build(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Main.TFrame", background="#111311")
        style.configure("Title.TLabel", background="#111311", foreground="#f2f5ef", font=("Segoe UI", 27, "bold"))
        style.configure("Copy.TLabel", background="#111311", foreground="#b6bcb4", font=("Segoe UI", 10))
        style.configure("Status.TLabel", background="#1a1e1a", foreground="#9abe82", font=("Segoe UI", 11, "bold"))
        style.configure("App.TLabel", background="#1a1e1a", foreground="#f2f5ef", font=("Segoe UI", 14))
        style.configure("TButton", padding=(14, 8), font=("Segoe UI", 10, "bold"))
        frame = ttk.Frame(self, style="Main.TFrame", padding=28)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Fritlas", style="Title.TLabel").pack(anchor="w")
        ttk.Label(frame, text="Your private momentum map", style="Copy.TLabel").pack(anchor="w", pady=(0, 22))
        card = ttk.Frame(frame, padding=16, style="Main.TFrame")
        card.pack(fill="x")
        self.status = ttk.Label(card, text="● TRACKING", style="Status.TLabel")
        self.status.pack(anchor="w")
        self.current = ttk.Label(card, text="Waiting for activity", style="App.TLabel")
        self.current.pack(anchor="w", pady=(6, 0))
        buttons = ttk.Frame(frame, style="Main.TFrame")
        buttons.pack(fill="x", pady=(22, 0))
        self.pause_button = ttk.Button(buttons, text="Pause tracking", command=self.toggle_pause)
        self.pause_button.pack(side="left")
        ttk.Button(buttons, text="Open dashboard", command=lambda: webbrowser.open("http://127.0.0.1:8765")).pack(side="right")

    def toggle_pause(self) -> None:
        paused = self.tracker.toggle_pause()
        self.pause_button.configure(text="Resume tracking" if paused else "Pause tracking")

    def refresh(self) -> None:
        if self.tracker.paused:
            self.status.configure(text="Ⅱ PAUSED", foreground="#e0ad65")
            self.current.configure(text="No activity is being saved")
        else:
            self.status.configure(text="● TRACKING", foreground="#9abe82")
            self.current.configure(text=self.tracker.current_app)
        self.after(500, self.refresh)

    def close(self) -> None:
        self.tracker.stop()
        self.server.shutdown()
        self.destroy()


if __name__ == "__main__":
    FritlasApp().mainloop()

