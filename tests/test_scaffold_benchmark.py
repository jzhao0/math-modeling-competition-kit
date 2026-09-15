from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mmkit.benchmark import run_benchmark, validate_benchmark_manifest
from mmkit.scaffold import init_project


class ScaffoldBenchmarkIntegrationTests(unittest.TestCase):
    def test_new_project_has_runnable_benchmark_seed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "contest"
            report = init_project(root, competition="MCM", year=2027)
            self.assertEqual(report["benchmark"]["status"], "PASS")
            manifest_path = root / "config" / "benchmark.json"
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            validate_benchmark_manifest(data)
            benchmark = run_benchmark(root, "config/benchmark.json")
            self.assertEqual(benchmark["status"], "PASS")
            self.assertTrue(benchmark["output_stable"])

    def test_force_preserves_existing_benchmark_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "contest"
            root.mkdir()
            config = root / "config"
            config.mkdir()
            custom = config / "benchmark.json"
            custom.write_text('{"custom": true}\n', encoding="utf-8")
            report = init_project(root, competition="CUMCM", year=2027, force=True)
            self.assertIn("config/benchmark.json", report["benchmark"]["existing_files"])
            self.assertEqual(custom.read_text(encoding="utf-8"), '{"custom": true}\n')


if __name__ == "__main__":
    unittest.main()
