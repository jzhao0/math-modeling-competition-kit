from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from mmkit.cli import main


class CoordinationCliTests(unittest.TestCase):
    def test_coord_task_claim_checkpoint_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "workspace"
            root.mkdir()
            self.assertEqual(main(["coord", "init", str(root)]), 0)
            self.assertEqual(
                main([
                    "coord", "task", str(root), "T1",
                    "--title", "Bounded task",
                    "--objective", "Do one thing.",
                    "--next-action", "Claim it.",
                    "--expect-revision", "0",
                ]),
                0,
            )
            self.assertEqual(
                main([
                    "coord", "claim", str(root), "T1",
                    "--agent", "agent-a", "--role", "writer",
                    "--expect-revision", "1",
                ]),
                0,
            )
            self.assertEqual(
                main([
                    "coord", "checkpoint", str(root), "T1",
                    "--agent", "agent-a", "--status", "VERIFYING",
                    "--next-action", "Have a different agent review.",
                    "--evidence", "unit-test-pass",
                    "--expect-revision", "2",
                ]),
                0,
            )
            self.assertEqual(
                main([
                    "coord", "handoff", str(root), "T1",
                    "--agent", "agent-a",
                    "--summary", "Implementation is ready for independent review.",
                    "--next-action", "Reviewer claims reviewer role.",
                    "--to-agent", "agent-b",
                    "--expect-revision", "3",
                ]),
                0,
            )
            state = json.loads((root / "coordination" / "STATE.json").read_text(encoding="utf-8"))
            self.assertEqual(state["revision"], 4)
            self.assertIsNone(state["tasks"]["T1"]["leases"]["writer"])
            self.assertEqual(state["last_handoff"]["to_agent"], "agent-b")

    def test_stale_cli_revision_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "workspace"
            root.mkdir()
            main(["coord", "init", str(root)])
            main([
                "coord", "task", str(root), "T1",
                "--title", "Task", "--objective", "Objective",
                "--next-action", "Next", "--expect-revision", "0",
            ])
            output = StringIO()
            with redirect_stdout(output):
                code = main([
                    "coord", "task", str(root), "T2",
                    "--title", "Stale", "--objective", "Must fail",
                    "--next-action", "Stop", "--expect-revision", "0",
                ])
            self.assertEqual(code, 2)
            self.assertIn("stale coordination write", output.getvalue())


if __name__ == "__main__":
    unittest.main()
