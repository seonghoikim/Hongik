#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_pdf_figures.py -- get figures out of a PDF without losing transparency,
and render pages for visual comparison or for scanned PDFs.

Two jobs:
 1) --images : extract embedded raster images. Each SMask (alpha) is composited
               onto white. Plain extraction leaves transparent areas black, which
               hides black text, lines and arrows (see pitfalls.md, SMask case).
 2) --render-pages / --clip : render pages (or a clip rectangle) to PNG.
               Use it to compare with the extracted image, or to read a scanned
               PDF that has no text layer (the Read tool cannot display PDF pages here).

Existing output files are never overwritten: the script writes name_v2.png,
name_v3.png ... instead (project rule: no overwrite).

Usage:
  python extract_pdf_figures.py paper.pdf out_dir --images
  python extract_pdf_figures.py paper.pdf out_dir --render-pages 3,5 --dpi 190
  python extract_pdf_figures.py paper.pdf out_dir --render-pages 4 --dpi 520 --clip 50,80,550,400

Notes:
  * Page numbers are 1-based. --clip is x0,y0,x1,y1 in PDF points from the top-left corner.
  * Vector figures are not images: render them with --render-pages / --clip.
  * Requires: pip install pymupdf pillow   (PyMuPDF is imported as 'fitz')
"""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def unique_path(path: Path) -> Path:
    """Return path, or path_v2, path_v3 ... when it already exists (no overwrite)."""
    if not path.exists():
        return path
    n = 2
    while True:
        cand = path.with_name(f"{path.stem}_v{n}{path.suffix}")
        if not cand.exists():
            return cand
        n += 1


def pix_to_pil(pix):
    """Return (RGB image, alpha image or None) from a PyMuPDF pixmap."""
    from PIL import Image

    w, h = pix.width, pix.height
    if pix.n == 1:                                   # grayscale
        return Image.frombytes("L", (w, h), pix.samples).convert("RGB"), None
    if pix.n == 3:                                   # RGB
        return Image.frombytes("RGB", (w, h), pix.samples), None
    if pix.n == 4 and not pix.alpha:                 # CMYK
        return Image.frombytes("CMYK", (w, h), pix.samples).convert("RGB"), None
    if pix.n == 4 and pix.alpha:                     # RGBA
        rgba = Image.frombytes("RGBA", (w, h), pix.samples)
        return rgba.convert("RGB"), rgba.getchannel("A")
    if pix.n == 2:                                   # gray + alpha
        la = Image.frombytes("LA", (w, h), pix.samples)
        return la.getchannel("L").convert("RGB"), la.getchannel("A")
    raise ValueError(f"unsupported pixmap: n={pix.n} alpha={pix.alpha}")


def extract_image(doc, xref, smask_xref):
    """Extract one image; composite its SMask onto a white background."""
    import fitz
    from PIL import Image

    base = fitz.Pixmap(doc, xref)
    rgb, alpha = pix_to_pil(base)
    if smask_xref:
        mask_pix = fitz.Pixmap(doc, smask_xref)
        mask = Image.frombytes("L", (mask_pix.width, mask_pix.height), mask_pix.samples)
        if mask.size != rgb.size:
            mask = mask.resize(rgb.size)
        if alpha is None:
            alpha = mask
        else:
            from PIL import ImageChops
            alpha = ImageChops.multiply(alpha, mask)
    if alpha is None:
        return rgb
    white = Image.new("RGB", rgb.size, (255, 255, 255))
    return Image.composite(rgb, white, alpha)     # rgb * a + white * (1 - a)


def export_images(doc, out_dir, min_size):
    count = 0
    for page_index in range(len(doc)):
        page = doc[page_index]
        for img in page.get_images(full=True):
            xref, smask = img[0], img[1]
            width, height = img[2], img[3]
            if min(width, height) < min_size:
                continue
            out = unique_path(out_dir / f"p{page_index + 1:03d}_x{xref}.png")
            try:
                extract_image(doc, xref, smask).save(out)
            except Exception as exc:  # keep going; report the image that failed
                print(f"[warn] page {page_index + 1} xref {xref}: {exc}")
                continue
            masked = " (SMask composited on white)" if smask else ""
            print(f"[img] page {page_index + 1}: {width}x{height} -> {out.name}{masked}")
            count += 1
    return count


def render_pages(doc, out_dir, pages, dpi, clip):
    import fitz

    rect = None
    if clip:
        x0, y0, x1, y1 = [float(v) for v in clip.split(",")]
        rect = fitz.Rect(x0, y0, x1, y1)
    written = 0
    for number in pages:
        if not 1 <= number <= len(doc):
            print(f"[warn] page {number} is outside 1..{len(doc)}; skipped")
            continue
        pix = doc[number - 1].get_pixmap(dpi=dpi, clip=rect)  # white background, alpha off
        suffix = "_clip" if rect else ""
        out = unique_path(out_dir / f"page{number:03d}_{dpi}dpi{suffix}.png")
        pix.save(str(out))
        print(f"[render] page {number} at {dpi} dpi: {pix.width}x{pix.height} px -> {out.name}")
        written += 1
    return written


def parse_pages(text):
    pages = []
    for part in text.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            pages.extend(range(int(a), int(b) + 1))
        elif part:
            pages.append(int(part))
    return pages


def main(argv=None):
    ap = argparse.ArgumentParser(description="Extract figures from a PDF (SMask-safe) and render pages.")
    ap.add_argument("pdf", help="input PDF")
    ap.add_argument("out_dir", help="output folder (created if missing)")
    ap.add_argument("--images", action="store_true", help="extract embedded images with SMask composited")
    ap.add_argument("--min-size", type=int, default=0,
                    help="skip images whose smaller side is below this many px (default: 0)")
    ap.add_argument("--render-pages", help="pages to render, e.g. 3,5 or 2-4 (1-based)")
    ap.add_argument("--dpi", type=int, default=190, help="render resolution (default: 190)")
    ap.add_argument("--clip", help="x0,y0,x1,y1 in PDF points, applied to --render-pages")
    args = ap.parse_args(argv)

    if not (args.images or args.render_pages):
        ap.print_usage()
        print("[error] choose --images and/or --render-pages")
        return 1

    try:
        import fitz
    except ImportError:
        print("[error] PyMuPDF is required: pip install pymupdf")
        return 1
    try:
        from PIL import Image  # noqa: F401  (needed for --images)
    except ImportError:
        if args.images:
            print("[error] Pillow is required for --images: pip install pillow")
            return 1

    try:  # validate options before touching the file system
        pages = parse_pages(args.render_pages) if args.render_pages else []
        if args.clip:
            if len(args.clip.split(",")) != 4:
                raise ValueError("clip needs four numbers")
            [float(v) for v in args.clip.split(",")]
    except ValueError:
        print("[error] --render-pages takes e.g. 3,5 or 2-4; --clip takes x0,y0,x1,y1 in PDF points")
        return 1

    pdf_path = Path(args.pdf)
    if not pdf_path.is_file():
        print(f"[error] PDF not found: {pdf_path}")
        return 1
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    print(f"[info] {pdf_path.name}: {len(doc)} pages")
    if args.images:
        n = export_images(doc, out_dir, args.min_size)
        print(f"[info] images written: {n}")
    if args.render_pages:
        n = render_pages(doc, out_dir, pages, args.dpi, args.clip)
        print(f"[info] pages rendered: {n}")
    doc.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
