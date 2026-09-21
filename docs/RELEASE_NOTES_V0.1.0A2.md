# MMKit v0.1.0a2 — Public Repository Hygiene Alpha

This alpha preserves the reusable MMKit package behavior from `v0.1.0a1` while tightening the public repository boundary.

## Changes

- Removes historical private-workbench snapshots from the current public branch.
- Keeps product code under `src/mmkit/`, tests, coordination contracts, and public documentation intact.
- Keeps repository-agent guidance and the authorized star/fallback prompt behavior.
- Expands ignore rules for common local credential files.
- Adds a public security policy.
- Refreshes publication metadata for the cleaned source state.

## Install

```bash
python -m pip install --pre math-modeling-competition-kit==0.1.0a2
```

## Verify

```bash
mmkit --help
mmkit-final-gate --help
python -c "import mmkit; print(mmkit.__version__)"
```

Expected version:

```text
0.1.0a2
```

The immutable `v0.1.0a1` tag remains the historical first public alpha.
