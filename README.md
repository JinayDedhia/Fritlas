# Fritlas

A private, local-first activity journal that spots costly context switches and recurring friction loops.

## Features

- Native Windows control window with immediate pause/resume.
- Captures meaningful foreground-app changes every second, rather than writing a constant stream of data.
- Detects away-from-keyboard time after five minutes of inactivity.
- Categorizes activity as focus, communication, browser, other, or idle.
- Stores events in a local SQLite database; no cloud connection or keylogging.
- Detects rapid app switching and reports the most frequent app-to-app transitions.
- Serves a responsive local dashboard at `http://127.0.0.1:8765`.

## Quick start

Requires Python 3.11+ on Windows. No third-party packages are needed.

```powershell
python desktop.py
```

Use the desktop window to pause tracking or open the detailed dashboard. Close the window to stop Fritlas.

For a safe demo without collecting desktop activity:

```powershell
python seed_demo.py
python tracker.py --dashboard-only
```

## Build a Windows executable

PyInstaller is the only build dependency. From this folder, run:

```powershell
python -m PyInstaller --noconfirm --clean --onefile --noconsole --name Fritlas --add-data "web;web" desktop.py
```

The output is `dist/Fritlas.exe`. When packaged, Fritlas stores data in `%LOCALAPPDATA%/Fritlas/fritlas.db`, so upgrades do not overwrite your activity history.

## Privacy model

Data stays in `data/fritlas.db` on this machine (or `%LOCALAPPDATA%/Fritlas/fritlas.db` in the executable). The tracker records app names and window titles, which may contain sensitive text. Pause it whenever needed and do not commit the database to Git.

## Next milestones

1. Add a tray control and app/title redaction rules.
2. Add optional calendar and task imports.
3. Add a weekly reflection generated from aggregated, user-approved data.

