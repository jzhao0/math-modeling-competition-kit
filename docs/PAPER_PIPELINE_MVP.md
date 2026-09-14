# Paper Pipeline MVP

P5 turns the paper phase into a deterministic engineering surface without pretending
that machine checks can approve scientific quality.

## Commands

Initialize generic paper-pipeline files inside an MMKit workspace:

```text
mmkit paper init .
```

This creates only missing files. If paper-pipeline files already exist, the command
refuses by default. `--force` means "fill missing files"; it never overwrites an
existing user file.

Audit a LaTeX source graph:

```text
mmkit paper audit . paper/main.tex --json coordination/paper_audit.json
```

The audit follows static `\input` / `\include` dependencies, fingerprints the
selected TeX graph, checks `\includegraphics` dependencies, parses bibliography
files, verifies citation keys, detects duplicate bibliography keys, and reports
statically unresolved references as warnings.

Build with an explicit argv contract:

```text
mmkit paper build . config/paper_build.json --json coordination/paper_build.json
```

The default seed uses `latexmk`. MMKit does not install TeX or silently choose a
compiler. The build command is executed with `shell=False`, inside a workspace-
contained working directory, with a timeout and an expected PDF path.

## Build manifest

```json
{
  "schema_version": 1,
  "main_tex": "paper/main.tex",
  "cwd": "paper",
  "argv": [
    "latexmk",
    "-pdf",
    "-interaction=nonstopmode",
    "-halt-on-error",
    "main.tex"
  ],
  "expected_pdf": "paper/main.pdf",
  "timeout_seconds": 300
}
```

`${PYTHON}` is accepted in argv for portable test or custom build scripts.

## Audit status

- `PASS`: no blockers or warnings.
- `PASS_WITH_WARNINGS`: no blockers, but static checks need human attention.
- `FAIL`: at least one deterministic blocker exists.

Blockers include missing/escaping TeX inputs, figure dependencies, bibliography
files, missing cited keys, and duplicate selected bibliography keys. A `\ref`
target not found statically is a warning because macro-generated labels cannot
always be resolved safely without compiling.

## Build status

`paper build` first runs the paper audit. If the audit has a blocker, execution is
skipped. Otherwise MMKit runs exactly the declared argv without a shell and verifies
that the expected output exists, is a regular file, begins with a PDF header, and
records its SHA-256 and size.

This does **not** prove that the PDF satisfies an official contest page limit,
template, typography, anonymity, visual-quality, or scientific-correctness
requirement. Those remain part of human review and the final submission gate.

## Provenance boundary

P3 claim/evidence provenance and P5 paper engineering answer different questions:

- provenance: did the claim row or upstream evidence bytes change?
- paper audit: are the selected paper source dependencies and citation/asset links current?
- human review: is the paper scientifically correct, convincing, clear, visually strong,
  and compliant with the official competition rules?

Do not collapse these layers into one generic PASS.
