from __future__ import annotations

import platform
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .backups import BackupService
from .creator import ModelRouter
from .database import Database
from .local_ai import LocalAIManager
from .paths import InstallationLayout
from .settings import SettingsService


BUILD_ID = "2026.08.16-local-first"


def format_bytes(value: int) -> str:
    size = float(max(0, value))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return str(value)


class DiagnosticsService:
    def __init__(
        self,
        database: Database,
        settings: SettingsService,
        layout: InstallationLayout,
        backups: BackupService,
        local_ai: LocalAIManager,
        router: ModelRouter,
        log_path: Path,
    ) -> None:
        self.database = database
        self.settings = settings
        self.layout = layout
        self.backups = backups
        self.local_ai = local_ai
        self.router = router
        self.log_path = log_path

    def collect(self, probe_external: bool = True) -> dict[str, Any]:
        current = self.settings.get()
        ai = self.local_ai.status(current.ollama_url, current.model)
        protection = self.backups.status()
        models = [str(item.get("name") or "") for item in ai.models]
        capabilities = self.router.statuses(
            ai.running and ai.configured_model_installed, models
        )
        internet = "BLOCKED BY OFFLINE MODE"
        if current.connectivity_mode != "Offline":
            internet = "ONLINE" if probe_external and self._internet_online() else "OFFLINE / NOT VERIFIED"
        hardware = ai.hardware
        return {
            "build": BUILD_ID,
            "windows": platform.platform(),
            "database": "Healthy" if protection["database_healthy"] else protection["database_detail"],
            "data_directory": str(self.layout.data),
            "backup_directory": str(self.layout.backups),
            "last_backup": protection["last_backup"],
            "backup_count": protection["backup_count"],
            "cache": "Present and safe to delete" if self.layout.cache.is_dir() else "Missing; will be recreated",
            "connectivity_mode": current.connectivity_mode,
            "internet": internet,
            "ollama_installed": ai.installed,
            "ollama_running": ai.running,
            "ollama_executable": ai.executable,
            "active_chat_model": current.model,
            "configured_model_ready": ai.configured_model_installed,
            "installed_models": models,
            "model_storage": ai.model_storage,
            "model_storage_size": format_bytes(ai.model_storage_bytes),
            "cpu": hardware.cpu,
            "cpu_threads": hardware.cpu_threads,
            "ram": format_bytes(hardware.ram_bytes),
            "gpu": hardware.gpu,
            "vram": format_bytes(hardware.vram_bytes),
            "free_disk": format_bytes(hardware.free_disk_bytes),
            "capabilities": [status.__dict__ for status in capabilities],
            "localhost_services": {
                "Ollama": ai.running,
                "ComfyUI": next((item.installed for item in capabilities if item.role == "Image AI"), False),
                "ACE-Step": next((item.installed for item in capabilities if item.role == "Music AI"), False),
            },
            "recent_errors": self._recent_errors(),
        }

    def report(self, probe_external: bool = True) -> str:
        data = self.collect(probe_external)
        capability_lines = "\n".join(
            f"  {item['role']}: {'READY' if item['installed'] else 'NOT INSTALLED'} "
            f"({item['backend']}; {item['model'] or 'no model selected'})"
            for item in data.pop("capabilities")
        )
        service_lines = "\n".join(
            f"  {name}: {'READY' if ready else 'OFFLINE'}"
            for name, ready in data.pop("localhost_services").items()
        )
        errors = data.pop("recent_errors")
        lines = ["ANGEL DIAGNOSTIC REPORT (non-sensitive)"]
        lines.extend(f"{key.replace('_', ' ').title()}: {value}" for key, value in data.items())
        lines.append("Capabilities:\n" + capability_lines)
        lines.append("Localhost Services:\n" + service_lines)
        lines.append("Recent Errors:\n" + ("\n".join(f"  {line}" for line in errors) if errors else "  None recorded"))
        return "\n".join(lines)

    def _recent_errors(self) -> list[str]:
        try:
            lines = self.log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return []
        return [line[:500] for line in lines if " ERROR " in line or " CRITICAL " in line][-12:]

    @staticmethod
    def _internet_online() -> bool:
        request = urllib.request.Request(
            "https://www.bing.com/favicon.ico",
            method="HEAD",
            headers={"User-Agent": "Angel Local Personal AI/Windows"},
        )
        try:
            with urllib.request.urlopen(request, timeout=3):
                return True
        except (urllib.error.URLError, OSError, TimeoutError):
            return False
