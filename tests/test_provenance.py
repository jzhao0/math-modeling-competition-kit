from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from mmkit.provenance import build_claim_lock, verify_claim_lock, write_claim_lock


HEADERS = [
    "claim_id",
    "paper_location",
    "producer",
    "input",
    "artifact",
    "value",
    "precision",
    "status",
]


class ProvenanceTests(unittest.TestCase):
    def _workspace(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "solve.py").write_text("print('ok')\n", encoding="utf-8")
        (root / "input.csv").write_text("x\n1\n", encoding="utf-8")
        (root / "result.json").write_text('{"objective": 12.34}\n', encoding="utf-8")
        registry = root / "claims.csv"
        self._write_registry(
            registry,
            [
                {
                    "claim_id": "Q1.OBJ",
                    "paper_location": "Sec. 4.1",
                    "producer": "solve.py",
                    "input": "input.csv",
                    "artifact": "result.json",
                    "value": "12.34",
                    "precision": "0.01",
                    "status": "APPROVED",
                }
            ],
        )
        return td, root, registry

    def _write_registry(self, path: Path, rows):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=HEADERS)
            writer.writeheader()
            writer.writerows(rows)

    def test_lock_and_verify_pass(self):
        td, root, registry = self._workspace()
        self.addCleanup(td.cleanup)
        lock = build_claim_lock(root, registry)
        lock_path = root / "claim.lock.json"
        write_claim_lock(lock, lock_path)

        report = verify_claim_lock(root, registry, lock_path)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["proof_level"], "MACHINE_VERIFIED")
        self.assertEqual(report["stale_claim_count"], 0)

    def test_evidence_change_marks_stale(self):
        td, root, registry = self._workspace()
        self.addCleanup(td.cleanup)
        lock_path = root / "claim.lock.json"
        write_claim_lock(build_claim_lock(root, registry), lock_path)

        (root / "result.json").write_text('{"objective": 99}\n', encoding="utf-8")
        report = verify_claim_lock(root, registry, lock_path)

        self.assertEqual(report["status"], "STALE")
        self.assertEqual(report["stale_claim_count"], 1)
        self.assertTrue(any(x["kind"] == "evidence_fingerprint_changed" for x in report["findings"]))

    def test_claim_semantic_change_marks_stale(self):
        td, root, registry = self._workspace()
        self.addCleanup(td.cleanup)
        lock_path = root / "claim.lock.json"
        write_claim_lock(build_claim_lock(root, registry), lock_path)

        self._write_registry(
            registry,
            [
                {
                    "claim_id": "Q1.OBJ",
                    "paper_location": "Sec. 4.1",
                    "producer": "solve.py",
                    "input": "input.csv",
                    "artifact": "result.json",
                    "value": "12.35",
                    "precision": "0.01",
                    "status": "APPROVED",
                }
            ],
        )
        report = verify_claim_lock(root, registry, lock_path)
        self.assertEqual(report["status"], "STALE")
        self.assertTrue(any(x["kind"] == "claim_semantics_changed" for x in report["findings"]))

    def test_unbound_new_claim_marks_stale(self):
        td, root, registry = self._workspace()
        self.addCleanup(td.cleanup)
        lock_path = root / "claim.lock.json"
        write_claim_lock(build_claim_lock(root, registry), lock_path)

        rows = [
            {
                "claim_id": "Q1.OBJ",
                "paper_location": "Sec. 4.1",
                "producer": "solve.py",
                "input": "input.csv",
                "artifact": "result.json",
                "value": "12.34",
                "precision": "0.01",
                "status": "APPROVED",
            },
            {
                "claim_id": "Q1.COST",
                "paper_location": "Sec. 4.2",
                "producer": "solve.py",
                "input": "input.csv",
                "artifact": "result.json",
                "value": "10",
                "precision": "1",
                "status": "DRAFT",
            },
        ]
        self._write_registry(registry, rows)
        report = verify_claim_lock(root, registry, lock_path)

        self.assertEqual(report["status"], "STALE")
        self.assertTrue(any(x["kind"] == "claim_unbound" for x in report["findings"]))

    def test_rejects_parent_escape(self):
        td, root, registry = self._workspace()
        self.addCleanup(td.cleanup)
        self._write_registry(
            registry,
            [
                {
                    "claim_id": "Q1.BAD",
                    "paper_location": "Sec. 1",
                    "producer": "",
                    "input": "",
                    "artifact": "../outside.json",
                    "value": "1",
                    "precision": "",
                    "status": "DRAFT",
                }
            ],
        )
        with self.assertRaises(ValueError):
            build_claim_lock(root, registry)

    def test_rejects_generic_pass_claim_state(self):
        td, root, registry = self._workspace()
        self.addCleanup(td.cleanup)
        self._write_registry(
            registry,
            [
                {
                    "claim_id": "Q1.BAD",
                    "paper_location": "Sec. 1",
                    "producer": "",
                    "input": "",
                    "artifact": "result.json",
                    "value": "1",
                    "precision": "",
                    "status": "PASS",
                }
            ],
        )
        with self.assertRaises(ValueError):
            build_claim_lock(root, registry)


if __name__ == "__main__":
    unittest.main()
