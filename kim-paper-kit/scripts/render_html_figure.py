#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_html_figure.py -- render an HTML/CSS/SVG figure to a high-resolution PNG.

  * no hard-coded paths; no required #canvas element
  * captures one element chosen by CSS selector (default ".container");
    falls back to the whole viewport when the selector is absent
  * device scale factor is a parameter (default 3)
  * prints the PNG pixel width and exits 2 below the print gate
    (default 1534 px = 368 pt print width at 300 dpi, rounded up from 1533.3;
     see references/print-quality.md). check_figure_print.py uses the same gate.

Usage:
  python render_html_figure.py <input.html> <output.png> [options]

Examples:
  python render_html_figure.py figures_html/fig2.html figures_png/fig2.png
  python render_html_figure.py fig.html fig.png --selector "#figure" --scale 3 --bg white
  python render_html_figure.py fig.html fig.png --min-width 0    # disable the gate

Setup (once):
  pip install playwright pillow
  python -m playwright install chromium

Notes:
  * PNG pixel width = CSS width of the captured element x --scale.
    When you compute a print or slide size, divide by --scale first.
  * Put the page background in the HTML (body { background: #fff }) when --bg white.
  * Wrap text in a font stack that exists on the target machine
    (e.g. 'Times New Roman', 'Malgun Gothic') so the render matches the body text.
"""
import argparse
import math
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PRINT_GATE_PX = math.ceil(368 / 72 * 300)  # 1534: 368 pt at 300 dpi = 1533.3 px, rounded up


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="Render an HTML figure to PNG with Playwright (Chromium).")
    ap.add_argument("html", help="input .html file")
    ap.add_argument("png", help="output .png file (its folder must exist)")
    ap.add_argument("--selector", default=".container",
                    help="CSS selector of the element to capture (default: .container). "
                         "If not found, the whole viewport is captured.")
    ap.add_argument("--viewport-width", type=int, default=1700,
                    help="layout viewport width in CSS px (default: 1700)")
    ap.add_argument("--viewport-height", type=int, default=1200,
                    help="layout viewport height in CSS px (default: 1200)")
    ap.add_argument("--scale", type=float, default=3.0,
                    help="device scale factor (default: 3)")
    ap.add_argument("--bg", choices=["white", "transparent"], default="white",
                    help="white = capture the page as rendered (Chromium default background is white); "
                         "transparent = omit the background")
    ap.add_argument("--min-width", type=int, default=PRINT_GATE_PX,
                    help=f"exit 2 if the PNG pixel width is below this (default: {PRINT_GATE_PX}; 0 disables)")
    ap.add_argument("--chromium-path", default=os.environ.get("CHROMIUM_PATH"),
                    help="existing chromium executable to use instead of Playwright's bundled one "
                         "(also read from env CHROMIUM_PATH). Use when the bundled browser is missing.")
    return ap.parse_args(argv)


def render(html_path, png_path, selector, vw, vh, scale, transparent, chromium_path=None):
    """Render one element (or the viewport) to png_path. Returns a short description."""
    from playwright.sync_api import sync_playwright

    url = Path(html_path).resolve().as_uri()
    with sync_playwright() as pw:
        launch_kwargs = {"executable_path": chromium_path} if chromium_path else {}
        browser = pw.chromium.launch(**launch_kwargs)
        try:
            page = browser.new_page(viewport={"width": vw, "height": vh},
                                    device_scale_factor=scale)
            page.goto(url, wait_until="load")
            # wait for web fonts before capture, then let SVG/CSS layout settle
            page.evaluate("() => document.fonts.ready.then(() => true)")
            page.wait_for_timeout(150)
            locator = page.locator(selector)
            if locator.count() > 0:
                locator.first.screenshot(path=png_path, omit_background=transparent)
                return f"element '{selector}'"
            print(f"[warn] selector '{selector}' not found; capturing the viewport instead")
            page.screenshot(path=png_path, omit_background=transparent)
            return "viewport"
        finally:
            browser.close()


def image_size(path):
    """Return (width, height) in px, or None when Pillow is not installed."""
    try:
        from PIL import Image
    except ImportError:
        return None
    with Image.open(path) as im:
        return im.size


def main(argv=None):
    args = parse_args(argv)
    html = Path(args.html)
    png = Path(args.png)
    if not html.is_file():
        print(f"[error] input not found: {html}")
        return 1
    if not png.parent.is_dir():
        print(f"[error] output folder does not exist: {png.parent}")
        return 1
    try:
        target = render(str(html), str(png), args.selector, args.viewport_width,
                        args.viewport_height, args.scale, args.bg == "transparent",
                        args.chromium_path)
    except ImportError:
        print("[error] playwright is not installed: pip install playwright && python -m playwright install chromium")
        return 1
    except Exception as exc:  # launch failures: missing browser build, bad --chromium-path
        print(f"[error] browser launch/render failed: {str(exc).splitlines()[0]}")
        print("        run: python -m playwright install chromium  (or pass --chromium-path)")
        return 1
    print(f"[ok] rendered {target} -> {png}")

    size = image_size(png)
    if size is None:
        print("[warn] Pillow not installed; pixel gate skipped (pip install pillow)")
        return 0
    width_px, height_px = size
    print(f"[info] PNG size: {width_px} x {height_px} px (device scale {args.scale})")
    if args.min_width:
        if width_px < args.min_width:
            print(f"[fail] width {width_px} px < gate {args.min_width} px. "
                  f"Raise --scale or narrow the canvas, then re-render.")
            return 2
        print(f"[pass] width gate {args.min_width} px")
    return 0


if __name__ == "__main__":
    sys.exit(main())
