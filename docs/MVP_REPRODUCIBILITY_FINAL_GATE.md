# MVP: reproducibility and final submission gate

This is the first public-product slice of MMKit.

## Scope

The MVP deliberately starts with engineering guarantees rather than a large modeling-algorithm catalog:

- deterministic SHA-256 workspace manifests;
- bounded clean-room execution from an explicit command manifest;
- a generic final-submission engineering gate;
- standard-library-only runtime code;
- deterministic tests.

Product code is self-contained under `src/mmkit/` and must not depend on private workspaces or historical snapshots.

## Reproducibility manifest

```python
from mmkit.reproducibility import build_manifest, write_manifest

manifest = build_manifest("workspace")
write_manifest(manifest, "reports/input_manifest.json")
```

The serialized manifest excludes absolute host paths and sorts records by POSIX-style relative path.

## Clean-room runner

A run manifest is JSON-compatible and explicit:

```json
{
  "schema_version": 1,
  "stop_on_failure": true,
  "commands": [
    {
      "name": "solve",
      "argv": ["${PYTHON}", "analysis/solve.py"],
      "cwd": ".",
      "timeout_seconds": 300,
      "expected_outputs": ["results/result.csv"]
    }
  ]
}
```

The runner copies the source tree to a temporary directory, rejects source symlinks, executes with `shell=False`, validates working-directory/output paths, and records command evidence.

## Final submission gate

Repository-local usage:

```bash
python tools/final_gate.py submission \
  --require paper.pdf \
  --require support.zip \
  --json reports/final_gate.json
```

The initial gate checks:

- required artifacts;
- SHA-256/size inventory;
- filesystem symlinks;
- common credential/secret patterns in text files;
- leaked absolute local paths;
- ZIP traversal/absolute paths;
- duplicate ZIP members;
- ZIP symlinks;
- ZIP CRC integrity.

A `PASS` here is `MACHINE_VERIFIED` submission-engineering evidence only. It does **not** certify scientific correctness, model quality, originality, contest eligibility, or human paper quality.

## Unified CLI

After installation, the current MVP exposes three commands through `mmkit`:

```bash
mmkit manifest workspace --output reports/workspace_manifest.json
mmkit reproduce workspace RUN_MANIFEST.json --json reports/reproduce.json
mmkit audit submission --require paper.pdf --require support.zip --json reports/final_gate.json
```

The clean-room report binds the run evidence to a deterministic source manifest and hashes declared output files (or recursively manifests declared output directories).
