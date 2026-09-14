from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mmkit.benchmark import (
    BenchmarkError,
    build_baseline,
    compare_to_baseline,
    run_benchmark,
    validate_benchmark_manifest,
)


class BenchmarkTests(unittest.TestCase):
    def _workspace(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / "scripts").mkdir()
        (root / "results").mkdir()
        (root / "scripts" / "bench.py").write_text(
            "from pathlib import Path\n"
            "p=Path('results/value.txt')\n"
            "p.parent.mkdir(parents=True, exist_ok=True)\n"
            "p.write_text('42\\n', encoding='utf-8')\n",
            encoding="utf-8",
        )
        return temp, root

    def _manifest(self) -> dict:
        return {
            "schema_version": 1,
            "name": "stable-bench",
            "argv": ["${PYTHON}", "scripts/bench.py"],
            "cwd": ".",
            "timeout_seconds": 10,
            "warmup_runs": 1,
            "measured_runs": 3,
            "expected_outputs": ["results/value.txt"],
            "require_stable_outputs": True,
        }

    def test_run_benchmark_passes_and_records_stats(self) -> None:
        temp, root = self._workspace()
        self.addCleanup(temp.cleanup)
        report = run_benchmark(root, self._manifest())
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["statistics"]["count"], 3)
        self.assertTrue(report["output_stable"])
        self.assertEqual(report["output_artifacts"][0]["path"], "results/value.txt")
        self.assertEqual(len(report["runs"]), 3)

    def test_parent_escape_rejected(self) -> None:
        manifest = self._manifest()
        manifest["cwd"] = "../escape"
        with self.assertRaises(BenchmarkError):
            validate_benchmark_manifest(manifest)

    def test_unstable_outputs_block(self) -> None:
        temp, root = self._workspace()
        self.addCleanup(temp.cleanup)
        (root / "scripts" / "bench.py").write_text(
            "from pathlib import Path\n"
            "p=Path('results/value.txt')\n"
            "old=p.read_text(encoding='utf-8') if p.exists() else ''\n"
            "p.write_text(old+'x', encoding='utf-8')\n",
            encoding="utf-8",
        )
        manifest = self._manifest()
        manifest["warmup_runs"] = 0
        report = run_benchmark(root, manifest)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any(x["kind"] == "output_identity_unstable" for x in report["findings"]))

    def test_baseline_compare_passes_same_report(self) -> None:
        temp, root = self._workspace()
        self.addCleanup(temp.cleanup)
        report = run_benchmark(root, self._manifest())
        baseline = build_baseline(report, max_regression_percent=100.0)
        comparison = compare_to_baseline(report, baseline)
        self.assertEqual(comparison["status"], "PASS")

    def test_runtime_regression_blocks(self) -> None:
        temp, root = self._workspace()
        self.addCleanup(temp.cleanup)
        report = run_benchmark(root, self._manifest())
        baseline = build_baseline(report, max_regression_percent=5.0)
        slower = json.loads(json.dumps(report))
        slower["statistics"]["median_seconds"] = baseline["baseline_median_seconds"] * 1.50
        comparison = compare_to_baseline(slower, baseline)
        self.assertEqual(comparison["status"], "FAIL")
        self.assertTrue(any(x["kind"] == "runtime_regression" for x in comparison["findings"]))

    def test_output_identity_change_blocks(self) -> None:
        temp, root = self._workspace()
        self.addCleanup(temp.cleanup)
        report = run_benchmark(root, self._manifest())
        baseline = build_baseline(report, max_regression_percent=100.0)
        changed = json.loads(json.dumps(report))
        changed["output_artifacts"][0]["sha256"] = "0" * 64
        comparison = compare_to_baseline(changed, baseline)
        self.assertEqual(comparison["status"], "FAIL")
        self.assertTrue(any(x["kind"] == "output_identity_changed" for x in comparison["findings"]))

    def test_environment_mismatch_warns_by_default(self) -> None:
        temp, root = self._workspace()
        self.addCleanup(temp.cleanup)
        report = run_benchmark(root, self._manifest())
        baseline = build_baseline(report, max_regression_percent=100.0)
        changed = json.loads(json.dumps(report))
        changed["environment"]["machine"] = "DIFFERENT"
        comparison = compare_to_baseline(changed, baseline)
        self.assertEqual(comparison["status"], "PASS_WITH_WARNINGS")

    def test_same_environment_can_be_required(self) -> None:
        temp, root = self._workspace()
        self.addCleanup(temp.cleanup)
        report = run_benchmark(root, self._manifest())
        baseline = build_baseline(
            report, max_regression_percent=100.0, require_same_environment=True
        )
        changed = json.loads(json.dumps(report))
        changed["environment"]["machine"] = "DIFFERENT"
        comparison = compare_to_baseline(changed, baseline)
        self.assertEqual(comparison["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
