"""Context-resilient multi-agent coordination primitives for MMKit workspaces."""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

STATE_RELATIVE_PATH = Path("coordination") / "STATE.json"
TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")
AGENT_ID_RE = re.compile(r"^[^\s/\\\x00-\x1f]{1,96}$")

TASK_STATUSES = {
    "PROPOSED",
    "READY",
    "IN_PROGRESS",
    "VERIFYING",
    "COMPLETE",
    "BLOCKED",
    "NEEDS_ADJUDICATION",
    "SUPERSEDED",
    "ABORTED",
}
TERMINAL_STATUSES = {"COMPLETE", "SUPERSEDED", "ABORTED"}
ROLES = {"worker", "writer", "reviewer"}
MAX_EVIDENCE = 20
MAX_BLOCKERS = 10


class CoordinationError(ValueError):
    """Base error for invalid or conflicting coordination state."""


class CoordinationConflict(CoordinationError):
    """Raised when an optimistic revision or live lease conflict is detected."""


def _now(value: datetime | None = None) -> datetime:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc).replace(microsecond=0)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _root(root: str | Path) -> Path:
    path = Path(root).expanduser().resolve()
    if not path.exists() or not path.is_dir():
        raise CoordinationError(f"workspace root is not a directory: {path}")
    return path


def _state_path(root: str | Path) -> Path:
    return _root(root) / STATE_RELATIVE_PATH


def _blank_task(
    task_id: str,
    *,
    title: str,
    objective: str,
    next_action: str,
    status: str = "READY",
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    invariants: list[str] | None = None,
    acceptance: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "title": title.strip(),
        "objective": objective.strip(),
        "status": status,
        "inputs": list(inputs or []),
        "outputs": list(outputs or []),
        "invariants": list(invariants or []),
        "acceptance": list(acceptance or []),
        "evidence": [],
        "blockers": [],
        "next_action": next_action.strip(),
        "leases": {role: None for role in sorted(ROLES)},
        "failure": {"mechanism": None, "streak": 0, "last_detail": None},
        "handoff": None,
    }


def _default_state() -> dict[str, Any]:
    task = _blank_task(
        "PROBLEM_INTAKE",
        title="Preserve and inspect the official problem package",
        objective="Establish bounded source evidence and the next concrete modeling decision.",
        next_action="Read the official problem package and replace this action with one bounded next step.",
    )
    return {
        "schema_version": 1,
        "revision": 0,
        "active_task_id": "PROBLEM_INTAKE",
        "tasks": {"PROBLEM_INTAKE": task},
        "last_handoff": None,
    }


def _validate_id(value: str, *, kind: str) -> str:
    text = value.strip()
    pattern = TASK_ID_RE if kind == "task" else AGENT_ID_RE
    if not pattern.fullmatch(text):
        raise CoordinationError(f"invalid {kind} id: {value!r}")
    return text


def _validate_text(value: str, *, field: str, required: bool = True, limit: int = 4000) -> str:
    text = value.strip()
    if required and not text:
        raise CoordinationError(f"{field} must not be empty")
    if len(text) > limit:
        raise CoordinationError(f"{field} exceeds {limit} characters")
    return text


def _validate_state(state: dict[str, Any]) -> None:
    if state.get("schema_version") != 1:
        raise CoordinationError("unsupported coordination schema_version")
    if not isinstance(state.get("revision"), int) or state["revision"] < 0:
        raise CoordinationError("coordination revision must be a non-negative integer")
    tasks = state.get("tasks")
    if not isinstance(tasks, dict):
        raise CoordinationError("coordination tasks must be an object")
    active = state.get("active_task_id")
    if active is not None and active not in tasks:
        raise CoordinationError("active_task_id does not exist in tasks")

    for key, task in tasks.items():
        if task.get("task_id") != key:
            raise CoordinationError(f"task key/id mismatch: {key}")
        if task.get("status") not in TASK_STATUSES:
            raise CoordinationError(f"invalid task status for {key}: {task.get('status')}")
        leases = task.get("leases")
        if not isinstance(leases, dict) or set(leases) != ROLES:
            raise CoordinationError(f"task {key} must define worker/writer/reviewer leases")
        writer = leases.get("writer")
        reviewer = leases.get("reviewer")
        if writer and reviewer and writer.get("agent_id") == reviewer.get("agent_id"):
            raise CoordinationError(f"task {key} assigns the same agent as writer and reviewer")


def _atomic_write_json(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=".mmkit-coord-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def load_state(root: str | Path) -> dict[str, Any]:
    path = _state_path(root)
    if not path.exists():
        raise CoordinationError(f"coordination state does not exist: {path}")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CoordinationError(f"unable to read coordination state: {path}") from exc
    _validate_state(state)
    return state


def init_coordination(root: str | Path, *, force: bool = False) -> dict[str, Any]:
    path = _state_path(root)
    if path.exists():
        state = load_state(root)
        return {
            "status": "EXISTS",
            "path": str(STATE_RELATIVE_PATH).replace("\\", "/"),
            "revision": state["revision"],
            "active_task_id": state["active_task_id"],
        }

    state = _default_state()
    _atomic_write_json(path, state)
    return {
        "status": "CREATED",
        "path": str(STATE_RELATIVE_PATH).replace("\\", "/"),
        "revision": 0,
        "active_task_id": "PROBLEM_INTAKE",
    }


def _check_revision(state: dict[str, Any], expected_revision: int | None) -> None:
    if expected_revision is not None and state["revision"] != expected_revision:
        raise CoordinationConflict(
            f"stale coordination write: expected revision {expected_revision}, actual {state['revision']}"
        )


def _save(root: str | Path, state: dict[str, Any]) -> dict[str, Any]:
    _validate_state(state)
    state["revision"] += 1
    _atomic_write_json(_state_path(root), state)
    return state


def create_task(
    root: str | Path,
    task_id: str,
    *,
    title: str,
    objective: str,
    next_action: str,
    status: str = "READY",
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    invariants: list[str] | None = None,
    acceptance: list[str] | None = None,
    expected_revision: int | None = None,
) -> dict[str, Any]:
    state = load_state(root)
    _check_revision(state, expected_revision)
    task_id = _validate_id(task_id, kind="task")
    if task_id in state["tasks"]:
        raise CoordinationConflict(f"task already exists: {task_id}")
    if status not in TASK_STATUSES:
        raise CoordinationError(f"invalid task status: {status}")
    if status not in TERMINAL_STATUSES:
        _validate_text(next_action, field="next_action")

    task = _blank_task(
        task_id,
        title=_validate_text(title, field="title", limit=240),
        objective=_validate_text(objective, field="objective"),
        next_action=next_action,
        status=status,
        inputs=inputs,
        outputs=outputs,
        invariants=invariants,
        acceptance=acceptance,
    )
    state["tasks"][task_id] = task
    state["active_task_id"] = task_id
    _save(root, state)
    return {"status": "CREATED", "revision": state["revision"], "task": task}


def _lease_is_stale(lease: dict[str, Any], now: datetime) -> bool:
    return _parse_iso(lease["expires_at"]) <= now


def _live_roles(task: dict[str, Any], agent_id: str, now: datetime) -> list[str]:
    return [
        role
        for role, lease in task["leases"].items()
        if lease and lease.get("agent_id") == agent_id and not _lease_is_stale(lease, now)
    ]


def claim_role(
    root: str | Path,
    task_id: str,
    *,
    agent_id: str,
    role: str = "worker",
    lease_minutes: int = 60,
    expected_revision: int | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    state = load_state(root)
    _check_revision(state, expected_revision)
    task_id = _validate_id(task_id, kind="task")
    agent_id = _validate_id(agent_id, kind="agent")
    if role not in ROLES:
        raise CoordinationError(f"invalid role: {role}")
    if not 1 <= lease_minutes <= 1440:
        raise CoordinationError("lease_minutes must be between 1 and 1440")
    if task_id not in state["tasks"]:
        raise CoordinationError(f"unknown task: {task_id}")

    task = state["tasks"][task_id]
    if task["status"] in TERMINAL_STATUSES:
        raise CoordinationConflict(f"cannot claim terminal task: {task_id}")

    current_time = _now(now)
    current = task["leases"][role]
    if current and not _lease_is_stale(current, current_time) and current["agent_id"] != agent_id:
        raise CoordinationConflict(
            f"role {role} is held by {current['agent_id']} until {current['expires_at']}"
        )

    if role in {"writer", "reviewer"}:
        opposite = "reviewer" if role == "writer" else "writer"
        opposite_lease = task["leases"][opposite]
        if (
            opposite_lease
            and not _lease_is_stale(opposite_lease, current_time)
            and opposite_lease["agent_id"] == agent_id
        ):
            raise CoordinationConflict(
                f"agent {agent_id} cannot be both writer and reviewer for task {task_id}"
            )

    expires = current_time + timedelta(minutes=lease_minutes)
    task["leases"][role] = {
        "agent_id": agent_id,
        "claimed_at": _iso(current_time),
        "heartbeat_at": _iso(current_time),
        "expires_at": _iso(expires),
        "lease_minutes": lease_minutes,
    }
    if task["status"] in {"PROPOSED", "READY"}:
        task["status"] = "IN_PROGRESS"
    state["active_task_id"] = task_id
    _save(root, state)
    return {
        "status": "CLAIMED",
        "revision": state["revision"],
        "task_id": task_id,
        "role": role,
        "lease": task["leases"][role],
    }


def heartbeat(
    root: str | Path,
    task_id: str,
    *,
    agent_id: str,
    role: str,
    lease_minutes: int | None = None,
    expected_revision: int | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    state = load_state(root)
    _check_revision(state, expected_revision)
    if role not in ROLES:
        raise CoordinationError(f"invalid role: {role}")
    task = state["tasks"].get(task_id)
    if task is None:
        raise CoordinationError(f"unknown task: {task_id}")
    current = task["leases"].get(role)
    current_time = _now(now)
    if not current or current["agent_id"] != agent_id or _lease_is_stale(current, current_time):
        raise CoordinationConflict(f"agent {agent_id} does not hold a live {role} lease")
    minutes = lease_minutes if lease_minutes is not None else int(current["lease_minutes"])
    if not 1 <= minutes <= 1440:
        raise CoordinationError("lease_minutes must be between 1 and 1440")
    current["heartbeat_at"] = _iso(current_time)
    current["expires_at"] = _iso(current_time + timedelta(minutes=minutes))
    current["lease_minutes"] = minutes
    _save(root, state)
    return {"status": "HEARTBEAT", "revision": state["revision"], "lease": current}


def release_role(
    root: str | Path,
    task_id: str,
    *,
    agent_id: str,
    role: str,
    expected_revision: int | None = None,
) -> dict[str, Any]:
    state = load_state(root)
    _check_revision(state, expected_revision)
    if role not in ROLES:
        raise CoordinationError(f"invalid role: {role}")
    task = state["tasks"].get(task_id)
    if task is None:
        raise CoordinationError(f"unknown task: {task_id}")
    lease = task["leases"].get(role)
    if not lease or lease["agent_id"] != agent_id:
        raise CoordinationConflict(f"agent {agent_id} does not hold role {role}")
    task["leases"][role] = None
    _save(root, state)
    return {"status": "RELEASED", "revision": state["revision"], "task_id": task_id, "role": role}


def _require_live_actor(task: dict[str, Any], agent_id: str, now: datetime) -> list[str]:
    roles = _live_roles(task, agent_id, now)
    if not roles:
        raise CoordinationConflict(f"agent {agent_id} has no live lease for task {task['task_id']}")
    return roles


def checkpoint(
    root: str | Path,
    task_id: str,
    *,
    agent_id: str,
    status: str,
    next_action: str,
    evidence: list[str] | None = None,
    blockers: list[str] | None = None,
    expected_revision: int | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    state = load_state(root)
    _check_revision(state, expected_revision)
    if status not in TASK_STATUSES:
        raise CoordinationError(f"invalid task status: {status}")
    task = state["tasks"].get(task_id)
    if task is None:
        raise CoordinationError(f"unknown task: {task_id}")
    current_time = _now(now)
    _require_live_actor(task, agent_id, current_time)
    if status not in TERMINAL_STATUSES:
        _validate_text(next_action, field="next_action")
    task["status"] = status
    task["next_action"] = _validate_text(
        next_action, field="next_action", required=status not in TERMINAL_STATUSES
    )
    if evidence:
        cleaned = [_validate_text(item, field="evidence", limit=1000) for item in evidence]
        task["evidence"] = (task["evidence"] + cleaned)[-MAX_EVIDENCE:]
    if blockers:
        cleaned = [_validate_text(item, field="blocker", limit=1000) for item in blockers]
        task["blockers"] = (task["blockers"] + cleaned)[-MAX_BLOCKERS:]
    state["active_task_id"] = task_id
    _save(root, state)
    return {"status": "CHECKPOINTED", "revision": state["revision"], "task": task}


def record_failure(
    root: str | Path,
    task_id: str,
    *,
    agent_id: str,
    mechanism: str,
    detail: str,
    next_action: str,
    expected_revision: int | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    state = load_state(root)
    _check_revision(state, expected_revision)
    task = state["tasks"].get(task_id)
    if task is None:
        raise CoordinationError(f"unknown task: {task_id}")
    current_time = _now(now)
    _require_live_actor(task, agent_id, current_time)
    mechanism = _validate_text(mechanism, field="mechanism", limit=240)
    detail = _validate_text(detail, field="detail", limit=1200)
    next_action = _validate_text(next_action, field="next_action")
    failure = task["failure"]
    if failure.get("mechanism") == mechanism:
        failure["streak"] = int(failure.get("streak", 0)) + 1
    else:
        failure["mechanism"] = mechanism
        failure["streak"] = 1
    failure["last_detail"] = detail
    task["next_action"] = next_action
    circuit_open = failure["streak"] >= 2
    if circuit_open:
        task["status"] = "NEEDS_ADJUDICATION"
        blocker = f"failure circuit open for {mechanism}: {detail}"
        task["blockers"] = (task["blockers"] + [blocker])[-MAX_BLOCKERS:]
    _save(root, state)
    return {
        "status": "CIRCUIT_OPEN" if circuit_open else "FAILURE_RECORDED",
        "revision": state["revision"],
        "failure_streak": failure["streak"],
        "task_status": task["status"],
    }


def handoff(
    root: str | Path,
    task_id: str,
    *,
    agent_id: str,
    summary: str,
    next_action: str,
    to_agent: str | None = None,
    expected_revision: int | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    state = load_state(root)
    _check_revision(state, expected_revision)
    task = state["tasks"].get(task_id)
    if task is None:
        raise CoordinationError(f"unknown task: {task_id}")
    current_time = _now(now)
    held_roles = _require_live_actor(task, agent_id, current_time)
    summary = _validate_text(summary, field="summary")
    next_action = _validate_text(next_action, field="next_action")
    if to_agent is not None:
        to_agent = _validate_id(to_agent, kind="agent")

    record = {
        "task_id": task_id,
        "from_agent": agent_id,
        "to_agent": to_agent,
        "summary": summary,
        "next_action": next_action,
        "at": _iso(current_time),
        "released_roles": sorted(held_roles),
    }
    for role in held_roles:
        task["leases"][role] = None
    task["handoff"] = record
    task["next_action"] = next_action
    if task["status"] == "IN_PROGRESS":
        task["status"] = "READY"
    state["active_task_id"] = task_id
    state["last_handoff"] = record
    _save(root, state)
    result = dict(record)
    result["revision"] = state["revision"]
    result["status"] = "HANDOFF_RECORDED"
    return result


def status_report(root: str | Path, *, now: datetime | None = None) -> dict[str, Any]:
    state = load_state(root)
    current_time = _now(now)
    tasks: list[dict[str, Any]] = []
    stale_count = 0
    for task_id in sorted(state["tasks"]):
        task = state["tasks"][task_id]
        leases: dict[str, Any] = {}
        for role in sorted(ROLES):
            lease = task["leases"][role]
            if lease is None:
                leases[role] = None
                continue
            stale = _lease_is_stale(lease, current_time)
            stale_count += int(stale)
            leases[role] = {
                "agent_id": lease["agent_id"],
                "expires_at": lease["expires_at"],
                "stale": stale,
            }
        tasks.append(
            {
                "task_id": task_id,
                "title": task["title"],
                "status": task["status"],
                "next_action": task["next_action"],
                "leases": leases,
                "failure_streak": task["failure"]["streak"],
                "blocker_count": len(task["blockers"]),
            }
        )
    return {
        "schema_version": 1,
        "status": "PASS_WITH_WARNINGS" if stale_count else "PASS",
        "revision": state["revision"],
        "active_task_id": state["active_task_id"],
        "task_count": len(tasks),
        "stale_lease_count": stale_count,
        "tasks": tasks,
        "last_handoff": state.get("last_handoff"),
        "scope": "coordination freshness/ownership only; scientific correctness and human gates are not certified",
    }
