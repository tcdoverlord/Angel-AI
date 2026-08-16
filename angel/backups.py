from __future__ import annotations

import json
import os
import shutil
import sqlite3
import uuid
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .database import Database, utc_now
from .paths import InstallationLayout, ensure_layout


BACKUP_PREFIX = "angel-backup-"
BACKUP_SUFFIX = ".zip"


class DatabaseRecoveryError(RuntimeError):
    pass


@dataclass(frozen=True)
class BackupInfo:
    path: str
    name: str
    size: int
    created_at: str
    reason: str


def sqlite_quick_check(path: str | Path) -> tuple[bool, str]:
    try:
        connection = sqlite3.connect(Path(path), timeout=5)
        try:
            row = connection.execute("PRAGMA quick_check").fetchone()
        finally:
            connection.close()
        result = str(row[0] if row else "no result")
        return result.lower() == "ok", result
    except sqlite3.DatabaseError as exc:
        return False, f"{type(exc).__name__}: {exc}"


def recover_database_if_needed(layout: InstallationLayout) -> str:
    """Preserve a damaged database and restore the newest valid snapshot if possible."""
    ensure_layout(layout)
    if not layout.database.exists():
        return "new"
    healthy, detail = sqlite_quick_check(layout.database)
    if healthy:
        return "healthy"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    preserved = layout.data / f"angel.corrupt-{stamp}.db"
    shutil.copy2(layout.database, preserved)
    for suffix in ("-wal", "-shm"):
        sidecar = Path(str(layout.database) + suffix)
        if sidecar.exists():
            shutil.copy2(sidecar, Path(str(preserved) + suffix))
    for backup in sorted(layout.backups.glob(f"{BACKUP_PREFIX}*{BACKUP_SUFFIX}"), reverse=True):
        staging = layout.data / f".recovery-{uuid.uuid4().hex}.db"
        try:
            with zipfile.ZipFile(backup) as archive:
                with archive.open("data/angel.db") as source, staging.open("wb") as target:
                    shutil.copyfileobj(source, target)
            valid, _ = sqlite_quick_check(staging)
            if valid:
                _remove_sqlite_sidecars(layout.database)
                os.replace(staging, layout.database)
                return f"restored:{backup.name};preserved:{preserved.name}"
        except (OSError, KeyError, zipfile.BadZipFile):
            pass
        finally:
            staging.unlink(missing_ok=True)
    raise DatabaseRecoveryError(
        f"Angel preserved the damaged database as {preserved.name}, but no valid backup "
        f"could be restored. Integrity result: {detail}"
    )


class BackupService:
    def __init__(
        self,
        database: Database,
        layout: InstallationLayout,
        keep: int = 7,
    ) -> None:
        self.database = database
        self.layout = layout
        self.keep = max(3, min(30, keep))

    def create(self, reason: str = "manual") -> BackupInfo:
        healthy, detail = self.database.integrity_check()
        if not healthy:
            raise DatabaseRecoveryError(f"Backup stopped because the database is not healthy: {detail}")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        destination = self.layout.backups / f"{BACKUP_PREFIX}{stamp}.zip"
        staging = self.layout.data / f".backup-{uuid.uuid4().hex}.db"
        try:
            self.database.checkpoint()
            self.database.backup_to(staging)
            valid, result = sqlite_quick_check(staging)
            if not valid:
                raise DatabaseRecoveryError(f"Snapshot integrity check failed: {result}")
            manifest: dict[str, Any] = {
                "format": 1,
                "created_at": utc_now(),
                "reason": " ".join(reason.split())[:80] or "manual",
                "database": "data/angel.db",
                "includes": [
                    "conversations",
                    "long-term memory",
                    "projects",
                    "settings",
                    "knowledge metadata/index",
                    "creator metadata",
                ],
                "excludes": ["AI models", "cache", "generated media files"],
            }
            with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.write(staging, "data/angel.db")
                archive.writestr("manifest.json", json.dumps(manifest, indent=2))
                for config in sorted(self.layout.settings.glob("*.json")):
                    if config.is_file():
                        archive.write(config, f"data/settings/{config.name}")
            info = self._info(destination)
            self._rotate()
            return info
        finally:
            staging.unlink(missing_ok=True)

    def create_if_due(self, hours: int = 24) -> BackupInfo | None:
        backups = self.list()
        if backups:
            try:
                last = datetime.fromisoformat(backups[0].created_at)
                if datetime.now(timezone.utc) - last < timedelta(hours=max(1, hours)):
                    return None
            except ValueError:
                pass
        return self.create("automatic startup backup")

    def list(self) -> list[BackupInfo]:
        items = [
            self._info(path)
            for path in sorted(
                self.layout.backups.glob(f"{BACKUP_PREFIX}*{BACKUP_SUFFIX}"), reverse=True
            )
        ]
        return items

    def restore(self, backup_path: str | Path) -> BackupInfo:
        selected = Path(backup_path).resolve()
        backup_root = self.layout.backups.resolve()
        if selected.parent != backup_root or not selected.is_file():
            raise ValueError("Restore file must be an Angel backup from the backup directory")
        safety = self.create("automatic safety backup before restore")
        staging = self.layout.data / f".restore-{uuid.uuid4().hex}.db"
        try:
            with zipfile.ZipFile(selected) as archive:
                with archive.open("data/angel.db") as source, staging.open("wb") as target:
                    shutil.copyfileobj(source, target)
            valid, detail = sqlite_quick_check(staging)
            if not valid:
                raise DatabaseRecoveryError(f"Selected backup database is invalid: {detail}")
            self.database.checkpoint()
            _remove_sqlite_sidecars(self.layout.database)
            os.replace(staging, self.layout.database)
            return safety
        except (KeyError, zipfile.BadZipFile) as exc:
            raise DatabaseRecoveryError("Selected file is not a valid Angel backup") from exc
        finally:
            staging.unlink(missing_ok=True)

    def clear_cache(self) -> None:
        root = self.layout.root.resolve()
        target = self.layout.cache.resolve()
        if target == root or root not in target.parents:
            raise RuntimeError("Unsafe cache path refused")
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict[str, Any]:
        healthy, detail = self.database.integrity_check()
        backups = self.list()
        return {
            "database_healthy": healthy,
            "database_detail": detail,
            "last_backup": backups[0].created_at if backups else "Never",
            "backup_count": len(backups),
            "data_directory": str(self.layout.data),
            "backup_directory": str(self.layout.backups),
            "cache_directory": str(self.layout.cache),
            "cache_exists": self.layout.cache.is_dir(),
        }

    def _rotate(self) -> None:
        paths = sorted(
            self.layout.backups.glob(f"{BACKUP_PREFIX}*{BACKUP_SUFFIX}"), reverse=True
        )
        for old in paths[self.keep :]:
            old.unlink(missing_ok=True)

    @staticmethod
    def _info(path: Path) -> BackupInfo:
        created = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(
            timespec="seconds"
        )
        reason = "unknown"
        try:
            with zipfile.ZipFile(path) as archive:
                manifest = json.loads(archive.read("manifest.json"))
            reason = str(manifest.get("reason") or reason)
            created = str(manifest.get("created_at") or created)
        except (OSError, KeyError, ValueError, zipfile.BadZipFile, json.JSONDecodeError):
            pass
        return BackupInfo(str(path), path.name, path.stat().st_size, created, reason)


def _remove_sqlite_sidecars(database: Path) -> None:
    for suffix in ("-wal", "-shm"):
        try:
            Path(str(database) + suffix).unlink(missing_ok=True)
        except OSError:
            pass
