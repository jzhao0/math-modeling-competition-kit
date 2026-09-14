from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from mmkit.coordination import (
    CoordinationConflict,
    checkpoint,
    claim_role,
    create_task,
    handoff,
    heartbeat,
    init_coordination,
    load_state,
    record_failure,
    status_report,
)

T0 = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)


class CoordinationTests(unittest.TestCase):
    def make_root(self, temp: str) -> Path:
        root = Path(temp) / "workspace"
        root.mkdir()
        init_coordination(root)
        return root

    def test_init_and_revision_guard(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_root(temp)
            self.assertEqual(load_state(root)["revision"], 0)
            report = create_task(
                root,
                "T1",
                title="Build baseline",
                objective="Produce a bounded baseline.",
                next_action="Run baseline.",
                expected_revision=0,
            )
            self.assertEqual(report["revision"], 1)
            with self.assertRaises(CoordinationConflict):
                create_task(
                    root,
                    "T2",
                    title="Stale writer",
                    objective="Must fail.",
                    next_action="Do not run.",
                    expected_revision=0,
                )

    def test_live_role_conflict_and_stale_takeover(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_root(temp)
            claim_role(root, "PROBLEM_INTAKE", agent_id="agent-a", role="worker", now=T0, lease_minutes=10)
            with self.assertRaises(CoordinationConflict):
                claim_role(
                    root,
                    "PROBLEM_INTAKE",
                    agent_id="agent-b",
                    role="worker",
                    now=T0 + timedelta(minutes=5),
                )
            takeover = claim_role(
                root,
                "PROBLEM_INTAKE",
                agent_id="agent-b",
                role="worker",
                now=T0 + timedelta(minutes=11),
            )
            self.assertEqual(takeover["lease"]["agent_id"], "agent-b")

    def test_writer_reviewer_separation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_root(temp)
            claim_role(root, "PROBLEM_INTAKE", agent_id="agent-a", role="writer", now=T0)
            with self.assertRaises(CoordinationConflict):
                claim_role(root, "PROBLEM_INTAKE", agent_id="agent-a", role="reviewer", now=T0)
            claim_role(root, "PROBLEM_INTAKE", agent_id="agent-b", role="reviewer", now=T0)
            state = load_state(root)
            self.assertEqual(state["tasks"]["PROBLEM_INTAKE"]["leases"]["reviewer"]["agent_id"], "agent-b")

    def test_heartbeat_refreshes_lease(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_root(temp)
            claim_role(root, "PROBLEM_INTAKE", agent_id="agent-a", role="worker", now=T0, lease_minutes=10)
            report = heartbeat(
                root,
                "PROBLEM_INTAKE",
                agent_id="agent-a",
                role="worker",
                now=T0 + timedelta(minutes=8),
                lease_minutes=20,
            )
            self.assertEqual(report["lease"]["expires_at"], "2026-09-14T12:28:00Z")

    def test_two_failure_circuit_breaker(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_root(temp)
            claim_role(root, "PROBLEM_INTAKE", agent_id="agent-a", role="worker", now=T0)
            first = record_failure(
                root,
                "PROBLEM_INTAKE",
                agent_id="agent-a",
                mechanism="latex-build",
                detail="first deterministic failure",
                next_action="Inspect the log once.",
                now=T0,
            )
            self.assertEqual(first["status"], "FAILURE_RECORDED")
            second = record_failure(
                root,
                "PROBLEM_INTAKE",
                agent_id="agent-a",
                mechanism="latex-build",
                detail="same mechanism failed again",
                next_action="Stop and request adjudication.",
                now=T0,
            )
            self.assertEqual(second["status"], "CIRCUIT_OPEN")
            self.assertEqual(second["task_status"], "NEEDS_ADJUDICATION")
            self.assertEqual(second["failure_streak"], 2)

    def test_checkpoint_requires_live_lease(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_root(temp)
            with self.assertRaises(CoordinationConflict):
                checkpoint(
                    root,
                    "PROBLEM_INTAKE",
                    agent_id="agent-a",
                    status="IN_PROGRESS",
                    next_action="Continue.",
                    now=T0,
                )

    def test_handoff_is_compact_and_releases_actor_roles(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_root(temp)
            claim_role(root, "PROBLEM_INTAKE", agent_id="agent-a", role="worker", now=T0)
            report = handoff(
                root,
                "PROBLEM_INTAKE",
                agent_id="agent-a",
                to_agent="agent-b",
                summary="Problem files preserved; next decision is bounded.",
                next_action="Compare two candidate model routes.",
                now=T0,
            )
            self.assertEqual(report["status"], "HANDOFF_RECORDED")
            state = load_state(root)
            task = state["tasks"]["PROBLEM_INTAKE"]
            self.assertIsNone(task["leases"]["worker"])
            self.assertEqual(task["status"], "READY")
            self.assertEqual(state["last_handoff"]["to_agent"], "agent-b")

    def test_status_reports_stale_lease_without_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_root(temp)
            claim_role(root, "PROBLEM_INTAKE", agent_id="agent-a", role="worker", now=T0, lease_minutes=5)
            revision = load_state(root)["revision"]
            report = status_report(root, now=T0 + timedelta(minutes=6))
            self.assertEqual(report["status"], "PASS_WITH_WARNINGS")
            self.assertEqual(report["stale_lease_count"], 1)
            self.assertEqual(load_state(root)["revision"], revision)


if __name__ == "__main__":
    unittest.main()
