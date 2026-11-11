#!/usr/bin/env python3
"""
Render every slide of a .pptx to a JPEG image, for visual QA.
Standalone version (just calls soffice + pdftoppm directly, no sandbox shim needed
on a normal VPS/Docker; that workaround only applies to Anthropic's own sandboxed
environment where AF_UNIX sockets can be restricted).

Usage: python render_qa.py deck.pptx [--dpi 150] [--outdir renders]

Produces: <outdir>/slide-1.jpg, slide-2.jpg, ... (one per slide)
"""
import argparse
import subprocess
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input", help="Input .pptx file")
    p.add_argument("--dpi", type=int, default=150)
    p.add_argument("--outdir", default="renders")
    args = p.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print("Converting to PDF...")
    result = subprocess.run(
        ["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(outdir), str(input_path)],
        capture_output=True, text=True,
    )
    pdf_path = outdir / f"{input_path.stem}.pdf"
    if result.returncode != 0 or not pdf_path.exists():
        print("PDF conversion failed:", result.stderr or result.stdout, file=sys.stderr)
        sys.exit(1)

    print("Rendering pages to JPEG...")
    result = subprocess.run(
        ["pdftoppm", "-jpeg", "-r", str(args.dpi), str(pdf_path), str(outdir / "slide")],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("Image rendering failed:", result.stderr, file=sys.stderr)
        sys.exit(1)

    images = sorted(outdir.glob("slide-*.jpg"))
    print(f"Rendered {len(images)} slide(s) to {outdir}/:")
    for img in images:
        print(f"  {img}")


if __name__ == "__main__":
    main()
