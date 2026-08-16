from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class InstallationLayout:
    root: Path
    data: Path
    cache: Path
    backups: Path
    knowledge: Path
    models: Path
    projects: Path
    creator: Path
    generated_images: Path
    generated_music: Path
    logs: Path
    settings: Path
    indexes: Path
    bible: Path

    @property
    def database(self) -> Path:
        return self.data / "angel.db"


def installation_root() -> Path:
    configured = os.environ.get("ANGEL_HOME", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def installation_layout(data_override: str | Path | None = None) -> InstallationLayout:
    if data_override:
        data = Path(data_override).expanduser().resolve()
        root = data
    else:
        root = installation_root()
        data = root / "data"
    layout = InstallationLayout(
        root=root,
        data=data,
        cache=root / "cache",
        backups=root / "backups",
        knowledge=root / "knowledge",
        models=root / "models",
        projects=root / "projects",
        creator=root / "creator",
        generated_images=data / "generated" / "images",
        generated_music=data / "generated" / "music",
        logs=data / "logs",
        settings=data / "settings",
        indexes=data / "indexes",
        bible=data / "bible",
    )
    ensure_layout(layout)
    if data_override is None:
        migrate_legacy_data(layout)
    return layout


def ensure_layout(layout: InstallationLayout) -> None:
    directories = (
        layout.root,
        layout.data,
        layout.cache,
        layout.backups,
        layout.knowledge,
        layout.models,
        layout.projects,
        layout.creator,
        layout.creator / "images",
        layout.creator / "music",
        layout.data / "memory",
        layout.data / "projects",
        layout.generated_images,
        layout.generated_music,
        layout.logs,
        layout.settings,
        layout.indexes,
        layout.bible,
    )
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def migrate_legacy_data(layout: InstallationLayout) -> bool:
    """Copy the former LocalAppData database once, never replacing newer data."""
    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if not local_app_data:
        return False
    legacy = Path(local_app_data) / "Angel"
    legacy_database = legacy / "angel.db"
    if layout.database.exists() or not legacy_database.is_file():
        return False
    staging = layout.data / ".angel.db.migrating"
    shutil.copy2(legacy_database, staging)
    os.replace(staging, layout.database)
    legacy_log = legacy / "angel.log"
    if legacy_log.is_file() and not (layout.logs / "legacy-angel.log").exists():
        shutil.copy2(legacy_log, layout.logs / "legacy-angel.log")
    return True


def app_data_dir(override: str | Path | None = None) -> Path:
    """Return Angel's controlled durable data directory."""
    if override:
        return installation_layout(override).data
    configured = os.environ.get("ANGEL_DATA_DIR", "").strip()
    if configured:
        return installation_layout(configured).data
    return installation_layout().data


def database_path(override: str | Path | None = None) -> Path:
    return app_data_dir(override) / "angel.db"


def log_path(override: str | Path | None = None) -> Path:
    data = app_data_dir(override)
    logs = data / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    return logs / "angel.log"


def safe_write_json(path: str | Path, value: Any) -> Path:
    """Durably write JSON beside its destination, then atomically replace it."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
    return target


def bundled_path(relative: str) -> Path:
    """Resolve a resource in source and PyInstaller runtimes."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / relative
