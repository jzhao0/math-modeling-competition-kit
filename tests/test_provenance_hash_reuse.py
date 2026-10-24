"""Evidence-byte read reuse within one provenance operation.

Only synthetic workspace files are used. Exact lock and verification formats
must remain identical to the old one-hash-per-reference implementation.
"""
from __future__ import annotations

import csv
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mmkit.provenance import build_claim_lock, verify_claim_lock, write_claim_lock
from mmkit.provenance import registry

HEADERS = ("claim_id", "paper_location", "producer", "input",
           "artifact", "value", "precision", "status")


def fixture(root: Path, claims: int = 20) -> Path:
    (root / "shared.bin").write_bytes(b"repeated public synthetic evidence" * 32768)
    registry_path = root / "claims.csv"
    with registry_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        writer.writeheader()
        for index in range(claims):
            writer.writerow({
                "claim_id": f"Q{index}.E", "paper_location": f"Sec. {index}",
                "producer": "shared.bin", "input": "shared.bin",
                "artifact": "shared.bin", "value": str(index),
                "precision": "1", "status": "DRAFT",
            })
    return registry_path


class SharedEvidenceDigestTests(unittest.TestCase):
    def test_one_digest_per_unchanged_file_per_operation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_file = fixture(root)
            original_hash = hashlib.sha256
            calls = []

            def count_file_hashes(*args, **kwargs):
                # _fingerprint_file calls sha256() with no initial bytes;
                # the canonical JSON fingerprint uses sha256(encoded_bytes).
                if not args and not kwargs:
                    calls.append(1)
                return original_hash(*args, **kwargs)

            with mock.patch.object(registry.hashlib, "sha256", side_effect=count_file_hashes):
                lock = build_claim_lock(root, csv_file)
            self.assertEqual(len(calls), 1)
            self.assertEqual(lock["claim_count"], 20)

            lock_path = root / "claim.lock.json"
            write_claim_lock(lock, lock_path)
            calls.clear()
            with mock.patch.object(registry.hashlib, "sha256", side_effect=count_file_hashes):
                verified = verify_claim_lock(root, csv_file, lock_path)
            self.assertEqual(len(calls), 1)
            self.assertEqual(verified["status"], "PASS")
            self.assertEqual(verified["stale_claim_count"], 0)

            # Cache must NEVER persist into a subsequent invocation.
            (root / "shared.bin").write_bytes(b"different synthetic bytes")
            calls.clear()
            with mock.patch.object(registry.hashlib, "sha256", side_effect=count_file_hashes):
                changed = verify_claim_lock(root, csv_file, lock_path)
            self.assertEqual(len(calls), 1)
            self.assertEqual(changed["status"], "STALE")
            self.assertEqual(changed["stale_claim_count"], 20)

    def test_cached_and_uncached_claim_lock_are_identical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_file = fixture(root, 8)
            cached = build_claim_lock(root, csv_file)
            original = registry._fingerprint_file

            def force_uncached(workspace, path, *, claim_id, role, cache=None):
                return original(workspace, path, claim_id=claim_id, role=role)

            with mock.patch.object(registry, "_fingerprint_file", side_effect=force_uncached):
                reference = build_claim_lock(root, csv_file)
            self.assertEqual(cached, reference)
