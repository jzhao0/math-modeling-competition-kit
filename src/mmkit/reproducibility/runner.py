"""Bounded clean-room command execution for reproducibility checks."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath
from typing import Any

DEFAULT_COPY_IGNORES = (".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache")


def _safe_relative(value: str, *, field: str) -> PurePosixPath:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or any(part == ".." for part in path.parts):
        raise ValueError(f"{field} must stay inside the workspace: {value}")
    return path


def validate_run_manifest(data: dict[str, Any]) -> None:
    if data.get("schema_version") != 1:
        raise ValueError("run manifest schema_version must be 1")
    commands = data.get("commands")
    if not isinstance(commands, list) or not commands:
        raise ValueError("run manifest must contain a non-empty commands list")

    for index, command in enumerate(commands):
        if not isinstance(command, dict):
            raise ValueError(f"command {index} must be an object")
        argv = command.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
            raise ValueError(f"command {index} argv must be a non-empty string list")
        _safe_relative(str(command.get("cwd", ".")), field=f"command {index} cwd")
        timeout = command.get("timeout_seconds", 300)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError(f"command {index} timeout_seconds must be positive")
        outputs = command.get("expected_outputs", [])
        if not isinstance(outputs, list) or not all(isinstance(x, str) and x for x in outputs):
            raise ValueError(f"command {index} expected_outputs must be a string list")
        for output in outputs:
            _safe_relative(output, field=f"command {index} expected output")


def _expand_argv(argv: list[str]) -> list[str]:
    return [sys.executable if item == "${PYTHON}" else item for item in argv]


def _tail(value: str, limit: int = 4000) -> str:
    return value[-limit:]


def run_clean_room(
    source_root: Path | str,
    run_manifest: Path | str | dict[str, Any],
    *,
    retain: bool = False,
) -> dict[str, Any]:
    """Copy a workspace to a temporary directory and execute declared commands.

    Commands are executed with ``shell=False``. The manifest may use the
    portable ``${PYTHON}`` token for the current Python interpreter.
    """
    source = Path(source_root).resolve()
    if not source.is_dir():
        raise ValueError(f"source_root must be a directory: {source}")

    if isinstance(run_manifest, dict):
        data = run_manifest
    else:
        data = json.loads(Path(run_manifest).read_text(encoding="utf-8-sig"))
    validate_run_manifest(data)

    for path in source.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"clean-room source contains symlink: {path.relative_to(source)}")

    temp_parent = Path(tempfile.mkdtemp(prefix="mmkit-cleanroom-"))
    workspace = temp_parent / "workspace"
    shutil.copytree(
        source,
        workspace,
        ignore=shutil.ignore_patterns(*DEFAULT_COPY_IGNORES),
        symlinks=False,
    )

    results: list[dict[str, Any]] = []
    overall = "PASS"

    try:
        for index, command in enumerate(data["commands"]):
            name = str(command.get("name") or f"command_{index + 1}")
            cwd_rel = _safe_relative(str(command.get("cwd", ".")), field=f"{name} cwd")
            cwd = workspace.joinpath(*cwd_rel.parts).resolve()
            if workspace not in (cwd, *cwd.parents):
                raise ValueError(f"command cwd escaped workspace: {cwd_rel}")
            if not cwd.is_dir():
                raise ValueError(f"command cwd does not exist: {cwd_rel}")

            argv = _expand_argv(list(command["argv"]))
            started = time.monotonic()
            try:
                completed = subprocess.run(
                    argv,
                    cwd=cwd,
                    shell=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=float(command.get("timeout_seconds", 300)),
                    check=False,
                )
                returncode = completed.returncode
                error = None
                stdout_tail = _tail(completed.stdout)
                stderr_tail = _tail(completed.stderr)
            except subprocess.TimeoutExpired as exc:
                returncode = None
                error = f"timeout after {command.get('timeout_seconds', 300)} seconds"
                stdout_tail = _tail((exc.stdout or "") if isinstance(exc.stdout, str) else "")
                stderr_tail = _tail((exc.stderr or "") if isinstance(exc.stderr, str) else "")
            duration = round(time.monotonic() - started, 6)

            missing_outputs: list[str] = []
            for output in command.get("expected_outputs", []):
                rel = _safe_relative(output, field=f"{name} expected output")
                candidate = workspace.joinpath(*rel.parts)
                if not candidate.exists():
                    missing_outputs.append(rel.as_posix())

            status = "PASS" if returncode == 0 and not missing_outputs and error is None else "FAIL"
            if status == "FAIL":
                overall = "FAIL"

            results.append(
                {
                    "name": name,
                    "argv": command["argv"],
                    "cwd": cwd_rel.as_posix(),
                    "returncode": returncode,
                    "duration_seconds": duration,
                    "missing_outputs": missing_outputs,
                    "stdout_tail": stdout_tail,
                    "stderr_tail": stderr_tail,
                    "error": error,
                    "status": status,
                }
            )

            if status == "FAIL" and bool(data.get("stop_on_failure", True)):
                break

        report: dict[str, Any] = {
            "schema_version": 1,
            "status": overall,
            "proof_level": "MACHINE_VERIFIED",
            "commands": results,
        }
        if retain:
            report["retained_clean_room"] = str(workspace)
        return report
    finally:
        if not retain:
            shutil.rmtree(temp_parent, ignore_errors=True)
