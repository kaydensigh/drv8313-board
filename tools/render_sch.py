#!/usr/bin/env python3
"""Render the schematic to a PNG so it can be LOOKED AT, not just netlist-checked.

ERC and the netlist prove a schematic is *correct*; only looking at a render
proves it is *readable* (no overlapping value/ref text, no floating-looking
connectors, sensible flow). Render + inspect after every placement/label edit
-- treat this as the visual analogue of running DRC after every copper edit.

Needs kicad-cli (SVG export) and ImageMagick's `magick` (rasterize). Any
Python 3 works -- this only shells out.

    python tools/render_sch.py                       # whole sheet, default density
    python tools/render_sch.py --density 300         # zoom for label-level detail
    python tools/render_sch.py --crop 800x600+200+150   # px crop of the raster
    python tools/render_sch.py --sch path/to/x.kicad_sch --out preview.png
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXIT_OK, EXIT_ERROR = 0, 2

CLI_CANDIDATES = (
    r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe",
    r"C:\Program Files\KiCad\9.0\bin\kicad-cli.exe",
    "/usr/bin/kicad-cli",
    "/usr/local/bin/kicad-cli",
    "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
    "kicad-cli",
)


def locate_cli():
    cli = os.environ.get("KICAD_CLI")
    if cli:
        return cli
    for c in CLI_CANDIDATES:
        if Path(c).exists() or shutil.which(c):
            return c
    return None


def find_sch(explicit):
    """--sch flag, else the unique *.kicad_sch under cwd (skipping backups)."""
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    hits = [p for p in Path.cwd().rglob("*.kicad_sch")
            if not p.name.startswith("_autosave")
            and not any(part.startswith((".", "_scratch")) or part.endswith("-backups")
                        for part in p.parts)]
    if len(hits) == 1:
        return hits[0]
    if hits:
        print(f"ERROR: multiple schematics found, pass --sch:\n  " +
              "\n  ".join(str(h) for h in hits), file=sys.stderr)
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sch", default=None, help="path to the .kicad_sch (default: auto-discover)")
    ap.add_argument("--out", default=None,
                    help="output PNG path (default: <temp>/kicad-render/<stem>.png)")
    ap.add_argument("--density", type=int, default=150,
                    help="raster density (default 150 ~ full-sheet overview; 300+ to read labels)")
    ap.add_argument("--crop", default=None, metavar="WxH+X+Y",
                    help="ImageMagick pixel crop applied after rasterizing")
    ap.add_argument("--no-frame", action="store_true",
                    help="exclude the drawing sheet (title block / frame)")
    args = ap.parse_args()

    cli = locate_cli()
    if not cli:
        print("ERROR: kicad-cli not found (set $KICAD_CLI)", file=sys.stderr)
        return EXIT_ERROR
    magick = shutil.which("magick")
    if not magick:
        print("ERROR: ImageMagick 'magick' not found on PATH", file=sys.stderr)
        return EXIT_ERROR

    sch = find_sch(args.sch)
    if not sch:
        print("ERROR: no .kicad_sch found (pass --sch)", file=sys.stderr)
        return EXIT_ERROR

    out = Path(args.out) if args.out else (
        Path(tempfile.gettempdir()) / "kicad-render" / f"{sch.stem}.png")
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        cmd = [cli, "sch", "export", "svg", "--output", td]
        if args.no_frame:
            cmd.append("--exclude-drawing-sheet")
        cmd.append(str(sch))
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"ERROR: svg export failed:\n{r.stdout}\n{r.stderr}", file=sys.stderr)
            return EXIT_ERROR
        svgs = sorted(Path(td).glob("*.svg"))
        if not svgs:
            print("ERROR: export produced no SVG", file=sys.stderr)
            return EXIT_ERROR

        outputs = []
        for i, svg in enumerate(svgs):
            # one PNG per sheet; single-sheet schematics get the plain name
            dst = out if len(svgs) == 1 else out.with_name(f"{out.stem}-{svg.stem}{out.suffix}")
            mcmd = [magick, "-density", str(args.density), str(svg),
                    "-background", "white", "-flatten"]
            if args.crop:
                mcmd += ["-crop", args.crop, "+repage"]
            mcmd.append(str(dst))
            r = subprocess.run(mcmd, capture_output=True, text=True)
            if r.returncode != 0:
                print(f"ERROR: rasterize failed:\n{r.stderr}", file=sys.stderr)
                return EXIT_ERROR
            outputs.append(dst)

    for dst in outputs:
        ident = subprocess.run([magick, "identify", str(dst)],
                               capture_output=True, text=True).stdout.strip()
        print(dst)
        if ident:
            print(f"  {ident}")
    print("\nNow READ the PNG and check: no overlapping text, no text through symbol"
          "\nbodies, connectors visibly wired, left-to-right flow. See also sch_lint.py.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
