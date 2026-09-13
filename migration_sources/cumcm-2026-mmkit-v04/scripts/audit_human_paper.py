#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Human-paper risk linter for CUMCM manuscripts.

This is a deterministic warning tool distilled from real Drill-02 defects. It does not
judge scientific correctness or estimate whether text is AI-generated. It locates
presentation/writing patterns that deserve a human read before G4.

Default mode is advisory (exit 0 even with findings). --strict returns 1 when a HARD
presentation defect is found. --json writes a machine-readable report.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Finding:
    severity: str
    rule: str
    file: str
    line: int
    snippet: str
    advice: str


TEXT_RULES: list[tuple[str, str, re.Pattern[str], str]] = [
    (
        "WARN",
        "raw_float_precision",
        re.compile(r"(?<![\w.])[-+]?\d+\.\d{5,}(?!\d)"),
        "正文中疑似直接保留机器浮点精度；按决策需要保留 2–4 位，完整精度留结果文件/附录。",
    ),
    (
        "WARN",
        "defensive_not_report",
        re.compile(r"本文\s*(?:不|未)\s*(?:报告|讨论|给出|声称|考虑)"),
        "优先改成正向的模型范围/比较指标陈述；若不影响理解，可直接删除内部审计式说明。",
    ),
    (
        "WARN",
        "defensive_absolute",
        re.compile(r"(?:绝不|绝非|不在本文(?:的)?(?:声明|讨论|研究)?范围|不构成[^。；，]{0,24}(?:证明|结论))"),
        "检查是否是防御式 LLM 句框；必要边界用正常学术句说明，非必要免责声明删除。",
    ),
    (
        "WARN",
        "internal_process_vocabulary",
        re.compile(r"(?i)(?:\baudit\b|\bpipeline\b|\bhandoff\b|\bfrozen[-_ ]?claim\b|\bverified[-_ ]?pipeline\b|\bagent\b)"),
        "正文不应出现内部 Agent/审计/流水线语言；改成研究对象、算法或验证方法本身。",
    ),
    (
        "WARN",
        "slash_separated_tuple_output",
        re.compile(r"\([^()]{0,30}\)\s*/\s*\([^()]{0,30}\)"),
        "多个参数—结果映射不要用程序输出式斜杠拼接；改成正文映射、分号或小表格。",
    ),
    (
        "WARN",
        "informal_numeric_range",
        re.compile(r"\d+(?:\.\d+)?\s*[~～]\s*\d+(?:\.\d+)?\s*%?"),
        "数值范围优先写成‘约 a%–b%’或数学区间 [a%, b%]。",
    ),
    (
        "INFO",
        "expanded_strategy_count",
        re.compile(r"2\s*\^?\s*\{?\s*\d+\s*\}?\s*=\s*\d{4,}"),
        "若这里只是说明枚举规模，可直接写‘共枚举 N 种策略’；公式推导仅在有解释价值时保留。",
    ),
]

CODE_RULES: list[tuple[str, str, re.Pattern[str], str]] = [
    (
        "WARN",
        "code_internal_audit_language",
        re.compile(r"(?i)(?:frozen[_ -]?claim|verified[_ -]?pipeline|agent[_ -]?handoff|audit[_ -]?status)"),
        "支撑代码应像科研代码；内部审计/Agent 生命周期命名若非复现所需应清理。",
    ),
    (
        "WARN",
        "generated_step_comment",
        re.compile(r"^\s*#\s*(?:Step|STEP)\s*\d+\b"),
        "机械 Step 注释通常可改成数学意义、输入输出或非显然算法说明。",
    ),
    (
        "HARD",
        "personal_absolute_path",
        re.compile(r"(?i)(?:[A-Z]:\\(?:Users|Projects)\\|/Users/[^/]+/)"),
        "提交代码不得依赖个人绝对路径；改为 workspace-relative/pathlib/CLI 输入。",
    ),
]


def compact(s: str, limit: int = 180) -> str:
    s = re.sub(r"\s+", " ", s.strip())
    return s if len(s) <= limit else s[: limit - 1] + "…"


def audit_tex(path: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    out: list[Finding] = []

    for no, line in enumerate(lines, 1):
        for severity, rule, pat, advice in TEXT_RULES:
            if pat.search(line):
                out.append(Finding(severity, rule, str(path), no, compact(line), advice))

        # Long parenthetical content: advisory only. Ignore short refs/math-like groups.
        for m in re.finditer(r"[（(]([^（）()]{35,})[）)]", line):
            content = m.group(1)
            if not re.fullmatch(r"[\s\w\\{}\[\].,;:+\-*/=<>|]+", content):
                out.append(
                    Finding(
                        "WARN",
                        "long_parenthetical_argument",
                        str(path),
                        no,
                        compact(m.group(0)),
                        "括号承载了较长正文；若包含论证、限制或完整分句，改写成正常句子。",
                    )
                )
                break

    if "\\usepackage" in text and "hyperref" in text and "\\hypersetup{hidelinks}" not in text:
        out.append(
            Finding(
                "HARD",
                "visible_hyperlink_boxes_risk",
                str(path),
                1,
                "hyperref loaded without \\hypersetup{hidelinks}",
                "正式稿隐藏图/表/公式/文献交叉引用的红绿边框，同时保留可点击链接。",
            )
        )
    if re.search(r"\\pagestyle\s*\{\s*fancy\s*\}", text) or "\\fancyhead" in text:
        out.append(
            Finding(
                "WARN",
                "running_header_risk",
                str(path),
                1,
                "fancy page style/header detected",
                "CUMCM 默认不使用期刊式 running header；按当届官方模板人工核对页码/页眉。",
            )
        )
    return out


def audit_code(root: Path) -> list[Finding]:
    out: list[Finding] = []
    suffixes = {".py", ".R", ".m", ".wl", ".ps1", ".sh"}
    if not root.exists():
        return out
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix in suffixes):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for no, line in enumerate(lines, 1):
            for severity, rule, pat, advice in CODE_RULES:
                if pat.search(line):
                    out.append(Finding(severity, rule, str(path), no, compact(line), advice))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit CUMCM manuscript for human-paper presentation risks")
    ap.add_argument("tex", help="paper .tex file")
    ap.add_argument("--code-dir", help="optional submitted-code directory")
    ap.add_argument("--json", dest="json_path", help="write JSON report")
    ap.add_argument("--strict", action="store_true", help="exit 1 if HARD findings exist")
    args = ap.parse_args()

    tex = Path(args.tex)
    if not tex.is_file():
        print(f"PAPER_HUMAN_AUDIT: INPUT_MISSING | {tex}")
        return 2

    findings = audit_tex(tex)
    if args.code_dir:
        findings.extend(audit_code(Path(args.code_dir)))

    counts = {k: sum(f.severity == k for f in findings) for k in ("HARD", "WARN", "INFO")}
    print(
        "PAPER_HUMAN_AUDIT: "
        f"HARD={counts['HARD']} WARN={counts['WARN']} INFO={counts['INFO']} TOTAL={len(findings)}"
    )
    for f in findings:
        print(f"[{f.severity}] {f.rule} | {f.file}:{f.line} | {f.snippet}")
        print(f"  -> {f.advice}")

    report = {
        "tex": str(tex),
        "code_dir": args.code_dir,
        "counts": counts,
        "findings": [asdict(f) for f in findings],
        "note": "Advisory linter; no AI probability is produced. Human judge-view review remains required.",
    }
    if args.json_path:
        p = Path(args.json_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return 1 if args.strict and counts["HARD"] else 0


if __name__ == "__main__":
    sys.exit(main())
