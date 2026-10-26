"""Local SQLite persistence for Fritlas."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from paths import DATA_ROOT

DATABASE_PATH = DATA_ROOT / "fritlas.db"
LEGACY_DATABASE_PATH = DATA_ROOT / "friction_atlas.db"


@contextmanager
def connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=15000")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def initialize() -> None:
    # Preserve early Fritlas data created before the product rename.
    if not DATABASE_PATH.exists() and LEGACY_DATABASE_PATH.exists():
        LEGACY_DATABASE_PATH.replace(DATABASE_PATH)
    with connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                occurred_at TEXT NOT NULL,
                app_name TEXT NOT NULL,
                window_title TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'other',
                idle_seconds INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_activity_time ON activity_events(occurred_at)"
        )
        columns = {row[1] for row in conn.execute("PRAGMA table_info(activity_events)")}
        if "category" not in columns:
            conn.execute("ALTER TABLE activity_events ADD COLUMN category TEXT NOT NULL DEFAULT 'other'")
        if "idle_seconds" not in columns:
            conn.execute("ALTER TABLE activity_events ADD COLUMN idle_seconds INTEGER NOT NULL DEFAULT 0")
        conn.execute(
            """CREATE TABLE IF NOT EXISTS behavior_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT, occurred_at TEXT NOT NULL,
                app_name TEXT NOT NULL, category TEXT NOT NULL,
                mouse_distance REAL NOT NULL, switches INTEGER NOT NULL,
                idle_seconds INTEGER NOT NULL, active_seconds REAL NOT NULL
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS check_ins (
                id INTEGER PRIMARY KEY AUTOINCREMENT, occurred_at TEXT NOT NULL,
                intention TEXT NOT NULL, energy INTEGER NOT NULL
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS ai_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT, occurred_at TEXT NOT NULL,
                label TEXT NOT NULL, message TEXT NOT NULL
            )"""
        )


def add_event(occurred_at: str, app_name: str, window_title: str, category: str = "other", idle_seconds: int = 0) -> None:
    with connection() as conn:
        conn.execute(
            "INSERT INTO activity_events (occurred_at, app_name, window_title, category, idle_seconds) VALUES (?, ?, ?, ?, ?)",
            (occurred_at, app_name, window_title, category, idle_seconds),
        )


def recent_events(limit: int | None = 500):
    with connection() as conn:
        if limit is None:
            return conn.execute(
                "SELECT occurred_at, app_name, window_title, category, idle_seconds FROM activity_events "
                "ORDER BY occurred_at DESC"
            ).fetchall()
        return conn.execute(
            "SELECT occurred_at, app_name, window_title, category, idle_seconds FROM activity_events "
            "ORDER BY occurred_at DESC LIMIT ?",
            (limit,),
        ).fetchall()


def add_behavior_sample(occurred_at: str, app_name: str, category: str, mouse_distance: float, switches: int, idle: int, active_seconds: float) -> None:
    with connection() as conn:
        conn.execute(
            "INSERT INTO behavior_samples (occurred_at, app_name, category, mouse_distance, switches, idle_seconds, active_seconds) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (occurred_at, app_name, category, mouse_distance, switches, idle, active_seconds),
        )


def recent_behavior_samples(limit: int = 100):
    with connection() as conn:
        return conn.execute("SELECT * FROM behavior_samples ORDER BY occurred_at DESC LIMIT ?", (limit,)).fetchall()


def add_check_in(occurred_at: str, intention: str, energy: int) -> None:
    with connection() as conn:
        conn.execute("INSERT INTO check_ins (occurred_at, intention, energy) VALUES (?, ?, ?)", (occurred_at, intention, energy))


def latest_check_in():
    with connection() as conn:
        return conn.execute("SELECT * FROM check_ins ORDER BY occurred_at DESC LIMIT 1").fetchone()


def add_feedback(occurred_at: str, label: str, message: str) -> None:
    with connection() as conn:
        conn.execute("INSERT INTO ai_feedback (occurred_at, label, message) VALUES (?, ?, ?)", (occurred_at, label, message))


def recent_feedback(limit: int = 20):
    with connection() as conn:
        return conn.execute("SELECT * FROM ai_feedback ORDER BY occurred_at DESC LIMIT ?", (limit,)).fetchall()

