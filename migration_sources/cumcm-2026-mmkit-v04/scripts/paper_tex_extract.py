"""Shared deterministic LaTeX extraction for the Paper Gate and Sol packet."""

from __future__ import annotations

import bisect
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from paper_gate_common import chinese_char_count


@dataclass
class TexDocument:
    text: str
    main_path: Path | None = None
    line_origins: list[tuple[Path | None, int]] = field(default_factory=list)
    source_files: list[Path] = field(default_factory=list)
    _line_starts: list[int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._line_starts = [0]
        self._line_starts.extend(match.end() for match in re.finditer(r"\n", self.text))
        if not self.line_origins:
            self.line_origins = [(self.main_path, index + 1) for index in range(len(self._line_starts))]

    @classmethod
    def from_text(cls, text: str, source_path: str | Path | None = None) -> "TexDocument":
        path = Path(source_path).resolve() if source_path else None
        return cls(text=text, main_path=path, source_files=[path] if path else [])

    def location(self, offset: int) -> dict[str, Any]:
        line_index = max(0, bisect.bisect_right(self._line_starts, offset) - 1)
        if line_index < len(self.line_origins):
            path, line = self.line_origins[line_index]
        else:
            path, line = self.main_path, line_index + 1
        return {"source_file": str(path) if path else "UNKNOWN", "source_line": line}


def strip_tex_comments(text: str) -> str:
    """Strip unescaped comments while preserving line count."""

    return "\n".join(re.sub(r"(?<!\\)%.*$", "", line) for line in text.splitlines())


def mask_tex_comments(text: str) -> str:
    """Mask comments with spaces so source offsets and line origins stay stable."""

    output: list[str] = []
    for line in text.splitlines(keepends=True):
        match = re.search(r"(?<!\\)%", line)
        if not match:
            output.append(line)
            continue
        ending = "\n" if line.endswith("\n") else ""
        content = line[:-1] if ending else line
        output.append(content[:match.start()] + " " * (len(content) - match.start()) + ending)
    return "".join(output)


def _resolve_include(current: Path, reference: str) -> Path:
    dependency = current.parent / reference
    if not dependency.suffix:
        dependency = dependency.with_suffix(".tex")
    return dependency.resolve()


def expand_tex_document(main_tex: str | Path) -> TexDocument:
    """Expand explicit input/include commands without scanning sibling drafts."""

    root = Path(main_tex).resolve()
    output_lines: list[str] = []
    origins: list[tuple[Path | None, int]] = []
    source_files: list[Path] = []
    active: set[Path] = set()

    def expand(path: Path) -> None:
        if path in active:
            raise ValueError(f"Recursive TeX include detected: {path}")
        if not path.is_file():
            raise FileNotFoundError(f"TeX source not found: {path}")
        active.add(path)
        if path not in source_files:
            source_files.append(path)
        content = path.read_text(encoding="utf-8-sig", errors="replace")
        for line_number, line in enumerate(content.splitlines(keepends=True), start=1):
            uncommented = re.sub(r"(?<!\\)%.*$", "", line).strip()
            include_match = re.fullmatch(r"\\(?:input|include)\{([^}]+)\}", uncommented)
            if include_match and not re.search(r"[#\\]", include_match.group(1)):
                expand(_resolve_include(path, include_match.group(1).strip()))
            else:
                output_lines.append(line)
                origins.append((path, line_number))
        active.remove(path)

    expand(root)
    text = "".join(output_lines)
    return TexDocument(text=text, main_path=root, line_origins=origins, source_files=source_files)


def _balanced_group(text: str, opening_brace: int) -> tuple[str, int] | None:
    depth = 0
    index = opening_brace
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[opening_brace + 1:index], index + 1
        index += 1
    return None


def command_arguments(text: str, command: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    pattern = re.compile(rf"\\{re.escape(command)}\*?(?:\[[^]]*\])?\s*\{{")
    for match in pattern.finditer(text):
        group = _balanced_group(text, match.end() - 1)
        if group:
            value, end = group
            results.append({"value": value, "start": match.start(), "end": end})
    return results


def _environment_spans(text: str, names: Iterable[str]) -> list[dict[str, Any]]:
    name_pattern = "|".join(re.escape(name) for name in names)
    begin_pattern = re.compile(rf"\\begin\{{(?P<name>{name_pattern})\}}")
    results: list[dict[str, Any]] = []
    cursor = 0
    while True:
        begin = begin_pattern.search(text, cursor)
        if not begin:
            break
        name = begin.group("name")
        end = re.search(rf"\\end\{{{re.escape(name)}\}}", text[begin.end():])
        if not end:
            cursor = begin.end()
            continue
        end_start = begin.end() + end.start()
        end_offset = begin.end() + end.end()
        results.append({
            "name": name,
            "start": begin.start(),
            "body_start": begin.end(),
            "body_end": end_start,
            "end": end_offset,
            "body": text[begin.end():end_start],
        })
        cursor = end_offset
    return results


def _without_spans(text: str, spans: Iterable[dict[str, Any]]) -> str:
    characters = list(text)
    for span in spans:
        for index in range(span["start"], min(span["end"], len(characters))):
            if characters[index] != "\n":
                characters[index] = " "
    return "".join(characters)


def _clean_command_wrappers(text: str) -> str:
    for _ in range(5):
        updated = re.sub(
            r"\\(?:textbf|textit|emph|underline|mbox|textrm|textsf|texttt|text|mathrm|mathbf|operatorname)\{([^{}]*)\}",
            r"\1",
            text,
        )
        if updated == text:
            break
        text = updated
    return text


def latex_to_readable(text: str, *, exclude_blocks: bool = True) -> str:
    """Convert a bounded source range to readable prose without rewriting it."""

    text = strip_tex_comments(text)
    if exclude_blocks:
        spans = _environment_spans(text, (
            "figure", "figure*", "table", "table*", "longtable", "equation", "equation*",
            "align", "align*", "alignat", "alignat*", "gather", "gather*", "multline", "multline*",
            "displaymath", "listings", "lstlisting", "verbatim", "verbatim*", "minted",
            "algorithm", "algorithm*", "algorithmic", "tikzpicture",
        ))
        text = _without_spans(text, spans)
    text = re.sub(r"\\(?:section|subsection|subsubsection|[A-Za-z@]*Section|[A-Za-z@]*Subsection)\*?\{[^{}]*\}", "\n\n", text)
    text = re.sub(r"\\(?:label|includegraphics)(?:\[[^]]*\])?\{[^{}]*\}", " ", text)
    text = re.sub(r"\\caption\*?(?:\[[^]]*\])?\{(?:[^{}]|\{[^{}]*\})*\}", " ", text, flags=re.DOTALL)
    text = re.sub(r"\\(?:cite\w*)\{([^{}]+)\}", r"[cite:\1]", text)
    text = re.sub(r"\\(?:ref|autoref|cref|Cref)\{([^{}]+)\}", r"ref(\1)", text)
    text = text.replace("\\item", "\n- ").replace("\\par", "\n\n")
    text = _clean_command_wrappers(text)
    text = re.sub(r"\\begin\{[^{}]+\}|\\end\{[^{}]+\}", " ", text)
    text = re.sub(r"\\(?:centering|small|footnotesize|scriptsize|normalsize|noindent|raggedright|raggedleft)\b", " ", text)
    text = re.sub(r"\\(?:vspace|hspace|setlength|addvspace)\*?(?:\[[^]]*\])?\{[^{}]*\}", " ", text)
    text = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^]]*\])?", " ", text)
    text = text.replace("\\%", "%").replace("\\&", "&").replace("\\_", "_")
    text = text.replace("~", " ").replace("{", "").replace("}", "")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    output: list[str] = []
    blank = False
    for line in lines:
        if line:
            output.append(line)
            blank = False
        elif output and not blank:
            output.append("")
            blank = True
    return "\n".join(output).strip()


def extract_readable_prose_document(source: str) -> str:
    source = strip_tex_comments(source)
    document = re.search(r"\\begin\{document\}", source)
    if document:
        source = source[document.end():]
    end = re.search(
        r"\\(?:section\*?|[A-Za-z@]*Section)\*?\{\s*(?:AI\s*工具使用声明|参考文献|References|Bibliography)[^}]*\}"
        r"|\\begin\{thebibliography\}|\\printbibliography|\\bibliography\{|\\appendix|\\end\{document\}",
        source,
        flags=re.IGNORECASE,
    )
    if end:
        source = source[:end.start()]
    return latex_to_readable(source, exclude_blocks=True)


def _document_end(text: str) -> int:
    candidates = [len(text)]
    for pattern in (
        r"\\begin\{thebibliography\}", r"\\printbibliography", r"\\bibliography\{",
        r"\\appendix\b", r"\\end\{document\}",
    ):
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            candidates.append(match.start())
    return min(candidates)


def extract_sections(document: TexDocument) -> list[dict[str, Any]]:
    text = mask_tex_comments(document.text)
    end_of_body = _document_end(text)
    command_pattern = re.compile(r"\\(?P<command>[A-Za-z@]+)(?P<star>\*)?\s*\{")
    headings: list[dict[str, Any]] = []
    for match in command_pattern.finditer(text[:end_of_body]):
        command = match.group("command")
        lowered = command.lower()
        if not lowered.endswith("section"):
            continue
        level = 2 if lowered.endswith("subsection") else 1
        group = _balanced_group(text, match.end() - 1)
        if not group:
            continue
        title, command_end = group
        if "#" in title or "\\" in title:
            continue
        headings.append({
            "level": level,
            "title": re.sub(r"\s+", " ", title).strip(),
            "starred": bool(match.group("star")) or command in {"section", "subsection"} and bool(match.group("star")),
            "start": match.start(),
            "heading_end": command_end,
            **document.location(match.start()),
        })

    section_number = 0
    subsection_number = 0
    for index, heading in enumerate(headings):
        if heading["level"] == 1:
            if not heading["starred"]:
                section_number += 1
                subsection_number = 0
                heading["number"] = str(section_number)
            else:
                heading["number"] = ""
        else:
            subsection_number += 1
            heading["number"] = f"{section_number}.{subsection_number}" if section_number else str(subsection_number)
        body_end = headings[index + 1]["start"] if index + 1 < len(headings) else end_of_body
        heading["body_start"] = heading["heading_end"]
        heading["body_end"] = body_end
        raw_body = text[heading["body_start"]:body_end]
        heading["raw_body"] = raw_body
        heading["text"] = latex_to_readable(raw_body, exclude_blocks=True)
        heading["chinese_characters"] = chinese_char_count(heading["text"])
        end_location = document.location(max(heading["body_start"], body_end - 1))
        heading["source_end_file"] = end_location["source_file"]
        heading["source_end_line"] = end_location["source_line"]
    return headings


def extract_section_titles(source_text: str) -> set[str]:
    return {item["title"] for item in extract_sections(TexDocument.from_text(source_text))}


def _first_argument(text: str, command: str) -> dict[str, Any] | None:
    arguments = command_arguments(text, command)
    return arguments[0] if arguments else None


def _reference_locations(document: TexDocument, text_without_entities: str) -> dict[str, list[dict[str, Any]]]:
    refs: dict[str, list[dict[str, Any]]] = {}
    for match in re.finditer(r"\\(?:ref|autoref|cref|Cref)\s*\{([^}]+)\}", text_without_entities):
        refs.setdefault(match.group(1), []).append(document.location(match.start()))
    return refs


def _graphic_paths(text: str) -> list[str]:
    paths: list[str] = []
    for argument in command_arguments(text, "graphicspath"):
        paths.extend(match.group(1) for match in re.finditer(r"\{([^{}]+)\}", argument["value"]))
    return paths


def _resolve_graphic(source_file: str, graphic: str, graphic_paths: list[str]) -> tuple[str, str]:
    if not source_file or source_file == "UNKNOWN" or "#" in graphic or "\\" in graphic:
        return graphic, "MISSING" if "#" not in graphic else "DYNAMIC"
    source_dir = Path(source_file).parent
    roots = [source_dir]
    roots.extend((source_dir / item).resolve() for item in graphic_paths)
    extensions = [""] if Path(graphic).suffix else [".pdf", ".png", ".jpg", ".jpeg", ".eps"]
    for root in roots:
        for extension in extensions:
            candidate = (root / f"{graphic}{extension}").resolve()
            if candidate.is_file():
                return str(candidate), "AVAILABLE"
    return str((source_dir / graphic).resolve()), "MISSING"


def extract_figures(document: TexDocument) -> list[dict[str, Any]]:
    spans = _environment_spans(document.text, ("figure", "figure*"))
    reference_text = _without_spans(document.text, spans)
    refs = _reference_locations(document, reference_text)
    graphic_paths = _graphic_paths(document.text)
    figures: list[dict[str, Any]] = []
    for index, span in enumerate(spans, start=1):
        caption = _first_argument(span["body"], "caption")
        label = _first_argument(span["body"], "label")
        graphic = _first_argument(span["body"], "includegraphics")
        location = document.location(span["start"])
        label_value = label["value"].strip() if label else ""
        dynamic = "#" in span["body"] or bool(label_value and not re.fullmatch(r"[A-Za-z0-9_.:-]+", label_value))
        references = refs.get(label_value, []) if label_value and not dynamic else []
        graphic_value = graphic["value"].strip() if graphic else ""
        resolved, source_status = _resolve_graphic(location["source_file"], graphic_value, graphic_paths) if graphic_value else ("UNKNOWN", "MISSING")
        end_location = document.location(span["end"] - 1)
        figures.append({
            "number": index,
            "label": label_value or "UNKNOWN",
            "caption": latex_to_readable(caption["value"], exclude_blocks=False) if caption else "UNKNOWN",
            "source_file": resolved,
            "source_status": source_status,
            "source_tex": location["source_file"],
            "source_line": location["source_line"],
            "source_end_line": end_location["source_line"],
            "first_reference": references[0] if references else None,
            "referenced": bool(references),
            "dynamic": dynamic,
            "page": "UNKNOWN",
        })
    return figures


def _table_markdown(body: str) -> str:
    tabular = re.search(r"\\begin\{tabular\}(?:\[[^]]*\])?\{[^{}]*\}(.*?)\\end\{tabular\}", body, flags=re.DOTALL)
    content = tabular.group(1) if tabular else body
    content = re.sub(r"\\(?:toprule|midrule|bottomrule|hline|endhead|endfirsthead|endfoot|endlastfoot)\b", "", content)
    content = re.sub(r"\\(?:caption|label)\*?(?:\[[^]]*\])?\{[^{}]*\}", "", content)
    rows: list[list[str]] = []
    for row in re.split(r"\\\\(?:\[[^]]*\])?", content):
        if "&" not in row:
            continue
        cells = [latex_to_readable(cell, exclude_blocks=False).replace("|", "\\|") for cell in row.split("&")]
        if any(cells):
            rows.append(cells)
    if not rows:
        cleaned = latex_to_readable(content, exclude_blocks=False)
        return f"```text\n{cleaned}\n```" if cleaned else "NOT DETERMINISTICALLY EXTRACTABLE"
    width = max(len(row) for row in rows)
    normalized = [row + [""] * (width - len(row)) for row in rows]
    header = normalized[0]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * width) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in normalized[1:])
    return "\n".join(lines)


def extract_tables(document: TexDocument) -> list[dict[str, Any]]:
    spans = _environment_spans(document.text, ("table", "table*", "longtable"))
    reference_text = _without_spans(document.text, spans)
    refs = _reference_locations(document, reference_text)
    tables: list[dict[str, Any]] = []
    for index, span in enumerate(spans, start=1):
        caption = _first_argument(span["body"], "caption")
        label = _first_argument(span["body"], "label")
        label_value = label["value"].strip() if label else ""
        references = refs.get(label_value, []) if label_value else []
        location = document.location(span["start"])
        end_location = document.location(span["end"] - 1)
        tables.append({
            "number": index,
            "label": label_value or "UNKNOWN",
            "caption": latex_to_readable(caption["value"], exclude_blocks=False) if caption else "UNKNOWN",
            "source_tex": location["source_file"],
            "source_line": location["source_line"],
            "source_end_line": end_location["source_line"],
            "first_reference": references[0] if references else None,
            "referenced": bool(references),
            "dynamic": "#" in span["body"],
            "content_markdown": _table_markdown(span["body"]),
        })
    return tables


def _section_for_offset(sections: list[dict[str, Any]], offset: int) -> str:
    prior = [item for item in sections if item["start"] <= offset]
    return prior[-1]["title"] if prior else "UNKNOWN"


def extract_equations(document: TexDocument, sections: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    sections = sections or extract_sections(document)
    spans = _environment_spans(document.text, ("equation",))
    equations: list[dict[str, Any]] = []
    for index, span in enumerate(spans, start=1):
        location = document.location(span["start"])
        body = re.sub(r"\\label\{[^{}]+\}", "", span["body"]).strip()
        tag = _first_argument(span["body"], "tag")
        equations.append({
            "number": tag["value"].strip() if tag else str(index),
            "source_section": _section_for_offset(sections, span["start"]),
            "latex": body,
            **location,
        })
    return equations


def extract_abstract(document: TexDocument, sections: list[dict[str, Any]] | None = None) -> str:
    abstract_env = _environment_spans(document.text, ("abstract",))
    if abstract_env:
        return latex_to_readable(abstract_env[0]["body"], exclude_blocks=True)
    sections = sections or extract_sections(document)
    first_section = sections[0]["start"] if sections else _document_end(document.text)
    preamble_body = document.text[:first_section]
    document_start = re.search(r"\\begin\{document\}", preamble_body)
    if document_start:
        preamble_body = preamble_body[document_start.end():]
    abstract_heading = re.search(r"(?:\\bfseries\s*)?摘要", preamble_body)
    if not abstract_heading:
        return "NOT DETERMINISTICALLY EXTRACTABLE"
    keywords = re.search(r"(?:关键词|关\s*键\s*词)[：:]", preamble_body[abstract_heading.end():])
    end = abstract_heading.end() + keywords.start() if keywords else len(preamble_body)
    return latex_to_readable(preamble_body[abstract_heading.end():end], exclude_blocks=True)


def extract_references(document: TexDocument) -> list[dict[str, Any]]:
    bibliography = _environment_spans(document.text, ("thebibliography",))
    if not bibliography:
        return []
    body = bibliography[0]["body"]
    items = list(re.finditer(r"\\bibitem(?:\[[^]]*\])?\{([^}]+)\}", body))
    references: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        end = items[index].start() if index < len(items) else len(body)
        raw = body[item.end():end]
        summary = re.sub(r"\s+", " ", latex_to_readable(raw, exclude_blocks=False)).strip()
        dois = re.findall(r"(?i)\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", summary)
        references.append({"number": index, "key": item.group(1), "summary": summary, "dois": [doi.rstrip(".,;") for doi in dois]})
    return references
