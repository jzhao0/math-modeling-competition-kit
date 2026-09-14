from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mmkit.cli import main


class BenchmarkCliTests(unittest.TestCase):
    def test_run_lock_compare_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "workspace"
            (root / "scripts").mkdir(parents=True)
            (root / "results").mkdir()
            (root / "config").mkdir()
            (root / "scripts" / "bench.py").write_text(
                "from pathlib import Path\n"
                "p=Path('results/value.txt')\n"
                "p.write_text('fixed\\n', encoding='utf-8')\n",
                encoding="utf-8",
            )
            manifest = {
                "schema_version": 1,
                "name": "cli-bench",
                "argv": ["${PYTHON}", "scripts/bench.py"],
                "cwd": ".",
                "timeout_seconds": 10,
                "warmup_runs": 0,
                "measured_runs": 2,
                "expected_outputs": ["results/value.txt"],
                "require_stable_outputs": True,
            }
            manifest_path = root / "config" / "benchmark.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            report = root / "results" / "benchmark.json"
            baseline = root / "results" / "baseline.json"
            comparison = root / "results" / "comparison.json"

            self.assertEqual(
                main(["benchmark", "run", str(root), "config/benchmark.json", "--json", str(report)]),
                0,
            )
            self.assertEqual(
                main([
                    "benchmark", "lock", str(report), "--output", str(baseline),
                    "--max-regression-percent", "1000",
                ]),
                0,
            )
            self.assertEqual(
                main([
                    "benchmark", "compare", str(report), str(baseline),
                    "--json", str(comparison),
                ]),
                0,
            )
            result = json.loads(comparison.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "PASS")

    def test_lock_requires_explicit_threshold(self) -> None:
        with self.assertRaises(SystemExit):
            main(["benchmark", "lock", "missing.json", "--output", "baseline.json"])


if __name__ == "__main__":
    unittest.main()
