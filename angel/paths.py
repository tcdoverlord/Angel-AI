from __future__ import annotations

import os
import sys
from pathlib import Path


def app_data_dir(override: str | Path | None = None) -> Path:
    """Return Angel's durable local data directory."""
    if override:
        root = Path(override).expanduser()
    elif os.environ.get("ANGEL_DATA_DIR"):
        root = Path(os.environ["ANGEL_DATA_DIR"]).expanduser()
    else:
        local_app_data = os.environ.get("LOCALAPPDATA")
        root = Path(local_app_data) / "Angel" if local_app_data else Path.home() / ".angel"
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def database_path(override: str | Path | None = None) -> Path:
    return app_data_dir(override) / "angel.db"


def log_path(override: str | Path | None = None) -> Path:
    return app_data_dir(override) / "angel.log"


def bundled_path(relative: str) -> Path:
    """Resolve a resource in source and PyInstaller runtimes."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / relative
