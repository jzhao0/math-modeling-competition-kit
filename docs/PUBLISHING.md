# Publishing MMKit

This document covers the external publication path for the public package only. It does not authorize publication by itself.

## Publication boundary

The `v0.1.x` public line contains only generalized engineering distilled from the completed CUMCM 2026 cycle plus generic release hardening and maintenance.

Active MCM/ICM training, new competition-specific ideas, prompts, tactics, experiments, examples, adapters, failure records, and newly discovered techniques remain private until the relevant competition is finished and a later explicit distillation/publication decision is made.

## Target package

- PyPI project name: `math-modeling-competition-kit`
- Python import package: `mmkit`
- current candidate: `0.1.0a1`
- release tag: `v0.1.0a1`

The PyPI namespace is not considered reserved or verified merely because no public project is found in a search. PyPI pending Trusted Publishers do **not** reserve a project name before the first successful publication. Final namespace availability must therefore be confirmed in the authenticated PyPI setup flow immediately before publication.

## Trusted Publisher contract

Use PyPI Trusted Publishing with GitHub Actions OIDC. Do not add a long-lived PyPI API token to repository secrets for the normal release path.

Configure PyPI with exactly:

- Owner: `jzhao0`
- Repository: `math-modeling-competition-kit`
- Workflow filename: `publish-pypi.yml`
- Environment: `pypi`
- Project name: `math-modeling-competition-kit`

The GitHub workflow is `.github/workflows/publish-pypi.yml`.

The `pypi` GitHub environment should be configured with manual approval/reviewer protection when available. The workflow itself requests `id-token: write` only in the publishing job.

## Fail-closed publication sequence

1. Repository release-hardening CI must be green.
2. A human explicitly approves the exact release commit and publication action.
3. Create tag `v0.1.0a1` on the exact approved `main` commit.
4. Wait for the tag-triggered `Release build` workflow to finish successfully.
5. Verify its wheel and sdist artifacts, version, distribution audit, and hashes.
6. In PyPI, create/confirm the pending or existing Trusted Publisher using the exact contract above.
7. Manually dispatch `Publish to PyPI` with input `tag=v0.1.0a1`.
8. Approve the `pypi` GitHub environment gate if configured.
9. The workflow checks out `refs/tags/v0.1.0a1`, verifies tag == `v` + `[project].version`, rebuilds, audits, smoke-installs, and only then invokes the PyPA publishing action through OIDC.
10. After publication, install the package from PyPI in a fresh environment and run the public smoke checks.
11. Create GitHub Release notes for the exact tag after package publication is verified.

## Hard stops

Do not publish if any of the following is true:

- the intended PyPI project name cannot be claimed by the intended maintainer account;
- Trusted Publisher configuration does not exactly match repository/workflow/environment;
- the selected tag does not match `[project].version`;
- the tag does not point to the explicitly approved release commit;
- wheel/sdist audit fails;
- artifacts contain `migration_sources/`, private controller content, secrets, or embargoed future-competition material;
- publication approval is absent or ambiguous.

Repository readiness, packaging PASS, and successful PyPI upload do not certify scientific correctness of any mathematical model or competition result.
