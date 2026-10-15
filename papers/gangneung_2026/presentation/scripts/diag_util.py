"""Drawing helpers for box-and-arrow diagrams (inch coordinates, 1 unit = 1 inch)."""
from __future__ import annotations

import unicodedata

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon

from common import BLACK, WHITE

MIN = 18


def canvas(w, h):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return fig, ax


def rbox(ax, x, y, w, h, fc=WHITE, ec=BLACK, lw=2.0, r=0.12, ls="-", z=1):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw,
                                linestyle=ls, zorder=z))


def box(ax, x, y, w, h, title, sub=None, fc=WHITE, ec=BLACK, tc=BLACK, fs=20, sfs=MIN, lw=2.0, r=0.12,
        sub_color=None, gap=0.12):
    rbox(ax, x, y, w, h, fc=fc, ec=ec, lw=lw, r=r)
    if sub:
        n_sub = sub.count("\n") + 1
        th, sh = fs / 72 * 1.25, sfs / 72 * 1.35 * n_sub
        top = y + h / 2 + (th + gap + sh) / 2
        ax.text(x + w / 2, top - th / 2, title, ha="center", va="center", fontsize=fs, fontweight="bold", color=tc)
        ax.text(x + w / 2, top - th - gap - sh / 2, sub, ha="center", va="center", fontsize=sfs,
                color=sub_color or tc, linespacing=1.3)
    else:
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=fs, fontweight="bold", color=tc,
                linespacing=1.25)


def arrow(ax, p, q, color=BLACK, lw=2.5, ms=22, ls="-", rad=0.0, style="-|>"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=ms, color=color, lw=lw, linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0, zorder=3))


def path_arrow(ax, pts, color=BLACK, lw=2.5):
    xs, ys = zip(*pts)
    ax.plot(xs[:-1], ys[:-1], color=color, lw=lw, solid_capstyle="butt", zorder=3)
    arrow(ax, pts[-2], pts[-1], color=color, lw=lw)


def badge(ax, x, y, text, r=0.27, fc=BLACK, tc=WHITE, fs=MIN):
    ax.add_patch(Circle((x, y), r, fc=fc, ec=fc, zorder=5))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, fontweight="bold", color=tc, zorder=6)


def diamond(ax, cx, cy, w, h, text, fs=MIN, ec=BLACK):
    ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)], closed=True,
                         fc=WHITE, ec=ec, lw=2))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, fontweight="bold", linespacing=1.2)


def cw(ch):
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") or "가" <= ch <= "힣" else 1.1


def wrap(text, width):
    lines = []
    for para in text.split("\n"):
        cur, n = "", 0
        for word in para.split(" "):
            w = sum(cw(c) for c in word) + 1
            if n + w > width and cur:
                lines.append(cur.rstrip())
                cur, n = "", 0
            cur += word + " "
            n += w
        lines.append(cur.rstrip())
    return lines


def chars_for(width_in, fs):
    """Width units (Hangul=2) that fit in width_in inches at font size fs."""
    return int(width_in / (fs / 72 * 0.47))


def textblock(ax, x, y, width_in, segments, fs=MIN, lh=1.42, weight="normal"):
    """Draw wrapped text (list of (text, color)) top-down from y; returns new y."""
    step = fs / 72 * lh
    for text, color in segments:
        for ln in wrap(text, chars_for(width_in, fs)):
            ax.text(x, y, ln, fontsize=fs, color=color or BLACK, va="top", fontweight=weight)
            y -= step
    return y


def measure(width_in, segments, fs=MIN, lh=1.42):
    n = sum(len(wrap(t, chars_for(width_in, fs))) for t, _ in segments)
    return n * fs / 72 * lh


def bubble(ax, x, y, w, segments, fc, ec, fs=MIN, pad=0.16, lw=1.6, r=0.12):
    """Rounded box sized to wrapped text, top-left at (x, y). Returns bottom y."""
    h = measure(w - 2 * pad, segments, fs) + 2 * pad
    rbox(ax, x, y - h, w, h, fc=fc, ec=ec, lw=lw, r=r)
    textblock(ax, x + pad, y - pad, w - 2 * pad, segments, fs)
    return y - h
