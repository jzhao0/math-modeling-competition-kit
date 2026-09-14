"""Command-line interface for the MMKit engineering MVP."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mmkit.provenance import build_claim_lock, verify_claim_lock, write_claim_lock
from mmkit.reproducibility import build_manifest, run_clean_room, write_manifest
from mmkit.submission.gate import audit_submission


def _write_json(data: dict, path: str | None) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mmkit", description="MMKit competition-engineering CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    manifest = sub.add_parser("manifest", help="build a deterministic SHA-256 workspace manifest")
    manifest.add_argument("root")
    manifest.add_argument("--output", required=True)

    reproduce = sub.add_parser("reproduce", help="run a workspace in a bounded clean room")
    reproduce.add_argument("root")
    reproduce.add_argument("run_manifest")
    reproduce.add_argument("--json", dest="json_path")
    reproduce.add_argument("--retain", action="store_true")

    audit = sub.add_parser("audit", help="run the generic final-submission engineering gate")
    audit.add_argument("submission_dir")
    audit.add_argument("--require", action="append", default=[])
    audit.add_argument("--json", dest="json_path")
    audit.add_argument("--no-text-scan", action="store_true")
    audit.add_argument("--no-zip-scan", action="store_true")

    provenance = sub.add_parser("provenance", help="lock or verify claim/evidence provenance")
    provenance_sub = provenance.add_subparsers(dest="provenance_command", required=True)

    provenance_lock = provenance_sub.add_parser(
        "lock", help="bind claim rows to exact evidence file fingerprints"
    )
    provenance_lock.add_argument("root")
    provenance_lock.add_argument("registry")
    provenance_lock.add_argument("--output", required=True)

    provenance_verify = provenance_sub.add_parser(
        "verify", help="detect stale claims after registry or evidence changes"
    )
    provenance_verify.add_argument("root")
    provenance_verify.add_argument("registry")
    provenance_verify.add_argument("lock")
    provenance_verify.add_argument("--json", dest="json_path")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.command == "manifest":
        manifest = build_manifest(args.root)
        write_manifest(manifest, args.output)
        print(f"MANIFEST: PASS files={manifest['file_count']} output={args.output}")
        return 0

    if args.command == "reproduce":
        report = run_clean_room(args.root, args.run_manifest, retain=args.retain)
        _write_json(report, args.json_path)
        print(f"REPRODUCE: {report['status']} commands={len(report['commands'])}")
        return 0 if report["status"] == "PASS" else 2

    if args.command == "provenance":
        if args.provenance_command == "lock":
            lock = build_claim_lock(args.root, args.registry)
            write_claim_lock(lock, args.output)
            print(f"PROVENANCE LOCK: PASS claims={lock['claim_count']} output={args.output}")
            return 0

        report = verify_claim_lock(args.root, args.registry, args.lock)
        _write_json(report, args.json_path)
        print(
            f"PROVENANCE VERIFY: {report['status']} "
            f"claims={report['claim_count']} stale={report['stale_claim_count']}"
        )
        return 0 if report["status"] == "PASS" else 2

    report = audit_submission(
        args.submission_dir,
        required=args.require,
        scan_text=not args.no_text_scan,
        inspect_zips=not args.no_zip_scan,
    )
    _write_json(report, args.json_path)
    blockers = sum(1 for item in report["findings"] if item["severity"] == "BLOCKER")
    print(f"AUDIT: {report['status']} blockers={blockers} artifacts={report.get('artifact_count', 0)}")
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
