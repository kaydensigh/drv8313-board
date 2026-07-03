#!/usr/bin/env python3
"""Render datasheet PDF pages to PNG images for visual (vision-model) reading.

Text extraction loses a datasheet's figures entirely -- and the reference
schematic you are supposed to wire from IS a figure. Render the page, look at
the image, and wire from what the figure actually shows, never from prose
text-extraction alone. (This board's DRV8313 datasheet is the cautionary tale:
its section 8.2.2.2.1 prose contradicts its own Figure 12 on the comparator
pins -- following the text wires COMPP/COMPN backwards.)

Uses PyMuPDF (fitz). Run with KiCad's bundled Python, where it is installed:

    & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tools\\render_datasheet.py docs\\datasheets\\drv8313.pdf 14
    ... render_datasheet.py file.pdf 13-15,20 --dpi 200
    ... render_datasheet.py file.pdf --toc          # find the right pages first

If fitz is missing: python -m pip install --user pymupdf

Page numbers are 1-based PDF pages (what a PDF viewer shows), which may differ
from the page numbers printed on the pages themselves.
"""
import argparse
import sys
import tempfile
from pathlib import Path

EXIT_OK, EXIT_ERROR = 0, 2


def parse_pages(spec, n_pages):
    """'14' | '13-15' | '1,3,7-9' | 'all' -> sorted 1-based page list."""
    if spec.strip().lower() == "all":
        return list(range(1, n_pages + 1))
    pages = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            pages.update(range(int(lo), int(hi) + 1))
        elif part:
            pages.add(int(part))
    bad = [p for p in pages if p < 1 or p > n_pages]
    if bad:
        raise ValueError(f"page(s) {bad} out of range 1..{n_pages}")
    return sorted(pages)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pdf", help="path to the PDF")
    ap.add_argument("pages", nargs="?", default=None,
                    help="pages to render: '14', '13-15,20', or 'all'")
    ap.add_argument("--dpi", type=int, default=150,
                    help="render resolution (default 150; 200+ for dense figures)")
    ap.add_argument("--out-dir", default=None,
                    help="output directory (default: <temp>/datasheet-render/<stem>/)")
    ap.add_argument("--toc", action="store_true",
                    help="print the PDF table of contents (level, title, page) and exit")
    args = ap.parse_args()

    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("ERROR: PyMuPDF not available in this interpreter.\n"
              "Run with KiCad's bundled Python, or install it:\n"
              "  python -m pip install --user pymupdf", file=sys.stderr)
        return EXIT_ERROR

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"ERROR: {pdf_path} not found", file=sys.stderr)
        return EXIT_ERROR

    doc = fitz.open(str(pdf_path))
    print(f"{pdf_path.name}: {len(doc)} pages")

    if args.toc:
        toc = doc.get_toc()
        if not toc:
            print("(no table of contents in this PDF)")
        for level, title, page in toc:
            print(f"{'  ' * (level - 1)}p.{page:>3}  {title}")
        return EXIT_OK

    if not args.pages:
        print("ERROR: give a page spec (e.g. 14, 13-15, all) or --toc", file=sys.stderr)
        return EXIT_ERROR

    try:
        pages = parse_pages(args.pages, len(doc))
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_ERROR

    out_dir = Path(args.out_dir) if args.out_dir else (
        Path(tempfile.gettempdir()) / "datasheet-render" / pdf_path.stem)
    out_dir.mkdir(parents=True, exist_ok=True)

    for p in pages:
        pix = doc[p - 1].get_pixmap(dpi=args.dpi)
        out = out_dir / f"{pdf_path.stem}-p{p:03d}.png"
        pix.save(str(out))
        print(f"  p.{p}: {out}  ({pix.width}x{pix.height})")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
