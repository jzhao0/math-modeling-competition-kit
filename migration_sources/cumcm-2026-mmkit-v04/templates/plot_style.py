"""Competition-paper plotting defaults for CUMCM workspaces.

Keep this module lightweight and reproducible. Model scripts should emit data first;
final paper figures should be rendered from saved tables/results using this style.
"""
from __future__ import annotations

from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt

# Semantic palette: keep meanings stable across the whole paper.
PALETTE = {
    "primary": "#3B6FB6",
    "secondary": "#D97A45",
    "tertiary": "#5A9A73",
    "neutral": "#6E7781",
    "danger": "#B84A4A",
    "group_low": "#4C78A8",
    "group_mid": "#F2B134",
    "group_high": "#E45756",
    "uncertainty": "#9AA4B2",
}


def apply_paper_style() -> None:
    """Apply restrained, print-friendly defaults without external style packages."""
    mpl.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": 450,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.04,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "font.family": "sans-serif",
            "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial", "DejaVu Sans"],
            "mathtext.fontset": "stix",
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
            "lines.linewidth": 1.8,
            "lines.markersize": 5,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.18,
            "grid.linewidth": 0.6,
            "legend.frameon": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def save_figure(fig: plt.Figure, output_base: str | Path, *, png_dpi: int = 450) -> tuple[Path, Path]:
    """Save both vector PDF and high-resolution PNG from one deterministic figure."""
    base = Path(output_base)
    base.parent.mkdir(parents=True, exist_ok=True)
    pdf = base.with_suffix(".pdf")
    png = base.with_suffix(".png")
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(png, dpi=png_dpi, bbox_inches="tight")
    return pdf, png


def label_panel(ax: plt.Axes, label: str) -> None:
    """Add a consistent panel label such as (a), (b), (c)."""
    ax.text(-0.10, 1.03, label, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom")
