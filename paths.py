"""Paths that work both from source and from the packaged Windows app."""

from __future__ import annotations

import os
import sys
from pathlib import Path

SOURCE_ROOT = Path(__file__).parent
RESOURCE_ROOT = Path(getattr(sys, "_MEIPASS", SOURCE_ROOT))
DATA_ROOT = (
    Path(os.environ.get("LOCALAPPDATA", SOURCE_ROOT)) / "Fritlas"
    if getattr(sys, "frozen", False)
    else SOURCE_ROOT / "data"
)

