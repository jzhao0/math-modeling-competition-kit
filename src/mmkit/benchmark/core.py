"""Post-model-freeze algorithm/runtime benchmarking for MMKit."""

from __future__ import annotations

import hashlib
import json
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path, PurePosixPath
from typing import Any


MAX_RUNS = 50
MAX_WARMUPS = 10
MAX_TIMEOUT_SECONDS = 24 * 60 * 60


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class BenchmarkError(ValueError):
    """Raised when a benchmark contract or result is invalid."""


def _safe_relative(value: str, *, field: str) -> PurePosixPath:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or any(part == ".." for part in path.parts):
        raise BenchmarkError(f"{field} must stay inside the workspace: {value}")
    return path


def _root(root: str | Path) -> Path:
    path = Path(root).expanduser().resolve()
    if not path.exists() or not path.is_dir():
        raise BenchmarkError(f"workspace root is not a directory: {path}")
    return path


def _resolve_inside(root: Path, rel: PurePosixPath, *, field: str) -> Path:
    candidate = root.joinpath(*rel.parts).resolve()
    if not candidate.is_relative_to(root):
        raise BenchmarkError(f"{field} escaped workspace: {rel.as_posix()}")
    return candidate


def _expand_argv(argv: list[str]) -> list[str]:
    return [sys.executable if item == "${PYTHON}" else item for item in argv]


def _tail(value: str, limit: int = 1200) -> str:
    return value[-limit:]


def _semantic_sha256(data: Any) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _environment_signature() -> dict[str, str]:
    return {
        "system": platform.system(),
        "machine": platform.machine(),
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
    }


def _load_json(path: str | Path, *, label: str) -> dict[str, Any]:
    file_path = Path(path)
    try:
        data = json.loads(file_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BenchmarkError(f"unable to read {label}: {file_path}") from exc
    if not isinstance(data, dict):
        raise BenchmarkError(f"{label} must be a JSON object")
    return data


def _manifest_from(root: Path, manifest: str | Path | dict[str, Any]) -> dict[str, Any]:
    if isinstance(manifest, dict):
        data = manifest
    else:
        path = Path(manifest)
        if not path.is_absolute():
            path = root / path
        data = _load_json(path, label="benchmark manifest")
    validate_benchmark_manifest(data)
    return data


def init_benchmark(root: str | Path, *, force: bool = False) -> dict[str, Any]:
    """Seed a portable benchmark contract without overwriting user files."""

    workspace = _root(root)
    seeds = {
        "config/benchmark.json": json.dumps(
            {
                "schema_version": 1,
                "name": "scaffold-runtime-smoke",
                "argv": ["${PYTHON}", "scripts/benchmark_smoke.py"],
                "cwd": ".",
                "timeout_seconds": 30,
                "warmup_runs": 1,
                "measured_runs": 3,
                "expected_outputs": ["results/benchmark_smoke.txt"],
                "require_stable_outputs": True,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n",
        "scripts/benchmark_smoke.py": (
            "from pathlib import Path\n\n"
            "value = sum(i * i for i in range(10000))\n"
            "output = Path('results/benchmark_smoke.txt')\n"
            "output.parent.mkdir(parents=True, exist_ok=True)\n"
            "output.write_text(f'{value}\\n', encoding='utf-8')\n"
        ),
    }

    created: list[str] = []
    existing: list[str] = []
    for relpath, content in seeds.items():
        target = workspace.joinpath(*PurePosixPath(relpath).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if not target.is_file():
                raise BenchmarkError(f"benchmark seed path exists but is not a file: {relpath}")
            existing.append(relpath)
            continue
        target.write_text(content, encoding="utf-8", newline="\n")
        created.append(relpath)

    return {
        "schema_version": 1,
        "status": "PASS",
        "created_files": created,
        "existing_files": existing,
        "overwrite_policy": "existing files are never overwritten",
    }


def validate_benchmark_manifest(data: dict[str, Any]) -> None:
    if data.get("schema_version") != 1:
        raise BenchmarkError("benchmark manifest schema_version must be 1")

    name = data.get("name")
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 120:
        raise BenchmarkError("benchmark manifest name must be a non-empty string up to 120 characters")

    argv = data.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
        raise BenchmarkError("benchmark argv must be a non-empty string list")

    _safe_relative(str(data.get("cwd", ".")), field="benchmark cwd")

    timeout = data.get("timeout_seconds", 300)
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
        raise BenchmarkError("timeout_seconds must be positive")
    if float(timeout) > MAX_TIMEOUT_SECONDS:
        raise BenchmarkError(f"timeout_seconds must be <= {MAX_TIMEOUT_SECONDS}")

    warmups = data.get("warmup_runs", 1)
    measured = data.get("measured_runs", 5)
    if not isinstance(warmups, int) or isinstance(warmups, bool) or not 0 <= warmups <= MAX_WARMUPS:
        raise BenchmarkError(f"warmup_runs must be an integer between 0 and {MAX_WARMUPS}")
    if not isinstance(measured, int) or isinstance(measured, bool) or not 1 <= measured <= MAX_RUNS:
        raise BenchmarkError(f"measured_runs must be an integer between 1 and {MAX_RUNS}")

    outputs = data.get("expected_outputs", [])
    if not isinstance(outputs, list) or not all(isinstance(x, str) and x for x in outputs):
        raise BenchmarkError("expected_outputs must be a string list")
    if len(set(outputs)) != len(outputs):
        raise BenchmarkError("expected_outputs must not contain duplicates")
    for output in outputs:
        _safe_relative(output, field="expected output")

    stable = data.get("require_stable_outputs", True)
    if not isinstance(stable, bool):
        raise BenchmarkError("require_stable_outputs must be boolean")


def _fingerprint_outputs(root: Path, outputs: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    artifacts: list[dict[str, Any]] = []
    missing: list[str] = []
    for output in outputs:
        rel = _safe_relative(output, field="expected output")
        candidate = _resolve_inside(root, rel, field="expected output")
        if not candidate.exists():
            missing.append(rel.as_posix())
            continue
        if candidate.is_symlink():
            raise BenchmarkError(f"expected output may not be a symlink: {rel.as_posix()}")
        if not candidate.is_file():
            raise BenchmarkError(f"expected output must be a file: {rel.as_posix()}")
        artifacts.append(
            {
                "path": rel.as_posix(),
                "size": candidate.stat().st_size,
                "sha256": _hash_file(candidate),
            }
        )
    return artifacts, missing


def _run_once(
    workspace: Path,
    *,
    argv: list[str],
    cwd: Path,
    timeout_seconds: float,
    expected_outputs: list[str],
    phase: str,
    index: int,
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            _expand_argv(argv),
            cwd=cwd,
            shell=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
        elapsed = time.perf_counter() - started
        returncode = completed.returncode
        error = None
        stdout_tail = _tail(completed.stdout)
        stderr_tail = _tail(completed.stderr)
    except subprocess.TimeoutExpired as exc:
        elapsed = time.perf_counter() - started
        returncode = None
        error = f"timeout after {timeout_seconds:g} seconds"
        stdout_tail = _tail((exc.stdout or "") if isinstance(exc.stdout, str) else "")
        stderr_tail = _tail((exc.stderr or "") if isinstance(exc.stderr, str) else "")

    artifacts: list[dict[str, Any]] = []
    missing: list[str] = []
    if returncode == 0 and error is None:
        artifacts, missing = _fingerprint_outputs(workspace, expected_outputs)

    status = "PASS" if returncode == 0 and error is None and not missing else "FAIL"
    return {
        "phase": phase,
        "index": index,
        "status": status,
        "duration_seconds": round(elapsed, 9),
        "returncode": returncode,
        "error": error,
        "missing_outputs": missing,
        "output_artifacts": artifacts,
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
    }


def run_benchmark(
    root: str | Path,
    manifest: str | Path | dict[str, Any],
) -> dict[str, Any]:
    """Execute one benchmark contract with warmups and measured repetitions.

    The command is always executed with ``shell=False``. Runtime measurements are
    wall-clock observations for this host/run; they are not deterministic truth.
    """

    workspace = _root(root)
    data = _manifest_from(workspace, manifest)
    cwd_rel = _safe_relative(str(data.get("cwd", ".")), field="benchmark cwd")
    cwd = _resolve_inside(workspace, cwd_rel, field="benchmark cwd")
    if not cwd.is_dir():
        raise BenchmarkError(f"benchmark cwd does not exist: {cwd_rel.as_posix()}")

    expected_outputs = list(data.get("expected_outputs", []))
    argv = list(data["argv"])
    timeout = float(data.get("timeout_seconds", 300))
    warmup_runs = int(data.get("warmup_runs", 1))
    measured_runs = int(data.get("measured_runs", 5))
    require_stable_outputs = bool(data.get("require_stable_outputs", True))

    warmups: list[dict[str, Any]] = []
    for index in range(1, warmup_runs + 1):
        item = _run_once(
            workspace,
            argv=argv,
            cwd=cwd,
            timeout_seconds=timeout,
            expected_outputs=expected_outputs,
            phase="warmup",
            index=index,
        )
        warmups.append(item)
        if item["status"] != "PASS":
            return {
                "schema_version": 1,
                "status": "FAIL",
                "proof_level": "MACHINE_MEASURED",
                "scope": "engineering runtime/output identity only; scientific correctness is not certified",
                "name": data["name"],
                "manifest_sha256": _semantic_sha256(data),
                "manifest": data,
                "environment": _environment_signature(),
                "warmups": warmups,
                "runs": [],
                "statistics": None,
                "output_stable": None,
                "output_artifacts": [],
                "findings": [
                    {
                        "severity": "BLOCKER",
                        "kind": "warmup_failed",
                        "detail": f"warmup run {index} failed",
                    }
                ],
            }

    runs: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []
    for index in range(1, measured_runs + 1):
        item = _run_once(
            workspace,
            argv=argv,
            cwd=cwd,
            timeout_seconds=timeout,
            expected_outputs=expected_outputs,
            phase="measured",
            index=index,
        )
        runs.append(item)
        if item["status"] != "PASS":
            findings.append(
                {
                    "severity": "BLOCKER",
                    "kind": "measured_run_failed",
                    "detail": f"measured run {index} failed",
                }
            )
            break

    successful = [item for item in runs if item["status"] == "PASS"]
    durations = [float(item["duration_seconds"]) for item in successful]
    stats: dict[str, Any] | None = None
    if durations:
        stats = {
            "count": len(durations),
            "min_seconds": round(min(durations), 9),
            "max_seconds": round(max(durations), 9),
            "mean_seconds": round(statistics.fmean(durations), 9),
            "median_seconds": round(statistics.median(durations), 9),
            "pstdev_seconds": round(statistics.pstdev(durations), 9),
        }

    fingerprints = [_semantic_sha256(item["output_artifacts"]) for item in successful]
    output_stable = len(set(fingerprints)) <= 1 if fingerprints else True
    if require_stable_outputs and not output_stable:
        findings.append(
            {
                "severity": "BLOCKER",
                "kind": "output_identity_unstable",
                "detail": "expected output fingerprints changed across measured runs",
            }
        )

    if not expected_outputs:
        findings.append(
            {
                "severity": "WARNING",
                "kind": "no_expected_outputs",
                "detail": "runtime was measured without output-identity evidence",
            }
        )

    status = "FAIL" if any(item["severity"] == "BLOCKER" for item in findings) else (
        "PASS_WITH_WARNINGS" if findings else "PASS"
    )
    final_artifacts = successful[-1]["output_artifacts"] if successful else []

    return {
        "schema_version": 1,
        "status": status,
        "proof_level": "MACHINE_MEASURED",
        "scope": "engineering runtime/output identity only; scientific correctness is not certified",
        "measurement_note": (
            "wall-clock timings are host/run observations and may vary with hardware, OS, load, "
            "runtime versions, solver versions, and cache state"
        ),
        "name": data["name"],
        "manifest_sha256": _semantic_sha256(data),
        "manifest": data,
        "environment": _environment_signature(),
        "warmups": warmups,
        "runs": runs,
        "statistics": stats,
        "output_stable": output_stable,
        "output_artifacts": final_artifacts,
        "findings": findings,
    }


def write_json(data: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def build_baseline(
    report: dict[str, Any],
    *,
    max_regression_percent: float,
    compare_output_identity: bool = True,
    require_same_environment: bool = False,
) -> dict[str, Any]:
    if report.get("schema_version") != 1 or report.get("proof_level") != "MACHINE_MEASURED":
        raise BenchmarkError("benchmark report schema/proof_level is not supported")
    if report.get("status") not in {"PASS", "PASS_WITH_WARNINGS"}:
        raise BenchmarkError("baseline can only be locked from a passing benchmark report")
    stats = report.get("statistics")
    if not isinstance(stats, dict) or not isinstance(stats.get("median_seconds"), (int, float)):
        raise BenchmarkError("benchmark report has no median runtime")
    if not isinstance(max_regression_percent, (int, float)) or isinstance(max_regression_percent, bool):
        raise BenchmarkError("max_regression_percent must be numeric")
    if max_regression_percent < 0 or max_regression_percent > 10000:
        raise BenchmarkError("max_regression_percent must be between 0 and 10000")
    if compare_output_identity and not report.get("output_artifacts"):
        raise BenchmarkError("cannot require output identity without expected output artifacts")

    return {
        "schema_version": 1,
        "benchmark_name": report["name"],
        "manifest_sha256": report["manifest_sha256"],
        "baseline_median_seconds": float(stats["median_seconds"]),
        "baseline_mean_seconds": float(stats["mean_seconds"]),
        "measured_runs": int(stats["count"]),
        "max_regression_percent": float(max_regression_percent),
        "compare_output_identity": bool(compare_output_identity),
        "require_same_environment": bool(require_same_environment),
        "environment": dict(report["environment"]),
        "output_artifacts": list(report["output_artifacts"]),
        "source_report_sha256": _semantic_sha256(report),
        "scope": "runtime regression and output identity only; scientific correctness is not certified",
    }


def load_baseline(path: str | Path) -> dict[str, Any]:
    data = _load_json(path, label="benchmark baseline")
    if data.get("schema_version") != 1:
        raise BenchmarkError("benchmark baseline schema_version must be 1")
    required = {
        "benchmark_name",
        "manifest_sha256",
        "baseline_median_seconds",
        "max_regression_percent",
        "compare_output_identity",
        "require_same_environment",
        "environment",
        "output_artifacts",
    }
    missing = sorted(required - set(data))
    if missing:
        raise BenchmarkError(f"benchmark baseline missing fields: {', '.join(missing)}")
    return data


def compare_to_baseline(
    report: dict[str, Any],
    baseline: dict[str, Any],
) -> dict[str, Any]:
    if report.get("status") not in {"PASS", "PASS_WITH_WARNINGS"}:
        raise BenchmarkError("only passing benchmark reports can be compared")
    if baseline.get("schema_version") != 1:
        raise BenchmarkError("benchmark baseline schema_version must be 1")

    findings: list[dict[str, Any]] = []

    if report.get("name") != baseline.get("benchmark_name"):
        findings.append(
            {
                "severity": "BLOCKER",
                "kind": "benchmark_name_changed",
                "detail": f"current={report.get('name')!r} baseline={baseline.get('benchmark_name')!r}",
            }
        )

    if report.get("manifest_sha256") != baseline.get("manifest_sha256"):
        findings.append(
            {
                "severity": "BLOCKER",
                "kind": "benchmark_contract_changed",
                "detail": "benchmark manifest semantics differ from the locked baseline",
            }
        )

    stats = report.get("statistics") or {}
    current_median = stats.get("median_seconds")
    baseline_median = baseline.get("baseline_median_seconds")
    regression_percent: float | None = None
    if not isinstance(current_median, (int, float)) or not isinstance(baseline_median, (int, float)):
        findings.append(
            {
                "severity": "BLOCKER",
                "kind": "runtime_statistic_missing",
                "detail": "current or baseline median runtime is missing",
            }
        )
    elif baseline_median <= 0:
        findings.append(
            {
                "severity": "BLOCKER",
                "kind": "invalid_baseline_runtime",
                "detail": "baseline median runtime must be positive",
            }
        )
    else:
        regression_percent = ((float(current_median) / float(baseline_median)) - 1.0) * 100.0
        threshold = float(baseline["max_regression_percent"])
        if regression_percent > threshold:
            findings.append(
                {
                    "severity": "BLOCKER",
                    "kind": "runtime_regression",
                    "detail": (
                        f"median runtime regression {regression_percent:.3f}% exceeds "
                        f"locked threshold {threshold:.3f}%"
                    ),
                }
            )

    if bool(baseline.get("compare_output_identity")):
        if report.get("output_artifacts") != baseline.get("output_artifacts"):
            findings.append(
                {
                    "severity": "BLOCKER",
                    "kind": "output_identity_changed",
                    "detail": "current expected output fingerprints differ from the locked baseline",
                }
            )

    environment_matches = report.get("environment") == baseline.get("environment")
    if not environment_matches:
        findings.append(
            {
                "severity": "BLOCKER" if baseline.get("require_same_environment") else "WARNING",
                "kind": "environment_changed",
                "detail": "runtime environment differs from the baseline environment",
            }
        )

    blockers = sum(1 for item in findings if item["severity"] == "BLOCKER")
    warnings = sum(1 for item in findings if item["severity"] == "WARNING")
    status = "FAIL" if blockers else ("PASS_WITH_WARNINGS" if warnings else "PASS")

    return {
        "schema_version": 1,
        "status": status,
        "proof_level": "MACHINE_COMPARED",
        "scope": "runtime regression and output identity only; scientific correctness is not certified",
        "benchmark_name": report.get("name"),
        "manifest_sha256": report.get("manifest_sha256"),
        "baseline_median_seconds": baseline_median,
        "current_median_seconds": current_median,
        "runtime_regression_percent": (
            round(regression_percent, 6) if regression_percent is not None else None
        ),
        "max_regression_percent": baseline.get("max_regression_percent"),
        "environment_matches": environment_matches,
        "output_identity_compared": bool(baseline.get("compare_output_identity")),
        "findings": findings,
        "blocker_count": blockers,
        "warning_count": warnings,
    }
