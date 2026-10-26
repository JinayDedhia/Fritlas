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
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
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


def add_event(occurred_at: str, app_name: str, window_title: str, category: str = "other", idle_seconds: int = 0) -> None:
    with connection() as conn:
        conn.execute(
            "INSERT INTO activity_events (occurred_at, app_name, window_title, category, idle_seconds) VALUES (?, ?, ?, ?, ?)",
            (occurred_at, app_name, window_title, category, idle_seconds),
        )


def recent_events(limit: int = 500):
    with connection() as conn:
        return conn.execute(
            "SELECT occurred_at, app_name, window_title, category, idle_seconds FROM activity_events "
            "ORDER BY occurred_at DESC LIMIT ?",
            (limit,),
        ).fetchall()

