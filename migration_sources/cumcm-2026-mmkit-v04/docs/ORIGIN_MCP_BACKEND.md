# Optional Origin MCP Figure Backend

Status: **OPTIONAL / NOT YET VALIDATED ON THE ACTUAL CONTEST HOST**

MMKit v0.3 supports Origin/OriginPro as an optional high-presentation-quality backend. It is not a numerical truth source and is not required for the Python/R path to work.

## Audited upstream

Primary runtime candidate:

- `Ge-Shun/origin-mcp`
- pinned review commit: `fecb7226ed60d7651d921d2586eb9950bf16b618`
- license: MIT
- upstream requirements: Windows, licensed Origin/OriginPro, Python 3.10+
- advertised capabilities: worksheet/matrix import, 2D/3D/contour/statistical/specialized plots, fitting, signal processing, graph layout and publication export

Validation-pattern reference:

- `Yike-Ye/OriginLab-MCP`
- pinned review commit: `6e39f88c8a92da72c8b02f0b5e809779aeac34ba`
- license: MIT
- useful principle: verify what Origin actually executed, not only what the agent requested.

## MMKit role

Origin is preferred when it materially improves the competition-paper presentation, especially:

- 3D categorical columns;
- response/sensitivity surfaces and meshes;
- contour + projection combinations;
- fitting/response visualizations;
- polished multi-layer publication layouts.

`config/contest_visual.yaml` explicitly permits `PRESENTATION_3D`: visual depth can be decorative. A decorative depth dimension must not be labeled as a quantitative variable or used to imply nonexistent data.

## Truth / presentation split

```text
verified result CSV/JSON/table
        ↓
figure contract
        ↓
Python/R/Origin renderer
        ↓
visual QA
        ↓
paper PDF
```

The frozen result artifact is authoritative. If Origin rendering and the result artifact disagree, the figure is rejected or rebuilt; the result is never changed to match the picture.

## Pre-contest host validation

Do this before relying on Origin during the competition:

1. Confirm a licensed compatible Origin/OriginPro is installed on the Windows contest host.
2. Install the pinned/reviewed Origin MCP runtime using the upstream-supported installation route.
3. Start/configure the local authenticated bridge.
4. Run its status/doctor/ping checks.
5. Make one deterministic smoke figure from a tiny frozen CSV:
   - one 3D column chart (`PRESENTATION_3D`),
   - one surface/contour chart (`DATA_3D`).
6. Export to a paper-safe format and verify the values/labels against the CSV.
7. Save the reconstruction steps or editable Origin project/source.
8. Record the validated version in `docs/context/PROJECT_STATE.md`.

Do not fetch/install this dependency for the first time after the contest begins.

## Fallback

If Origin is unavailable or unstable, use the same frozen data with Python/matplotlib or R/ggplot2. The modeling pipeline must never be blocked by the optional renderer.

## Security

The reviewed primary project documents a localhost authenticated bridge. Treat its session token/handshake data as credentials; never put them in the MMKit repository, AI logs or support package.
