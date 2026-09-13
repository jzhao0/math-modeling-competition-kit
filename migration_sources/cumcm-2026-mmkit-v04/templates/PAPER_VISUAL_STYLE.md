# Paper Visual Style

Purpose: make every paper figure reproducible, readable on A4, and tied to a concrete claim.

## Core rules

1. Figure = evidence, not decoration. Every main-text figure must support one explicit claim.
2. Prefer white background, restrained low-saturation colors, minimal grid, no unnecessary 3D effects.
3. Keep semantic colors stable across the paper. The same model/group keeps the same color everywhere.
4. Use vector PDF for line plots, model diagrams, ROC/PR curves, and other scalable graphics. Also export PNG at 450 dpi for preview/WPS compatibility.
5. Design at final print size. Labels must remain readable after insertion into A4 paper.
6. Prefer one strong figure to several redundant plots. Multi-panel figures are allowed only when panels answer one shared question.
7. Titles should normally live in the paper caption, not as large text inside the plotting area.
8. Units belong on axes and tables. Decimal precision must be consistent within each metric.
9. Every figure must be regenerable from saved data/results and a committed script. No irreplaceable manual edits.
10. Final figures go to `05_results/figures/final/`; exploratory figures stay outside that directory.

## Default typography

- Chinese: Microsoft YaHei / SimHei fallback.
- English/numbers: readable sans-serif in figures; math via STIX.
- Axis labels: about 10 pt.
- Tick labels / legends: about 9 pt.
- Never allow critical text below roughly 7.5 pt at final printed size.

## Default visual grammar

- Main curve: 1.8-2.2 pt.
- Secondary/baseline curve: 1.2-1.6 pt.
- Confidence/uncertainty bands: low alpha, no heavy border.
- Markers: sparse and small; do not mark every observation on dense curves.
- Grid: major grid only, subtle.
- Remove top/right spines unless they carry information.

## Figure roles

### Evidence Figure
Python/Matplotlib. Supports a numeric/model claim: fit, risk, uncertainty, ROC/PR, sensitivity, optimization result.

### Model Diagram
Draw.io/TikZ/Graphviz. Explains one model mechanism or dependency chain.

### Overview Figure
Draw.io/TikZ. Gives a one-page navigation map of the entire solution. Keep it simpler than the full workflow implementation.

## Main-text admission gate

A figure may enter the main paper only if all are true:

- [ ] `claim_supported` is explicit.
- [ ] source table/data is recorded.
- [ ] generation script is recorded.
- [ ] axes/units/legend are readable at final size.
- [ ] caption states what is shown, not merely the file contents.
- [ ] the paragraph immediately after/before the figure explains the decision or conclusion enabled by the figure.
- [ ] no redundant main-text figure supports the same claim better.

## CUMCM-specific restraint

Borrow information organization from strong MCM/ICM papers, not their decorative excess. Avoid dashboard-like blocks, excessive gradients, icon-heavy illustrations, or many high-saturation colors unless the problem itself requires an infographic.
