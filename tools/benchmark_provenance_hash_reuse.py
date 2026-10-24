"""Offline synthetic claim-lock benchmark; no private contest inputs.

From repo root:
    PYTHONPATH=src python tools/benchmark_provenance_hash_reuse.py
"""
from __future__ import annotations

import csv
import statistics
import tempfile
import time
from pathlib import Path
from unittest import mock

from mmkit.provenance import build_claim_lock
from mmkit.provenance import registry


def median_seconds(task, repeats: int = 3) -> float:
    timings = []
    for _ in range(repeats):
        started = time.perf_counter()
        task()
        timings.append(time.perf_counter() - started)
    return statistics.median(timings)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Same input referenced by many independent synthetic claims/roles.
        (root / "shared.dat").write_bytes(b"synthetic-verifiable-bytes-" * 40000)
        registry_csv = root / "claims.csv"
        headers = ["claim_id", "paper_location", "producer", "input",
                   "artifact", "value", "precision", "status"]
        claim_count = 80
        with registry_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            for i in range(claim_count):
                writer.writerow({
                    "claim_id": f"Q{i}.X", "paper_location": f"Sec. {i}",
                    "producer": "shared.dat", "input": "shared.dat",
                    "artifact": "shared.dat", "value": str(i),
                    "precision": "1", "status": "DRAFT",
                })

        original = registry._fingerprint_file

        def no_cache(workspace, path, *, claim_id, role, cache=None):
            return original(workspace, path, claim_id=claim_id, role=role)

        expected = None
        with mock.patch.object(registry, "_fingerprint_file", side_effect=no_cache):
            expected = build_claim_lock(root, registry_csv)
            before = median_seconds(lambda: build_claim_lock(root, registry_csv))
        actual = build_claim_lock(root, registry_csv)
        assert expected == actual
        after = median_seconds(lambda: build_claim_lock(root, registry_csv))
        print("claims,references,uncached_seconds,cached_seconds,speedup,equivalent")
        print(f"{claim_count},{claim_count*3},{before:.6f},{after:.6f},{before/after:.2f},true")


if __name__ == "__main__":
    main()
