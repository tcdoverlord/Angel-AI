from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import time
import uuid


@dataclass(frozen=True)
class ExecutionPolicy:
    timeout_seconds: int = 30
    max_output_chars: int = 12000
    allow_network: bool = False
    require_confirmation: bool = True
    allowed_interpreters: tuple[str, ...] = ("python", "python3", "py", "pwsh", "powershell")


@dataclass
class ExecutionResult:
    execution_id: str
    command: list[str]
    workspace: str
    return_code: int | None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    blocked: bool = False
    duration_seconds: float = 0.0
    notes: list[str] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return self.return_code == 0 and not self.timed_out and not self.blocked


class IsolatedWorkspace:
    """Creates disposable build/run workspaces beneath the application data folder."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, label: str = "run") -> Path:
        safe = "".join(ch for ch in label if ch.isalnum() or ch in "-_")[:40] or "run"
        path = Path(tempfile.mkdtemp(prefix=f"{safe}-", dir=self.root))
        return path.resolve()

    def is_inside(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.root)
            return True
        except ValueError:
            return False


class SafeExecutor:
    """Conservative subprocess runner for AI-requested work.

    It never invokes a shell, restricts the working directory to an Angel workspace,
    enforces a timeout/output cap, and requires the caller to explicitly approve
    operations that are not read-only.
    """

    def __init__(self, workspace_root: Path, policy: ExecutionPolicy | None = None):
        self.policy = policy or ExecutionPolicy()
        self.workspaces = IsolatedWorkspace(workspace_root)

    def run(self, command: list[str], workspace: Path, approved: bool = False) -> ExecutionResult:
        execution_id = uuid.uuid4().hex[:12]
        workspace = workspace.resolve()
        started = time.monotonic()
        result = ExecutionResult(execution_id, list(command), str(workspace), None)

        if not command or command[0] not in self.policy.allowed_interpreters:
            result.blocked = True
            result.notes.append("Blocked: interpreter is not on the approved allowlist.")
            return result
        if not self.workspaces.is_inside(workspace):
            result.blocked = True
            result.notes.append("Blocked: workspace is outside Angel's isolated workspace root.")
            return result
        if self.policy.require_confirmation and not approved:
            result.blocked = True
            result.notes.append("Blocked: explicit execution approval is required.")
            return result
        if not workspace.exists() or not workspace.is_dir():
            result.blocked = True
            result.notes.append("Blocked: workspace does not exist.")
            return result

        env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUNBUFFERED": "1",
        }
        try:
            completed = subprocess.run(
                command,
                cwd=workspace,
                env=env,
                shell=False,
                capture_output=True,
                text=True,
                timeout=max(1, self.policy.timeout_seconds),
                check=False,
            )
            result.return_code = completed.returncode
            result.stdout = completed.stdout[: self.policy.max_output_chars]
            result.stderr = completed.stderr[: self.policy.max_output_chars]
            if len(completed.stdout) > self.policy.max_output_chars or len(completed.stderr) > self.policy.max_output_chars:
                result.notes.append("Output was truncated by the execution limit.")
        except subprocess.TimeoutExpired as exc:
            result.timed_out = True
            result.stdout = (exc.stdout or "")[: self.policy.max_output_chars] if isinstance(exc.stdout, str) else ""
            result.stderr = (exc.stderr or "")[: self.policy.max_output_chars] if isinstance(exc.stderr, str) else ""
            result.notes.append(f"Timed out after {self.policy.timeout_seconds} seconds.")
        except OSError as exc:
            result.stderr = str(exc)
            result.notes.append("The process could not be started.")
        finally:
            result.duration_seconds = round(time.monotonic() - started, 3)
        return result


def create_workspace(root: Path, label: str = "build") -> Path:
    return IsolatedWorkspace(root).create(label)
