#!/usr/bin/env python3
"""Bump the board version (and optionally the date) printed in the PCB silkscreen.

The board carries its version as silk text -- e.g. "v1.0" on the front and
"Board v1.0" on the back -- plus an "MM/YY" date stamp. This rewrites the
`vN.M` token wherever it appears on a silk layer (front or back), preserving
any surrounding label like "Board ". Edits are by `SetText`, which persists
across SaveBoard; copper/geometry are untouched.

Usage:
    python tools/set_silk_version.py --show          # list current silk version/date
    python tools/set_silk_version.py 2.1             # set version -> v2.1
    python tools/set_silk_version.py 2.1 --date 09/26
    python tools/set_silk_version.py 2.1 --date auto # use this month (MM/YY)

Only edits silk *text*; does not touch README/docs version references.
Run with KiCad's bundled Python:
    & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tools/set_silk_version.py 2.1
"""
import argparse
import re
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "KiCad" / "project" / "project.kicad_pcb"

VER_RE = re.compile(r"v\d+\.\d+", re.IGNORECASE)      # the version token
DATE_RE = re.compile(r"\b\d{1,2}/\d{2}\b")            # an MM/YY date token


def silk_texts(board):
    """All board-level PCB_TEXT items on a silk layer."""
    silk = {pcbnew.F_SilkS, pcbnew.B_SilkS}
    out = []
    for d in list(board.GetDrawings()):
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() in silk:
            out.append(d)
    return out


def layer_name(board, item):
    return board.GetLayerName(item.GetLayer())


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("version", nargs="?",
                    help="new version, e.g. 2.1 (a leading 'v' is optional)")
    ap.add_argument("--date", default=None,
                    help="new MM/YY date stamp, or 'auto' for the current month")
    ap.add_argument("--show", action="store_true",
                    help="just print the current silk version/date text")
    args = ap.parse_args()

    board = pcbnew.LoadBoard(str(PCB))
    texts = silk_texts(board)

    if args.show or not (args.version or args.date):
        print("Silk text with a version or date token:")
        found = False
        for t in texts:
            s = t.GetText()
            if VER_RE.search(s) or DATE_RE.search(s):
                print(f"  [{layer_name(board, t):8}] {s!r}")
                found = True
        if not found:
            print("  (none found)")
        return

    new_ver = None
    if args.version:
        v = args.version.lstrip("vV")
        if not re.fullmatch(r"\d+\.\d+", v):
            sys.exit(f"version must look like N.M (got {args.version!r})")
        new_ver = "v" + v

    new_date = args.date
    if new_date == "auto":
        import datetime
        new_date = datetime.date.today().strftime("%m/%y")
    if new_date and not DATE_RE.fullmatch(new_date):
        sys.exit(f"--date must look like MM/YY (got {args.date!r})")

    changed = 0
    for t in texts:
        s = t.GetText()
        ns = s
        if new_ver and VER_RE.search(ns):
            ns = VER_RE.sub(new_ver, ns)
        if new_date and DATE_RE.search(ns):
            ns = DATE_RE.sub(new_date, ns)
        if ns != s:
            print(f"  [{layer_name(board, t):8}] {s!r} -> {ns!r}")
            t.SetText(ns)
            changed += 1

    if not changed:
        print("No version/date silk text matched -- nothing changed.")
        return
    pcbnew.SaveBoard(str(PCB), board)
    print(f"Updated {changed} silk text item(s); saved {PCB.name}.")
    print("Note: regenerate fab images with tools/build_manufacturing.py if needed.")


if __name__ == "__main__":
    main()
