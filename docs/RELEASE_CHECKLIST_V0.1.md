# v0.1 release checklist

Target candidate: `v0.1.0a1`

This checklist separates repository readiness from irreversible publication actions.

## Repository / package gate

- [x] P1–P7 public engineering slices merged to `main` before the release branch.
- [x] MIT license present.
- [x] Python package metadata declares alpha status.
- [x] Package version is exposed as `mmkit.__version__` and unit-tested against `pyproject.toml`.
- [x] Windows + Ubuntu test matrix exists for Python 3.11 and 3.13.
- [x] Release candidate CI builds wheel and sdist.
- [x] Built distribution archives are audited to block `migration_sources/` and other forbidden components.
- [x] CI installs the built wheel without index access and runs CLI/import smoke checks.
- [x] CI reruns the full test suite against the installed package.
- [x] Tag-triggered release-build workflow can produce auditable distribution artifacts without automatically publishing them.
- [x] v0.1 publication scope explicitly excludes active future-competition training and private material.
- [x] PR #9 release-candidate CI run `34956898207` completed successfully before merge.
- [x] Human approved and PR #9 was merged to `main`.
- [x] PR #10 follow-up release-hardening CI run `34958136870` completed successfully with 64/64 tests passing.
- [x] Human approved and PR #10 was merged to `main`.
- [x] Distribution required-member matching rejects near-match archive names.
- [x] Tag-triggered build validates tag == `v` + `[project].version` before building.
- [ ] PyPI publication-readiness PR has a final successful GitHub Actions run.
- [ ] Human approves merging the PyPI publication-readiness PR.

## External publication gate

The items below are intentionally **not** satisfied merely by merging repository changes.

- [ ] Confirm the PyPI project namespace `math-modeling-competition-kit` can be claimed by the intended maintainer account in the authenticated PyPI flow.
- [ ] Create/confirm the PyPI Trusted Publisher with owner `jzhao0`, repository `math-modeling-competition-kit`, workflow `publish-pypi.yml`, environment `pypi`.
- [ ] Configure/review the GitHub `pypi` environment and use a manual approval/reviewer gate when available.
- [ ] Human explicitly approves the exact `v0.1.0a1` tag and external package publication.
- [ ] Create tag `v0.1.0a1` from the exact approved release commit.
- [ ] Verify tag-triggered `Release build` succeeds and archive audit is PASS.
- [ ] Verify wheel and sdist version/contents/hashes.
- [ ] Manually dispatch `Publish to PyPI` with `tag=v0.1.0a1` after Trusted Publisher configuration is verified.
- [ ] Verify PyPI upload succeeded through OIDC without a long-lived PyPI API token.
- [ ] Install from PyPI in a fresh environment and run `mmkit --help` plus scaffold/reproduce smoke.
- [ ] Create GitHub Release notes from `CHANGELOG.md` and link the exact tag/artifacts.

See `docs/PUBLISHING.md` for the exact trusted-publisher contract and fail-closed sequence.

## Hard stops

Do not create a public tag, GitHub Release, or PyPI upload when any of the following is true:

- release hardening or publication-readiness CI is not green;
- the package contains `migration_sources/`, private controller content, secrets, or embargoed future-competition material;
- version metadata does not match the intended tag;
- the tag does not point to the explicitly approved release commit;
- publication credentials/account ownership or PyPI namespace ownership are ambiguous;
- Trusted Publisher configuration does not exactly match the approved repository/workflow/environment;
- the human publication decision has not been given.

## Stable `v0.1.0` gate after alpha

Alpha publication does not automatically imply stable status. Before `v0.1.0`, require at minimum:

- fresh-install smoke from the published package;
- at least one bounded end-to-end public engineering example or equivalent dogfood record that does not use embargoed future-competition material;
- no known blocker-severity packaging or CLI defects;
- basic CLI contracts no longer changing incompatibly without release notes.
