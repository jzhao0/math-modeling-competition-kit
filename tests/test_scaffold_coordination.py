from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mmkit.coordination import load_state
from mmkit.scaffold import init_project


class ScaffoldCoordinationIntegrationTests(unittest.TestCase):
    def test_new_project_has_machine_readable_coordination_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "contest"
            report = init_project(root, competition="MCM", year=2027)
            self.assertEqual(report["coordination"]["status"], "CREATED")
            state = load_state(root)
            self.assertEqual(state["active_task_id"], "PROBLEM_INTAKE")
            self.assertEqual(state["revision"], 0)

    def test_force_preserves_existing_coordination_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "contest"
            init_project(root, competition="MCM", year=2027)
            state_path = root / "coordination" / "STATE.json"
            original = state_path.read_text(encoding="utf-8")
            report = init_project(root, competition="MCM", year=2027, force=True)
            self.assertEqual(report["coordination"]["status"], "EXISTS")
            self.assertEqual(state_path.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
