from pathlib import Path
from angel_platform.execution import SafeExecutor, ExecutionPolicy


def test_execution_requires_approval(tmp_path: Path):
    executor = SafeExecutor(tmp_path / "workspaces", ExecutionPolicy(timeout_seconds=3))
    workspace = executor.workspaces.create("test")
    result = executor.run(["python", "-c", "print('ok')"], workspace, approved=False)
    assert result.blocked
    assert not result.succeeded


def test_execution_runs_inside_workspace(tmp_path: Path):
    executor = SafeExecutor(tmp_path / "workspaces", ExecutionPolicy(timeout_seconds=3))
    workspace = executor.workspaces.create("test")
    result = executor.run(["python", "-c", "print('ok')"], workspace, approved=True)
    assert result.succeeded
    assert "ok" in result.stdout


def test_execution_blocks_outside_workspace(tmp_path: Path):
    executor = SafeExecutor(tmp_path / "workspaces", ExecutionPolicy(timeout_seconds=3))
    result = executor.run(["python", "-c", "print('ok')"], tmp_path, approved=True)
    assert result.blocked
