from __future__ import annotations

import ctypes
import json
import logging
import os
import platform
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .ollama_client import OllamaClient, OllamaError


@dataclass(frozen=True)
class HardwareInfo:
    cpu: str
    cpu_threads: int
    ram_bytes: int
    gpu: str
    vram_bytes: int
    free_disk_bytes: int


@dataclass(frozen=True)
class LocalAIStatus:
    installed: bool
    executable: str
    running: bool
    configured_model: str
    configured_model_installed: bool
    models: list[dict[str, Any]]
    model_storage: str
    model_storage_bytes: int
    hardware: HardwareInfo
    message: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class _MemoryStatus(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


class LocalAIManager:
    def __init__(self, client: OllamaClient, logger: logging.Logger | None = None) -> None:
        self.client = client
        self.logger = logger or logging.getLogger("angel.local_ai")

    def find_ollama(self) -> Path | None:
        candidates = [
            shutil.which("ollama.exe"),
            shutil.which("ollama"),
            str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"),
            str(Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Ollama" / "ollama.exe"),
        ]
        for candidate in candidates:
            if candidate and Path(candidate).is_file():
                return Path(candidate).resolve()
        return None

    def status(self, base_url: str, configured_model: str) -> LocalAIStatus:
        executable = self.find_ollama()
        running = False
        models: list[dict[str, Any]] = []
        try:
            models = self.client.list_model_details(base_url)
            running = True
        except OllamaError:
            pass
        names = {
            str(model.get("name") or model.get("model") or "").strip()
            for model in models
        }
        storage = self.model_storage_path()
        return LocalAIStatus(
            installed=executable is not None,
            executable=str(executable or ""),
            running=running,
            configured_model=configured_model,
            configured_model_installed=configured_model in names,
            models=[self._model_summary(model) for model in models],
            model_storage=str(storage),
            model_storage_bytes=self._directory_size(storage, maximum_files=50_000),
            hardware=self.hardware_info(),
            message=self._status_message(executable is not None, running, configured_model in names),
        )

    def ensure_running(self, base_url: str, wait_seconds: float = 10.0) -> tuple[bool, str]:
        online, _ = self.client.check(base_url)
        if online:
            return True, "Ollama is already running"
        executable = self.find_ollama()
        if executable is None:
            return False, "Ollama is not installed"
        if not self.client.is_local_url(base_url):
            return False, "Automatic start is available only for a localhost Ollama URL"
        creation_flags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            subprocess.Popen(
                [str(executable), "serve"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags,
            )
        except OSError as exc:
            self.logger.warning("Could not start Ollama: %s", exc)
            return False, f"Ollama could not start: {exc}"
        deadline = time.monotonic() + max(2.0, wait_seconds)
        while time.monotonic() < deadline:
            online, _ = self.client.check(base_url)
            if online:
                return True, "Ollama started and connected"
            time.sleep(0.4)
        return False, "Ollama was started, but its local service did not become ready in time"

    def restart(self, base_url: str) -> tuple[bool, str]:
        executable = self.find_ollama()
        if executable is None:
            return False, "Ollama is not installed"
        if not self.client.is_local_url(base_url):
            return False, "Restart is available only for localhost Ollama"
        creation_flags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            subprocess.run(
                ["taskkill.exe", "/IM", "ollama.exe", "/T", "/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
                creationflags=creation_flags,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            self.logger.exception("Ollama restart stop phase failed")
        time.sleep(0.5)
        return self.ensure_running(base_url)

    def test_inference(self, base_url: str, model: str) -> tuple[bool, str]:
        try:
            response = self.client.chat(
                base_url,
                model,
                [
                    {"role": "system", "content": "Reply with exactly ANGEL_LOCAL_OK."},
                    {"role": "user", "content": "Local inference test."},
                ],
            )
        except OllamaError as exc:
            return False, str(exc)
        return bool(response.strip()), f"Local inference succeeded with {model}"

    def model_recommendation(self, model_name: str, ram_bytes: int) -> str:
        lowered = model_name.lower()
        match = re.search(r"(?<!\d)(\d+(?:\.\d+)?)b(?!\w)", lowered)
        billions = float(match.group(1)) if match else 0.0
        ram_gb = ram_bytes / (1024**3)
        if billions and ram_gb and billions * 1.1 > ram_gb:
            return "NOT RECOMMENDED"
        if billions <= 4 or any(word in lowered for word in ("mini", "small", "tiny")):
            return "SAFE"
        if billions <= 9:
            return "RECOMMENDED"
        return "HEAVY"

    def model_storage_path(self) -> Path:
        configured = os.environ.get("OLLAMA_MODELS", "").strip()
        if configured:
            return Path(configured).expanduser().resolve()
        return Path.home() / ".ollama" / "models"

    def hardware_info(self) -> HardwareInfo:
        ram = 0
        try:
            status = _MemoryStatus()
            status.dwLength = ctypes.sizeof(_MemoryStatus)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                ram = int(status.ullTotalPhys)
        except (AttributeError, OSError):
            pass
        disk_root = Path(__file__).resolve().anchor or "C:\\"
        try:
            free_disk = int(shutil.disk_usage(disk_root).free)
        except OSError:
            free_disk = 0
        gpu, vram = self._gpu_info()
        return HardwareInfo(
            cpu=platform.processor() or platform.machine() or "Unknown CPU",
            cpu_threads=os.cpu_count() or 1,
            ram_bytes=ram,
            gpu=gpu,
            vram_bytes=vram,
            free_disk_bytes=free_disk,
        )

    def _gpu_info(self) -> tuple[str, int]:
        powershell = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
        if not powershell.is_file():
            return "Not detected", 0
        script = (
            "Get-CimInstance Win32_VideoController | "
            "Select-Object Name,AdapterRAM | ConvertTo-Json -Compress"
        )
        try:
            completed = subprocess.run(
                [str(powershell), "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
                creationflags=int(getattr(subprocess, "CREATE_NO_WINDOW", 0)),
                check=False,
            )
            payload = json.loads(completed.stdout or "null")
            entries = payload if isinstance(payload, list) else [payload] if isinstance(payload, dict) else []
            names = [str(item.get("Name") or "").strip() for item in entries if item.get("Name")]
            vram = max((int(item.get("AdapterRAM") or 0) for item in entries), default=0)
            return ", ".join(names) or "Not detected", vram
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError, ValueError):
            return "Not detected", 0

    @staticmethod
    def _model_summary(model: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": str(model.get("name") or model.get("model") or "Unknown"),
            "size": int(model.get("size") or 0),
            "modified_at": str(model.get("modified_at") or ""),
            "details": dict(model.get("details") or {}) if isinstance(model.get("details"), dict) else {},
        }

    @staticmethod
    def _directory_size(path: Path, maximum_files: int) -> int:
        if not path.is_dir():
            return 0
        total = 0
        count = 0
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    total += item.stat().st_size
                    count += 1
                    if count >= maximum_files:
                        break
        except OSError:
            pass
        return total

    @staticmethod
    def _status_message(installed: bool, running: bool, model_ready: bool) -> str:
        if not installed:
            return "Ollama is not installed"
        if not running:
            return "Ollama is installed but not running"
        if not model_ready:
            return "Ollama is running, but the configured chat model is not installed"
        return "Angel Local AI is ready"
