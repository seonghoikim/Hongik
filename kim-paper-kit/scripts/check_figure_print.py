#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_figure_print.py -- print-quality gate for paper figures.

Two independent checks (run either or both in one call):

 1) PNG check (--png)
    implied dpi = PNG pixel width / print width in inches
    PASS when the pixel width reaches the gate: ceil(print width / 72 x min dpi).
    At 368 pt and 300 dpi the exact value is 1533.3 px, so the gate is 1534 px.
    (A 1533 px PNG implies 299.9 dpi and must fail.)
    --gray-out writes a grayscale copy composited on white (black-and-white print test).
    Warns when the PNG has non-opaque pixels: check it on white (see pitfalls.md, SMask).

 2) Font check (--font-px with --canvas-px)
    effective pt = font px / canvas px x print width pt
    PASS when the SMALLEST label reaches --target-pt (default 8).
    Judge by the smallest font in the figure, never by the median.

Print width defaults to 368 pt (the thesis assembler width in the reference project).
Pass the width of the layout you actually print on:
  full text width (e.g. TKIPS two-column body 485 pt) or a single column (232.5 pt).

Examples:
  python check_figure_print.py --png figures_png/fig2.png
  python check_figure_print.py --font-px 26 --canvas-px 1700 --print-width-pt 368
  python check_figure_print.py --png fig2.png --print-width-pt 485 --gray-out fig2_gray.png
  python check_figure_print.py --font-px 37 --canvas-px 1700 --print-width-pt 368 --target-pt 8

Exit codes: 0 all requested checks pass, 2 at least one check fails, 1 usage or read error.
"""
import argparse
import math
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def effective_pt(font_px, canvas_px, print_width_pt):
    """Printed font size: the canvas is scaled down to print_width_pt."""
    return font_px / canvas_px * print_width_pt


def min_font_px(target_pt, canvas_px, print_width_pt):
    """Smallest on-canvas font size (px) that still prints at target_pt."""
    return target_pt * canvas_px / print_width_pt


def required_px(print_width_pt, min_dpi):
    """PNG pixel width needed for min_dpi at the given print width."""
    return print_width_pt / 72.0 * min_dpi


def check_png(path, print_width_pt, min_dpi, gray_out):
    from PIL import Image

    path = Path(path)
    if not path.is_file():
        print(f"[error] PNG not found: {path}")
        return None
    im = Image.open(path)
    w, h = im.size
    dpi = w / (print_width_pt / 72.0)
    gate = math.ceil(required_px(print_width_pt, min_dpi))  # 1534 px at 368 pt / 300 dpi
    ok = w >= gate
    print(f"[png] {path.name}: {w} x {h} px")
    print(f"[png] implied dpi at {print_width_pt:g} pt width: {dpi:.1f} "
          f"(needs >= {gate} px for {min_dpi:g} dpi)")
    print("[png] PASS" if ok else "[png] FAIL: raise the device scale or narrow the canvas, then re-render")

    rgba = im.convert("RGBA")
    alpha = rgba.getchannel("A")
    hist = alpha.histogram()
    non_opaque_share = sum(hist[:255]) / float(w * h)
    if non_opaque_share > 0:
        print(f"[png] note: {non_opaque_share * 100:.1f}% of pixels are not fully opaque (alpha < 255); "
              f"review on white (SMask/black-background check)")

    if gray_out:
        white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        flat = Image.alpha_composite(white, rgba).convert("L")
        Path(gray_out).parent.mkdir(parents=True, exist_ok=True)
        flat.save(gray_out)
        print(f"[png] grayscale preview written: {gray_out}")
    return ok


def check_font(font_px, canvas_px, print_width_pt, target_pt):
    eff = effective_pt(font_px, canvas_px, print_width_pt)
    need = min_font_px(target_pt, canvas_px, print_width_pt)
    ok = eff >= target_pt
    print(f"[font] effective size {eff:.2f} pt = {font_px:g} px / {canvas_px:g} px x {print_width_pt:g} pt")
    print(f"[font] smallest font for {target_pt:g} pt at this canvas: {need:.1f} px")
    print("[font] PASS" if ok else "[font] FAIL: enlarge the smallest label, shrink the canvas, or split the figure")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description="Print-quality gate for paper figures (see print-quality.md).")
    ap.add_argument("--png", help="PNG to check (pixel width -> implied dpi)")
    ap.add_argument("--gray-out", help="write a grayscale preview of --png to this path")
    ap.add_argument("--font-px", type=float, help="smallest font size on the canvas, in px")
    ap.add_argument("--canvas-px", type=float, help="canvas width in the same px unit")
    ap.add_argument("--print-width-pt", type=float, default=368.0,
                    help="printed width of the figure in pt (default: 368 = thesis assembler width "
                         "in the reference project; check your venue and pass it explicitly)")
    ap.add_argument("--min-dpi", type=float, default=300.0, help="dpi gate (default: 300)")
    ap.add_argument("--target-pt", type=float, default=8.0, help="minimum printed font size (default: 8)")
    args = ap.parse_args(argv)

    if not args.png and args.font_px is None:
        ap.print_usage()
        print("[error] give --png and/or --font-px with --canvas-px")
        return 1
    if args.font_px is not None and not args.canvas_px:
        print("[error] --font-px needs --canvas-px")
        return 1

    results = []
    if args.png:
        try:
            results.append(check_png(args.png, args.print_width_pt, args.min_dpi, args.gray_out))
        except ImportError:
            print("[error] Pillow is required: pip install pillow")
            return 1
    if args.font_px is not None:
        results.append(check_font(args.font_px, args.canvas_px, args.print_width_pt, args.target_pt))

    if None in results:
        return 1
    return 0 if all(results) else 2


if __name__ == "__main__":
    sys.exit(main())
