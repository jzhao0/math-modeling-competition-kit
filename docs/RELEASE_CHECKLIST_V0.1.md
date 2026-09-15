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
- [ ] Release-candidate PR has a final successful GitHub Actions run after all hardening changes.
- [ ] Human approves merging the release-candidate PR.

## External publication gate

The items below are intentionally **not** performed automatically by repository CI.

- [ ] Confirm the PyPI project namespace can be claimed by the intended maintainer account.
- [ ] Configure PyPI authentication / Trusted Publisher for this repository, or choose another approved publication path.
- [ ] Human explicitly approves the public tag and package publication.
- [ ] Create tag `v0.1.0a1` from the exact approved release commit.
- [ ] Verify tag-triggered `Release build` succeeds and archive audit is PASS.
- [ ] Verify wheel and sdist version/contents/hashes.
- [ ] Publish the exact approved wheel + sdist to PyPI if PyPI publication is desired.
- [ ] Install from PyPI in a fresh environment and run `mmkit --help` plus a scaffold/reproduce smoke.
- [ ] Create GitHub Release notes from `CHANGELOG.md` and link the exact tag/artifacts.

## Hard stops

Do not create a public tag, GitHub Release, or PyPI upload when any of the following is true:

- release PR CI is not green;
- the package contains `migration_sources/`, private controller content, secrets, or embargoed future-competition material;
- version metadata does not match the intended tag;
- publication credentials/account ownership are ambiguous;
- the human publication decision has not been given.

## Stable `v0.1.0` gate after alpha

Alpha publication does not automatically imply stable status. Before `v0.1.0`, require at minimum:

- fresh-install smoke from the published package;
- at least one bounded end-to-end public engineering example or equivalent dogfood record that does not use embargoed future-competition material;
- no known blocker-severity packaging or CLI defects;
- basic CLI contracts no longer changing incompatibly without release notes.
