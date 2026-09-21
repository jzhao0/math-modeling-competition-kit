# Publishing MMKit

This document covers the external publication path for the public package only. It does not authorize publication by itself.

## Publication boundary

The `v0.1.x` public line contains generalized engineering, public maintenance, security/reliability work, and release hardening.

Active future-competition training, competition-specific prompts/tactics/experiments, raw interaction histories, provider-local configuration, and private artifacts remain outside the public release line unless separately reviewed and explicitly approved.

## Target package

- PyPI project name: `math-modeling-competition-kit`
- Python import package: `mmkit`
- current candidate: `0.1.0a2`
- release tag: `v0.1.0a2`

## Trusted Publisher contract

Use PyPI Trusted Publishing with GitHub Actions OIDC. Do not add a long-lived PyPI API token to repository secrets for the normal release path.

Configure PyPI with exactly:

- Owner: `jzhao0`
- Repository: `math-modeling-competition-kit`
- Workflow filename: `publish-pypi.yml`
- Environment: `pypi`
- Project name: `math-modeling-competition-kit`

The GitHub workflow is `.github/workflows/publish-pypi.yml`.

The `pypi` GitHub environment should keep a manual approval/reviewer gate. The workflow requests `id-token: write` only in the publishing job.

## Fail-closed publication sequence

1. Repository CI must be green.
2. A human explicitly approves the exact release commit and publication action.
3. Create the exact version tag on the approved `main` commit.
4. Wait for the tag-triggered `Release build` workflow to finish successfully.
5. Verify wheel/sdist version, distribution audit, install smoke, and hashes.
6. Confirm the existing PyPI Trusted Publisher still matches the exact contract above.
7. Manually dispatch `Publish to PyPI` with the exact approved tag.
8. Approve the `pypi` GitHub environment gate.
9. The workflow checks out the exact tag, validates tag == `v` + `[project].version`, rebuilds, audits, smoke-installs, and only then invokes the PyPA publishing action through OIDC.
10. After publication, install from official PyPI in a fresh environment and run the public smoke checks.
11. Create a GitHub prerelease for the exact tag after package publication is verified.

## Hard stops

Do not publish if any of the following is true:

- release CI is not green;
- Trusted Publisher configuration does not exactly match repository/workflow/environment;
- the selected tag does not match `[project].version`;
- the tag does not point to the explicitly approved release commit;
- wheel/sdist audit fails;
- artifacts contain private controller content, secrets, historical private-workbench snapshots, or embargoed future-competition material;
- publication approval is absent or ambiguous.

Repository readiness, packaging PASS, and successful PyPI upload do not certify scientific correctness of any mathematical model or competition result.
