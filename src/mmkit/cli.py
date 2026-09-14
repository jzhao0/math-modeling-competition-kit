"""Command-line interface for the MMKit engineering MVP."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mmkit.coordination import (
    CoordinationError,
    checkpoint,
    claim_role,
    create_task,
    handoff,
    heartbeat,
    init_coordination,
    record_failure,
    release_role,
    status_report,
)
from mmkit.paper import audit_paper, build_paper, init_paper
from mmkit.provenance import build_claim_lock, verify_claim_lock, write_claim_lock
from mmkit.reproducibility import build_manifest, run_clean_room, write_manifest
from mmkit.scaffold import init_project
from mmkit.submission.gate import audit_submission


def _write_json(data: dict, path: str | None) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def _add_revision_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--expect-revision", type=int, dest="expected_revision")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mmkit", description="MMKit competition-engineering CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create a generic competition project workspace")
    init.add_argument("destination")
    init.add_argument("--competition", required=True)
    init.add_argument("--year", required=True, type=int)
    init.add_argument("--name", dest="project_name")
    init.add_argument(
        "--force",
        action="store_true",
        help="fill missing scaffold files in a non-empty destination without overwriting existing files",
    )
    init.add_argument("--json", dest="json_path")

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

    paper = sub.add_parser("paper", help="initialize, audit, or build paper sources")
    paper_sub = paper.add_subparsers(dest="paper_command", required=True)

    paper_init = paper_sub.add_parser(
        "init", help="seed generic paper-pipeline files without overwriting user content"
    )
    paper_init.add_argument("root")
    paper_init.add_argument("--force", action="store_true")
    paper_init.add_argument("--json", dest="json_path")

    paper_audit = paper_sub.add_parser(
        "audit", help="audit a LaTeX source graph, figures, citations, and bibliography"
    )
    paper_audit.add_argument("root")
    paper_audit.add_argument("main_tex")
    paper_audit.add_argument("--json", dest="json_path")

    paper_build = paper_sub.add_parser(
        "build", help="audit then run one bounded shell-free paper build command"
    )
    paper_build.add_argument("root")
    paper_build.add_argument("build_manifest")
    paper_build.add_argument("--json", dest="json_path")

    coord = sub.add_parser("coord", help="manage context-resilient multi-agent task state")
    coord_sub = coord.add_subparsers(dest="coord_command", required=True)

    coord_init = coord_sub.add_parser("init", help="create coordination/STATE.json if missing")
    coord_init.add_argument("root")
    coord_init.add_argument("--json", dest="json_path")

    coord_task = coord_sub.add_parser("task", help="create and activate a bounded task")
    coord_task.add_argument("root")
    coord_task.add_argument("task_id")
    coord_task.add_argument("--title", required=True)
    coord_task.add_argument("--objective", required=True)
    coord_task.add_argument("--next-action", required=True)
    coord_task.add_argument("--status", default="READY")
    coord_task.add_argument("--input", action="append", default=[])
    coord_task.add_argument("--output", action="append", default=[])
    coord_task.add_argument("--invariant", action="append", default=[])
    coord_task.add_argument("--acceptance", action="append", default=[])
    _add_revision_argument(coord_task)
    coord_task.add_argument("--json", dest="json_path")

    coord_claim = coord_sub.add_parser("claim", help="claim or refresh one task role lease")
    coord_claim.add_argument("root")
    coord_claim.add_argument("task_id")
    coord_claim.add_argument("--agent", required=True)
    coord_claim.add_argument("--role", choices=["worker", "writer", "reviewer"], default="worker")
    coord_claim.add_argument("--lease-minutes", type=int, default=60)
    _add_revision_argument(coord_claim)
    coord_claim.add_argument("--json", dest="json_path")

    coord_heartbeat = coord_sub.add_parser("heartbeat", help="refresh a live role lease")
    coord_heartbeat.add_argument("root")
    coord_heartbeat.add_argument("task_id")
    coord_heartbeat.add_argument("--agent", required=True)
    coord_heartbeat.add_argument("--role", choices=["worker", "writer", "reviewer"], required=True)
    coord_heartbeat.add_argument("--lease-minutes", type=int)
    _add_revision_argument(coord_heartbeat)
    coord_heartbeat.add_argument("--json", dest="json_path")

    coord_release = coord_sub.add_parser("release", help="release a role lease")
    coord_release.add_argument("root")
    coord_release.add_argument("task_id")
    coord_release.add_argument("--agent", required=True)
    coord_release.add_argument("--role", choices=["worker", "writer", "reviewer"], required=True)
    _add_revision_argument(coord_release)
    coord_release.add_argument("--json", dest="json_path")

    coord_checkpoint = coord_sub.add_parser("checkpoint", help="write compact current task state")
    coord_checkpoint.add_argument("root")
    coord_checkpoint.add_argument("task_id")
    coord_checkpoint.add_argument("--agent", required=True)
    coord_checkpoint.add_argument("--status", required=True)
    coord_checkpoint.add_argument("--next-action", required=True)
    coord_checkpoint.add_argument("--evidence", action="append", default=[])
    coord_checkpoint.add_argument("--blocker", action="append", default=[])
    _add_revision_argument(coord_checkpoint)
    coord_checkpoint.add_argument("--json", dest="json_path")

    coord_fail = coord_sub.add_parser(
        "fail", help="record a mechanism failure and open the circuit on the second consecutive failure"
    )
    coord_fail.add_argument("root")
    coord_fail.add_argument("task_id")
    coord_fail.add_argument("--agent", required=True)
    coord_fail.add_argument("--mechanism", required=True)
    coord_fail.add_argument("--detail", required=True)
    coord_fail.add_argument("--next-action", required=True)
    _add_revision_argument(coord_fail)
    coord_fail.add_argument("--json", dest="json_path")

    coord_handoff = coord_sub.add_parser("handoff", help="record compact takeover state and release actor roles")
    coord_handoff.add_argument("root")
    coord_handoff.add_argument("task_id")
    coord_handoff.add_argument("--agent", required=True)
    coord_handoff.add_argument("--summary", required=True)
    coord_handoff.add_argument("--next-action", required=True)
    coord_handoff.add_argument("--to-agent")
    _add_revision_argument(coord_handoff)
    coord_handoff.add_argument("--json", dest="json_path")

    coord_status = coord_sub.add_parser("status", help="show compact current tasks, leases, and handoff")
    coord_status.add_argument("root")
    coord_status.add_argument("--json", dest="json_path")

    return parser


def _run_coord(args: argparse.Namespace) -> int:
    try:
        if args.coord_command == "init":
            report = init_coordination(args.root)
        elif args.coord_command == "task":
            report = create_task(
                args.root,
                args.task_id,
                title=args.title,
                objective=args.objective,
                next_action=args.next_action,
                status=args.status,
                inputs=args.input,
                outputs=args.output,
                invariants=args.invariant,
                acceptance=args.acceptance,
                expected_revision=args.expected_revision,
            )
        elif args.coord_command == "claim":
            report = claim_role(
                args.root,
                args.task_id,
                agent_id=args.agent,
                role=args.role,
                lease_minutes=args.lease_minutes,
                expected_revision=args.expected_revision,
            )
        elif args.coord_command == "heartbeat":
            report = heartbeat(
                args.root,
                args.task_id,
                agent_id=args.agent,
                role=args.role,
                lease_minutes=args.lease_minutes,
                expected_revision=args.expected_revision,
            )
        elif args.coord_command == "release":
            report = release_role(
                args.root,
                args.task_id,
                agent_id=args.agent,
                role=args.role,
                expected_revision=args.expected_revision,
            )
        elif args.coord_command == "checkpoint":
            report = checkpoint(
                args.root,
                args.task_id,
                agent_id=args.agent,
                status=args.status,
                next_action=args.next_action,
                evidence=args.evidence,
                blockers=args.blocker,
                expected_revision=args.expected_revision,
            )
        elif args.coord_command == "fail":
            report = record_failure(
                args.root,
                args.task_id,
                agent_id=args.agent,
                mechanism=args.mechanism,
                detail=args.detail,
                next_action=args.next_action,
                expected_revision=args.expected_revision,
            )
        elif args.coord_command == "handoff":
            report = handoff(
                args.root,
                args.task_id,
                agent_id=args.agent,
                summary=args.summary,
                next_action=args.next_action,
                to_agent=args.to_agent,
                expected_revision=args.expected_revision,
            )
        else:
            report = status_report(args.root)
    except CoordinationError as exc:
        print(f"COORD: FAIL {exc}")
        return 2

    _write_json(report, args.json_path)
    print(
        f"COORD: {report.get('status', 'PASS')} "
        f"revision={report.get('revision', 'NA')} "
        f"task={report.get('task_id', report.get('active_task_id', 'NA'))}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.command == "init":
        report = init_project(
            args.destination,
            competition=args.competition,
            year=args.year,
            project_name=args.project_name,
            force=args.force,
        )
        if args.json_path:
            _write_json(report, args.json_path)
        print(
            f"INIT: PASS competition={report['competition']} year={report['year']} "
            f"created={report['created_file_count']} existing={report['existing_file_count']} "
            f"root={report['root']}"
        )
        return 0

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

    if args.command == "paper":
        if args.paper_command == "init":
            report = init_paper(args.root, force=args.force)
            if args.json_path:
                _write_json(report, args.json_path)
            print(
                f"PAPER INIT: PASS created={len(report['created_files'])} "
                f"existing={len(report['existing_files'])} root={report['root']}"
            )
            return 0

        if args.paper_command == "audit":
            report = audit_paper(args.root, args.main_tex)
            _write_json(report, args.json_path)
            print(
                f"PAPER AUDIT: {report['status']} blockers={report['blocker_count']} "
                f"warnings={report['warning_count']} sources={report['source_file_count']}"
            )
            return 0 if report["status"] != "FAIL" else 2

        report = build_paper(args.root, args.build_manifest)
        _write_json(report, args.json_path)
        pdf = report.get("pdf") or {}
        print(f"PAPER BUILD: {report['status']} pdf={pdf.get('path', 'NONE')}")
        return 0 if report["status"] == "PASS" else 2

    if args.command == "coord":
        return _run_coord(args)

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
