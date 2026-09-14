from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from mmkit.cli import main


class ProvenanceCliTests(unittest.TestCase):
    def test_lock_then_stale_verify_exit_codes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "result.txt").write_text("42\n", encoding="utf-8")
            registry = root / "claims.csv"
            with registry.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "claim_id",
                        "paper_location",
                        "producer",
                        "input",
                        "artifact",
                        "value",
                        "precision",
                        "status",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "claim_id": "C1",
                        "paper_location": "Sec. 1",
                        "producer": "",
                        "input": "",
                        "artifact": "result.txt",
                        "value": "42",
                        "precision": "1",
                        "status": "APPROVED",
                    }
                )

            lock_path = root / "claims.lock.json"
            self.assertEqual(
                main(
                    [
                        "provenance",
                        "lock",
                        str(root),
                        str(registry),
                        "--output",
                        str(lock_path),
                    ]
                ),
                0,
            )

            self.assertEqual(
                main(
                    [
                        "provenance",
                        "verify",
                        str(root),
                        str(registry),
                        str(lock_path),
                    ]
                ),
                0,
            )

            (root / "result.txt").write_text("43\n", encoding="utf-8")
            self.assertEqual(
                main(
                    [
                        "provenance",
                        "verify",
                        str(root),
                        str(registry),
                        str(lock_path),
                    ]
                ),
                2,
            )


if __name__ == "__main__":
    unittest.main()
