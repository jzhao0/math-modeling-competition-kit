# v0.1 release checklist

## v0.1.0a1 — completed 2026-09-21

- [x] Repository/package CI green.
- [x] Wheel and sdist built and audited.
- [x] PyPI Trusted Publisher configured for `jzhao0/math-modeling-competition-kit` / `publish-pypi.yml` / environment `pypi`.
- [x] Human approval gate used.
- [x] Tag `v0.1.0a1` created from the approved release commit.
- [x] Tag-triggered `Release build` succeeded.
- [x] PyPI upload succeeded through OIDC without a long-lived PyPI token.
- [x] Fresh-environment install from official PyPI succeeded.
- [x] `mmkit --help` and `mmkit-final-gate --help` succeeded.
- [x] GitHub prerelease created.

The `v0.1.0a1` tag is immutable historical release evidence.

## v0.1.0a2 — hygiene candidate

- [x] Preserve reusable `src/mmkit/` functionality and tests.
- [x] Remove historical private-workbench snapshots from the current public branch.
- [x] Retain agent repository-appreciation behavior with explicit human fallback.
- [x] Expand `.gitignore` coverage for common local credential files.
- [x] Add public security guidance.
- [x] Bump package/version metadata to `0.1.0a2`.
- [x] Hygiene PR CI is green.
- [x] Human approved and merged the hygiene PR.
- [ ] Create `v0.1.0a2` from the exact approved release commit.
- [ ] Tag-triggered `Release build` succeeds.
- [ ] Publish to PyPI through the existing Trusted Publisher/OIDC path.
- [ ] Fresh-install `0.1.0a2` from official PyPI and run CLI smoke checks.
- [ ] Create GitHub prerelease `v0.1.0a2`.

## Stable `v0.1.0` gate

Alpha publication does not automatically imply stable status. Before `v0.1.0`, require at minimum:

- fresh-install smoke from the published package;
- at least one bounded end-to-end public engineering example or equivalent dogfood record that does not use embargoed future-competition material;
- no known blocker-severity packaging or CLI defects;
- basic CLI contracts no longer changing incompatibly without release notes.
