"""Generic LaTeX paper engineering for MMKit."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")
INPUT_RE = re.compile(r"\\(?:input|include)\s*\{([^{}]+)\}")
FIG_RE = re.compile(r"\\includegraphics(?:\s*\[[^\]]*\])?\s*\{([^{}]+)\}")
BIB_RE = re.compile(r"\\bibliography\s*\{([^{}]+)\}")
ADDBIB_RE = re.compile(r"\\addbibresource(?:\s*\[[^\]]*\])?\s*\{([^{}]+)\}")
CITE_RE = re.compile(
    r"\\(?:cite|citep|citet|autocite|parencite|textcite|footcite)\*?"
    r"(?:\s*\[[^\]]*\]){0,2}\s*\{([^{}]+)\}"
)
LABEL_RE = re.compile(r"\\label\s*\{([^{}]+)\}")
REF_RE = re.compile(r"\\(?:ref|pageref|eqref|autoref|cref|Cref)\s*\{([^{}]+)\}")
BIBKEY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,", re.I)
COMMENT_RE = re.compile(r"(?<!\\)%.*$")
FIG_EXTS = (".pdf", ".png", ".jpg", ".jpeg", ".eps", ".svg")


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _record(root: Path, path: Path, role: str) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "role": role,
        "size": path.stat().st_size,
        "sha256": _sha(path),
    }


def _text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    return "\n".join(COMMENT_RE.sub("", line) for line in raw.splitlines())


def _tokens(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def _contained(root: Path, base: Path, raw: str, *, role: str) -> Path:
    value = raw.strip()
    if not value or value.startswith(("~", "/")) or DRIVE_RE.match(value):
        raise ValueError(f"{role} must be workspace-relative: {raw}")
    candidate = base / Path(value.replace("\\", "/"))
    if candidate.is_symlink():
        raise ValueError(f"{role} may not be a symlink: {raw}")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{role} escaped workspace: {raw}") from exc
    return resolved


def _existing(
    root: Path,
    base: Path,
    raw: str,
    *,
    role: str,
    suffixes: tuple[str, ...] = (),
    fallback: Path | None = None,
) -> Path:
    value = raw.strip()
    bases = (base,) if fallback is None or fallback == base else (base, fallback)
    for parent in bases:
        first = _contained(root, parent, value, role=role)
        candidates = [first]
        if suffixes and first.suffix == "":
            candidates = [first.with_suffix(s) for s in suffixes] + [first]
        for candidate in candidates:
            if candidate.is_symlink():
                raise ValueError(f"{role} may not be a symlink: {raw}")
            if candidate.exists():
                if not candidate.is_file():
                    raise ValueError(f"{role} must be a regular file: {raw}")
                return candidate
    raise FileNotFoundError(f"{role} missing: {raw}")


def _main(root: Path, raw: str | Path) -> Path:
    value = str(raw)
    p = Path(value)
    candidate = p if p.is_absolute() or DRIVE_RE.match(value) else root / p
    if candidate.is_symlink():
        raise ValueError(f"main_tex may not be a symlink: {raw}")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"main_tex escaped workspace: {raw}") from exc
    if not resolved.is_file():
        raise FileNotFoundError(f"main_tex missing: {raw}")
    return resolved


def _finding(severity: str, kind: str, detail: str, path: str | None = None) -> dict[str, str]:
    out = {"severity": severity, "kind": kind, "detail": detail}
    if path:
        out["path"] = path
    return out


def audit_paper(root: str | Path, main_tex: str | Path) -> dict[str, Any]:
    """Audit static LaTeX dependencies and bibliography identity without compiling."""

    workspace = Path(root).resolve()
    if not workspace.is_dir():
        raise ValueError(f"workspace root must be a directory: {workspace}")
    main = _main(workspace, main_tex)
    main_dir = main.parent
    queue, seen, sources, findings = [main], set(), [], []

    while queue:
        source = queue.pop(0)
        if source in seen:
            continue
        seen.add(source)
        sources.append(source)
        for raw in INPUT_RE.findall(_text(source)):
            try:
                dep = _existing(
                    workspace, source.parent, raw, role="TeX input",
                    suffixes=(".tex",), fallback=main_dir
                )
                if dep not in seen:
                    queue.append(dep)
            except (ValueError, FileNotFoundError) as exc:
                findings.append(_finding(
                    "BLOCKER", "tex_input_invalid", str(exc),
                    source.relative_to(workspace).as_posix()
                ))

    citations: set[str] = set()
    labels: set[str] = set()
    refs: set[str] = set()
    figures: set[Path] = set()
    bibs: dict[Path, set[str]] = {}

    for source in sources:
        body = _text(source)
        for raw in CITE_RE.findall(body):
            citations.update(_tokens(raw))
        labels.update(x.strip() for x in LABEL_RE.findall(body) if x.strip())
        refs.update(x.strip() for x in REF_RE.findall(body) if x.strip())

        for raw in FIG_RE.findall(body):
            try:
                figures.add(_existing(
                    workspace, source.parent, raw, role="figure",
                    suffixes=FIG_EXTS, fallback=main_dir
                ))
            except (ValueError, FileNotFoundError) as exc:
                findings.append(_finding(
                    "BLOCKER", "figure_invalid", str(exc),
                    source.relative_to(workspace).as_posix()
                ))

        declarations: list[str] = []
        for raw in BIB_RE.findall(body):
            declarations.extend(_tokens(raw))
        declarations.extend(x.strip() for x in ADDBIB_RE.findall(body) if x.strip())
        for raw in declarations:
            try:
                bib = _existing(
                    workspace, source.parent, raw, role="bibliography",
                    suffixes=(".bib",), fallback=main_dir
                )
                if bib not in bibs:
                    bibs[bib] = {x.strip() for x in BIBKEY_RE.findall(_text(bib)) if x.strip()}
            except (ValueError, FileNotFoundError) as exc:
                findings.append(_finding(
                    "BLOCKER", "bibliography_invalid", str(exc),
                    source.relative_to(workspace).as_posix()
                ))

    key_files: dict[str, list[Path]] = {}
    for bib, keys in bibs.items():
        for key in keys:
            key_files.setdefault(key, []).append(bib)
    for key in sorted(citations - set(key_files)):
        findings.append(_finding(
            "BLOCKER", "citation_key_missing",
            f"citation key not found in selected bibliography: {key}"
        ))
    for key, files in sorted(key_files.items()):
        if len(files) > 1:
            where = ", ".join(sorted(x.relative_to(workspace).as_posix() for x in files))
            findings.append(_finding(
                "BLOCKER", "duplicate_bibliography_key",
                f"{key} appears in multiple bibliography files: {where}"
            ))
    for label in sorted(refs - labels):
        findings.append(_finding(
            "WARNING", "reference_target_not_static",
            f"reference target not found in static source graph: {label}"
        ))

    files = (
        [_record(workspace, p, "tex") for p in sorted(sources)]
        + [_record(workspace, p, "bibliography") for p in sorted(bibs)]
        + [_record(workspace, p, "figure") for p in sorted(figures)]
    )
    blockers = sum(x["severity"] == "BLOCKER" for x in findings)
    warnings = sum(x["severity"] == "WARNING" for x in findings)
    status = "FAIL" if blockers else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    return {
        "schema_version": 1,
        "status": status,
        "proof_level": "MACHINE_VERIFIED",
        "scope": (
            "static paper dependency/citation identity only; scientific correctness, "
            "writing quality, visual quality and official-format compliance require human review"
        ),
        "main_tex": main.relative_to(workspace).as_posix(),
        "source_file_count": len(sources),
        "citation_count": len(citations),
        "bibliography_file_count": len(bibs),
        "figure_count": len(figures),
        "citations": sorted(citations),
        "bibliography_keys": sorted(key_files),
        "files": files,
        "findings": findings,
        "blocker_count": blockers,
        "warning_count": warnings,
    }


def init_paper(root: str | Path, *, force: bool = False) -> dict[str, Any]:
    """Seed generic paper files; force fills missing files but never overwrites."""

    workspace = Path(root).expanduser()
    if workspace.exists() and not workspace.is_dir():
        raise ValueError(f"paper workspace root is not a directory: {workspace}")
    workspace.mkdir(parents=True, exist_ok=True)
    for rel in ("paper", "references", "config", "coordination"):
        (workspace / rel).mkdir(parents=True, exist_ok=True)

    build = {
        "schema_version": 1,
        "main_tex": "paper/main.tex",
        "cwd": "paper",
        "argv": ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
        "expected_pdf": "paper/main.pdf",
        "timeout_seconds": 300,
    }
    seeds = {
        "paper/main.tex": (
            "\\documentclass{article}\n\\usepackage{graphicx}\n\\begin{document}\n"
            "\\title{Competition Paper}\\author{}\\date{}\\maketitle\n"
            "\\section{Problem and approach}\nReplace this starter with the official template when required.\n"
            "\\section{Model}\nWrite only claims supported by verified workspace evidence.\n"
            "\\section{Results}\nRegister important claims in \\texttt{coordination/CLAIM_REGISTRY.csv}.\n"
            "\\bibliographystyle{plain}\n\\bibliography{../references/references}\n\\end{document}\n"
        ),
        "paper/PAPER_PLAN.md": (
            "# Paper plan\n\n| section | reader question | central claim | evidence | figure/table | status |\n"
            "| --- | --- | --- | --- | --- | --- |\n|  |  |  |  |  | planned |\n"
        ),
        "paper/HUMAN_REVIEW.md": (
            "# Human paper review\n\n"
            "- [ ] Claims match frozen evidence and current provenance.\n"
            "- [ ] Mathematics and assumptions are scientifically adequate.\n"
            "- [ ] Figures/tables/equations/units/precision are clear and consistent.\n"
            "- [ ] Citations support the statements that use them.\n"
            "- [ ] PDF follows official template, page, anonymity and format rules.\n"
            "- [ ] Paper reads naturally at judge-view scale.\n"
        ),
        "references/references.bib": "% Add only verified bibliography entries.\n",
        "config/paper_build.json": json.dumps(build, indent=2, sort_keys=True) + "\n",
        "coordination/PAPER_PIPELINE.md": (
            "# Paper pipeline\n\n"
            "Audit: `mmkit paper audit . paper/main.tex --json coordination/paper_audit.json`\n\n"
            "Build: `mmkit paper build . config/paper_build.json --json coordination/paper_build.json`\n\n"
            "Machine checks do not replace `paper/HUMAN_REVIEW.md` or human gate approval.\n"
        ),
    }
    existing = [rel for rel in seeds if (workspace / rel).exists()]
    if existing and not force:
        raise FileExistsError(
            "paper pipeline files already exist; use --force only to fill missing files"
        )
    created, preserved = [], []
    for rel, content in seeds.items():
        target = workspace / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if not target.is_file():
                raise ValueError(f"paper seed path is not a file: {target}")
            preserved.append(rel)
            continue
        target.write_text(content, encoding="utf-8", newline="\n")
        created.append(rel)
    return {
        "schema_version": 1,
        "status": "PASS",
        "root": str(workspace.resolve()),
        "created_files": created,
        "existing_files": preserved,
        "overwrite_policy": "existing files are never overwritten",
    }


def _load_build_manifest(root: Path, manifest: str | Path | dict[str, Any]) -> dict[str, Any]:
    if isinstance(manifest, dict):
        data = manifest
    else:
        path = Path(manifest)
        if not path.is_absolute() and (root / path).exists():
            path = root / path
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    if data.get("schema_version") != 1:
        raise ValueError("paper build manifest schema_version must be 1")
    if not isinstance(data.get("main_tex"), str) or not data["main_tex"].strip():
        raise ValueError("paper build manifest main_tex must be non-empty")
    argv = data.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
        raise ValueError("paper build manifest argv must be a non-empty string list")
    if not isinstance(data.get("cwd", "."), str) or not data.get("cwd", ".").strip():
        raise ValueError("paper build manifest cwd must be non-empty")
    if not isinstance(data.get("expected_pdf"), str) or not data["expected_pdf"].strip():
        raise ValueError("paper build manifest expected_pdf must be non-empty")
    timeout = data.get("timeout_seconds", 300)
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ValueError("paper build timeout_seconds must be positive")
    return data


def _workspace_path(root: Path, raw: str, role: str, *, exists: bool = False) -> Path:
    path = _contained(root, root, raw, role=role)
    if exists and not path.exists():
        raise FileNotFoundError(f"{role} missing: {raw}")
    return path


def build_paper(root: str | Path, manifest: str | Path | dict[str, Any]) -> dict[str, Any]:
    """Audit then execute exactly one declared paper-build command with shell=False."""

    workspace = Path(root).resolve()
    if not workspace.is_dir():
        raise ValueError(f"workspace root must be a directory: {workspace}")
    data = _load_build_manifest(workspace, manifest)
    audit = audit_paper(workspace, data["main_tex"])
    if audit["status"] == "FAIL":
        return {
            "schema_version": 1, "status": "FAIL", "proof_level": "MACHINE_VERIFIED",
            "build_skipped": True, "reason": "pre-build paper audit contains blockers",
            "audit": audit, "command": None, "pdf": None,
        }

    cwd = _workspace_path(workspace, data.get("cwd", "."), "paper build cwd", exists=True)
    if not cwd.is_dir():
        raise ValueError("paper build cwd must be a directory")
    pdf = _workspace_path(workspace, data["expected_pdf"], "expected_pdf")
    argv = [sys.executable if x == "${PYTHON}" else x for x in data["argv"]]

    started = time.monotonic()
    returncode, error, stdout, stderr = None, None, "", ""
    try:
        done = subprocess.run(
            argv, cwd=cwd, shell=False, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=float(data.get("timeout_seconds", 300)), check=False
        )
        returncode, stdout, stderr = done.returncode, done.stdout[-4000:], done.stderr[-4000:]
    except FileNotFoundError as exc:
        error, stderr = f"executable not found: {argv[0]}", str(exc)
    except subprocess.TimeoutExpired as exc:
        error = f"timeout after {data.get('timeout_seconds', 300)} seconds"
        stdout = (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else ""

    pdf_record, pdf_error = None, None
    if not pdf.exists():
        pdf_error = "expected_pdf was not created"
    elif pdf.is_symlink() or not pdf.is_file():
        pdf_error = "expected_pdf is not a regular non-symlink file"
    elif pdf.read_bytes()[:5] != b"%PDF-":
        pdf_error = "expected_pdf does not start with a PDF header"
    else:
        pdf_record = _record(workspace, pdf, "paper_pdf")

    status = "PASS" if returncode == 0 and error is None and pdf_error is None else "FAIL"
    return {
        "schema_version": 1,
        "status": status,
        "proof_level": "MACHINE_VERIFIED",
        "scope": "build execution and PDF identity only; final scientific/visual/format approval is human",
        "build_skipped": False,
        "audit": audit,
        "command": {
            "argv": data["argv"],
            "cwd": cwd.relative_to(workspace).as_posix() or ".",
            "returncode": returncode,
            "duration_seconds": round(time.monotonic() - started, 6),
            "stdout_tail": stdout,
            "stderr_tail": stderr,
            "error": error,
        },
        "pdf": pdf_record,
        "pdf_error": pdf_error,
    }
