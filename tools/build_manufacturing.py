#!/usr/bin/env python3
"""Regenerate every fabrication + documentation output from the KiCad project.

One command rebuilds the JLCPCB fab package and the README visuals so a design
change never leaves stale outputs behind:

  fab (manufacturing/):
    gerbers/                       Gerber set (Protel extensions) + Excellon drill
    drv8313-board-gerbers.zip      the gerbers/ folder zipped, ready to upload
    drv8313-board-CPL.csv          pick-and-place (KiCad-native CSV, mm)
    drv8313-board-BOM.csv          grouped BOM with MPN + LCSC columns
    drv8313-board.step             STEP 3D model (3D models substituted in)
  images/:
    board-3d-{top,bottom}.png      raytraced 3D renders
    schematic.svg                  schematic
    pcb-{top,bottom}.svg           2D board plots

Usage:
    python tools/build_manufacturing.py            # everything
    python tools/build_manufacturing.py --fab      # fab package only
    python tools/build_manufacturing.py --images   # renders + SVGs only
    KICAD_CLI="/path/to/kicad-cli" python tools/build_manufacturing.py

Needs only kicad-cli (auto-located on Windows; override with $KICAD_CLI).
`pcb drc`/`sch erc` are deliberately NOT run here -- this tool only *generates*.
project.kicad_pro is snapshotted and restored, because kicad-cli rewrites it on
load (root-sheet registration, and `pcb drc` resets the custom min-via rules).
"""
import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJ = ROOT / "KiCad" / "project"
PCB = PROJ / "project.kicad_pcb"
SCH = PROJ / "project.kicad_sch"
PRO = PROJ / "project.kicad_pro"
MFG = ROOT / "manufacturing"
GERB = MFG / "gerbers"
IMG = ROOT / "images"

GERBER_LAYERS = ("F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,"
                 "F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts")
BOM_ARGS = [
    "--fields", "Reference,Value,Footprint,QUANTITY,Manufacturer Part,Supplier Part",
    "--labels", "Designator,Value,Footprint,Qty,MPN,LCSC",
    "--group-by", "Value,Footprint,Manufacturer Part,Supplier Part",
    "--ref-range-delimiter", "-", "--sort-field", "Reference",
]
RENDER_ARGS = ["--quality", "high", "--perspective", "--floor",
               "--width", "1568", "--height", "1176"]


def locate_cli():
    env = os.environ.get("KICAD_CLI")
    if env:
        return env
    for c in (r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe",
              "/usr/bin/kicad-cli", "kicad-cli"):
        if Path(c).exists() or shutil.which(c):
            return c
    return "kicad-cli"


CLI = locate_cli()


def run(args, label):
    print(f"  - {label}")
    r = subprocess.run([CLI] + [str(a) for a in args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.stderr.write((r.stdout or "")[-1000:] + "\n" + (r.stderr or "")[-1000:] + "\n")
        raise SystemExit(f"FAILED: {label} (exit {r.returncode})")


def build_fab():
    print("Fab package -> manufacturing/")
    GERB.mkdir(parents=True, exist_ok=True)
    run(["pcb", "export", "gerbers", "--output", str(GERB) + os.sep,
         "--layers", GERBER_LAYERS, PCB], "gerbers")
    run(["pcb", "export", "drill", "--output", str(GERB) + os.sep,
         "--format", "excellon", "--excellon-units", "mm", PCB], "drill (Excellon)")

    zpath = MFG / "drv8313-board-gerbers.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(GERB.iterdir()):
            if f.is_file():
                z.write(f, f.name)
    print(f"    zipped {sum(1 for _ in GERB.iterdir())} files -> {zpath.name}")

    run(["pcb", "export", "pos", "--output", MFG / "drv8313-board-CPL.csv",
         "--format", "csv", "--units", "mm", PCB], "CPL pick-and-place")
    run(["sch", "export", "bom", *BOM_ARGS,
         "--output", MFG / "drv8313-board-BOM.csv", SCH], "BOM (MPN + LCSC)")
    run(["pcb", "export", "step", "--subst-models", "--force",
         "--output", MFG / "drv8313-board.step", PCB], "STEP 3D model")


def build_images():
    print("Images -> images/")
    IMG.mkdir(exist_ok=True)
    run(["pcb", "render", "--output", IMG / "board-3d-top.png",
         "--side", "top", *RENDER_ARGS, PCB], "3D render (top)")
    run(["pcb", "render", "--output", IMG / "board-3d-bottom.png",
         "--side", "bottom", *RENDER_ARGS, PCB], "3D render (bottom)")

    tmp = IMG / "_schsvg_tmp"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir()
    run(["sch", "export", "svg", "--output", tmp, SCH], "schematic SVG")
    src = tmp / "project.svg"
    if src.exists():
        shutil.move(str(src), str(IMG / "schematic.svg"))
    shutil.rmtree(tmp, ignore_errors=True)

    run(["pcb", "export", "svg", "--output", IMG / "pcb-top.svg",
         "--mode-single", "--page-size-mode", "2", "--exclude-drawing-sheet",
         "--black-and-white", "--layers", "F.Cu,F.SilkS,F.Mask,Edge.Cuts", PCB],
        "PCB top SVG")
    run(["pcb", "export", "svg", "--output", IMG / "pcb-bottom.svg",
         "--mode-single", "--page-size-mode", "2", "--exclude-drawing-sheet",
         "--black-and-white", "--mirror",
         "--layers", "B.Cu,B.SilkS,B.Mask,Edge.Cuts", PCB], "PCB bottom SVG")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fab", action="store_true", help="fab package only")
    ap.add_argument("--images", action="store_true", help="renders + SVGs only")
    ap.add_argument("--no-restore-pro", action="store_true",
                    help="don't restore project.kicad_pro after kicad-cli edits it")
    args = ap.parse_args()
    do_fab = args.fab or not args.images
    do_img = args.images or not args.fab

    print(f"kicad-cli: {CLI}")
    pro_snapshot = PRO.read_bytes() if PRO.exists() else None
    try:
        if do_fab:
            build_fab()
        if do_img:
            build_images()
    finally:
        if pro_snapshot is not None and not args.no_restore_pro:
            if PRO.read_bytes() != pro_snapshot:
                PRO.write_bytes(pro_snapshot)
                print("  (restored project.kicad_pro)")
    print("Done.")


if __name__ == "__main__":
    main()
