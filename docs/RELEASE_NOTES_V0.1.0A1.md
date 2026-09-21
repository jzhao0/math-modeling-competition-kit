# MMKit v0.1.0a1 — First Public Alpha

This is the first public alpha of **Math Modeling Competition Kit (MMKit)**, a reusable engineering toolkit for mathematical modeling competitions.

## Highlights

- Reproducible competition workspace scaffolding
- Deterministic SHA-256 manifests
- Bounded clean-room reproduction
- Generic final-submission engineering gate
- Claim/evidence provenance locking
- Paper initialization, audit, and bounded build helpers
- Post-model-freeze runtime benchmarking
- Context-resilient multi-agent coordination

## Install

```bash
python -m pip install --pre math-modeling-competition-kit==0.1.0a1
```

Verify:

```bash
mmkit --help
mmkit-final-gate --help
python -c "import mmkit; print(mmkit.__version__)"
```

Expected version:

```text
0.1.0a1
```

## Release model

This alpha intentionally focuses on reusable engineering infrastructure rather than competition-specific algorithms or answer artifacts.

The public package excludes private contest material, active future-competition training, competition-specific tactics, and historical migration sources from distribution archives.

## Publishing

The package is published to PyPI through GitHub Actions using PyPI Trusted Publishing / OIDC and an explicit GitHub environment approval gate. No long-lived PyPI API token is required.

## PyPI

https://pypi.org/project/math-modeling-competition-kit/0.1.0a1/
