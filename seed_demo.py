"""Populate local demo events, without recording any real activity."""

from datetime import datetime, timedelta, timezone

import storage

storage.initialize()
start = datetime.now(timezone.utc) - timedelta(hours=2)
events = [
    ("VS Code", "tracker.py - friction-atlas"),
    ("Chrome", "YouTube - music"),
    ("VS Code", "analysis.py - friction-atlas"),
    ("Chrome", "GitHub Issues"),
    ("VS Code", "README.md - friction-atlas"),
    ("Slack", "Team chat"),
    ("VS Code", "tracker.py - friction-atlas"),
]
for index, (app, title) in enumerate(events):
    storage.add_event((start + timedelta(minutes=index * 4)).isoformat(), app, title)
print(f"Added {len(events)} demo events.")

