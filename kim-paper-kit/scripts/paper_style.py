# -*- coding: utf-8 -*-
"""
paper_style.py -- matplotlib preset for paper data plots (line, bar, scatter, heatmap).

Generalized from a project preset. No hard-coded drive or user paths.

Usage (every plot script):
    import sys; sys.path.insert(0, r"<KIT>/scripts")
    import paper_style                       # importing applies the rcParams
    fig, ax = paper_style.new_figure(16, 9) # width, height in cm
    ...plot...
    paper_style.save(fig, "fig9_metric")    # writes SVG + PNG (300 dpi) under FIG_ROOT

Output folder:
    FIG_ROOT environment variable, or the current working directory when unset.
    Files go to <FIG_ROOT>/figures_svg/<name>.svg and <FIG_ROOT>/figures_png/<name>.png

Conventions (see references/figure-style.md, tool-routing.md):
  * Okabe-Ito colour-blind safe palette; the yellow is last because it is weak on white.
  * Times-like serif text with a Korean fallback; SVG keeps text as text (svg.fonttype none).
  * Diagrams (trees, matrices, layouts) are not plots: use the black / one-red / grey
    rule from figure-style.md instead of this palette.
  * savefig uses bbox="tight", which crops the margins. The PNG pixel width is therefore
    not exactly width_cm / 2.54 x 300. Measure it with check_figure_print.py --png.
  * Set the figure width to the printed width (368 pt = 12.98 cm in the reference layout).
    Then a font size in pt prints at about the same size when the file is inserted at that
    width (the bbox crop makes the final scale slightly larger). See print-quality.md, section 1.
"""
import os
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from cycler import cycler

# Okabe-Ito colour-blind safe palette (yellow last)
OKABE_ITO = ["#0072B2", "#D55E00", "#009E73", "#CC79A7",
             "#56B4E9", "#E69F00", "#000000", "#F0E442"]

FIG_ROOT = Path(os.environ.get("FIG_ROOT", os.getcwd()))
SVG_DIR = FIG_ROOT / "figures_svg"
PNG_DIR = FIG_ROOT / "figures_png"

mpl.rcParams.update({
    # font: serif to match a Times body text; Korean falls back to a Gothic face
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Malgun Gothic", "DejaVu Serif"],
    "mathtext.fontset": "stix",          # Times-like math, e.g. $L_{fas}$
    "axes.unicode_minus": False,
    # size system: aim for 9-10 pt after the figure is scaled to column width
    "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10,
    "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.fontsize": 9,
    # lines and markers
    "lines.linewidth": 1.6, "lines.markersize": 5,
    "axes.prop_cycle": cycler(color=OKABE_ITO),
    # axes
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.8, "axes.grid": True,
    "grid.alpha": 0.30, "grid.linewidth": 0.6, "grid.linestyle": "-",
    "legend.frameon": False,
    # output
    "figure.dpi": 100, "savefig.dpi": 300, "savefig.bbox": "tight",
    "svg.fonttype": "none",
})


def save(fig, name, svg=True, png=True):
    """Save SVG (vector, Word-friendly) and PNG (300 dpi). name has no extension.

    Returns a dict with the written paths. Existing files with the same name are
    overwritten: the source script is the record, so regenerate freely during drafting.
    For a confirmed or submitted version, save under a new name (_v2, _v3 ...) instead.
    """
    out = {}
    if svg:
        SVG_DIR.mkdir(parents=True, exist_ok=True)
        p = SVG_DIR / f"{name}.svg"
        fig.savefig(p, format="svg")
        out["svg"] = str(p)
    if png:
        PNG_DIR.mkdir(parents=True, exist_ok=True)
        p = PNG_DIR / f"{name}.png"
        fig.savefig(p, format="png")
        out["png"] = str(p)
    return out


def new_figure(width_cm=16.0, height_cm=9.0):
    """Figure sized in cm. The 16 cm default approximates the reference project's body
    width; take the real width from the venue's author guide and pass it explicitly."""
    cm = 1 / 2.54
    return plt.subplots(figsize=(width_cm * cm, height_cm * cm))
