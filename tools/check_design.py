#!/usr/bin/env python3
"""Verify the board design: DRC, connectivity, clearance, and ERC.

Runs the checks this project is validated against and prints a PASS / FAIL
summary. Exit code is nonzero if any *hard* check fails, so it drops straight
into CI or a pre-commit hook.

  DRC    kicad-cli pcb drc --severity-error --refill-zones   hard: must be 0
  conn   KiCadRoutingTools check_connected.py                hard: all nets connected
  clear  KiCadRoutingTools check_drc.py                      hard: 0 clearance/short violations
  ERC    kicad-cli sch erc                                   tripwire: flagged if != baseline

The ERC baseline (101 = 10 error + 91 warning) is entirely EasyEDA-import
artifacts (pin types, lib-symbol issues) documented in CLAUDE.md -- a regression
*tripwire*, not a hard gate. DRC *warning*-severity items (silk/padstack/text)
are likewise cosmetic import artifacts and not gated; only error-severity DRC is.

project.kicad_pro is snapshotted as a defensive tripwire -- on the current
(canonical) file kicad-cli leaves it byte-identical (verified), so this never
fires; if a future KiCad version re-normalises it, it's restored with a warning.
KiCadRoutingTools is expected at ../KiCadRoutingTools; override with
$KRT_DIR / $KRT_PYTHON. If it's missing, conn+clear are skipped (with a notice)
and the gate falls back to DRC+ERC.

    & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tools/check_design.py
    python tools/check_design.py --erc-baseline 101
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJ = ROOT / "KiCad" / "project"
PCB = PROJ / "project.kicad_pcb"
SCH = PROJ / "project.kicad_sch"
PRO = PROJ / "project.kicad_pro"
ERC_BASELINE = 101


def locate_cli():
    env = os.environ.get("KICAD_CLI")
    if env:
        return env
    for c in (r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe",
              "/usr/bin/kicad-cli", "kicad-cli"):
        if Path(c).exists() or shutil.which(c):
            return c
    return "kicad-cli"


def locate_krt():
    """(scripts_dir, python_exe) for KiCadRoutingTools, or (None, None)."""
    d = Path(os.environ.get("KRT_DIR", ROOT.parent / "KiCadRoutingTools"))
    py = os.environ.get("KRT_PYTHON")
    if py:
        py = Path(py)
    else:
        for cand in (d / ".venv" / "Scripts" / "python.exe",
                     d / ".venv" / "bin" / "python"):
            if cand.exists():
                py = cand
                break
    if py and Path(py).exists() and (d / "check_connected.py").exists():
        return d, Path(py)
    return None, None


CLI = locate_cli()
KRT_DIR, KRT_PY = locate_krt()


def run(args):
    return subprocess.run([str(a) for a in args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def check_drc(results):
    out = Path(tempfile.gettempdir()) / "_chk_drc.rpt"
    r = run([CLI, "pcb", "drc", "--severity-error", "--refill-zones",
             "--format", "report", "--output", out, PCB])
    txt = out.read_text(encoding="utf-8", errors="replace") if out.exists() else r.stdout
    out.unlink(missing_ok=True)
    n = sum(int(m) for m in re.findall(r"Found (\d+) (?:DRC violations|unconnected pads|Footprint errors)", txt))
    results.append(("DRC (error severity)", n == 0, f"{n} error-severity violation(s)", True))


def check_erc(results, baseline):
    out = Path(tempfile.gettempdir()) / "_chk_erc.rpt"
    r = run([CLI, "sch", "erc", "--format", "report", "--output", out, SCH])
    txt = out.read_text(encoding="utf-8", errors="replace") if out.exists() else r.stdout
    out.unlink(missing_ok=True)
    m = re.search(r"ERC messages:\s*(\d+)\s+Errors\s+(\d+)\s+Warnings\s+(\d+)", txt)
    if not m:
        results.append(("ERC", False, "could not parse ERC report", False))
        return
    total, err, warn = (int(x) for x in m.groups())
    ok = total == baseline
    note = f"{total} messages ({err} err / {warn} warn); baseline {baseline}"
    if not ok:
        note += "  <-- DIVERGED from baseline (possible regression)"
    results.append(("ERC (import-artifact tripwire)", ok, note, False))


def run_krt(script, label, results):
    if not KRT_PY:
        results.append((label, None, "SKIPPED -- KiCadRoutingTools not found "
                        "(set $KRT_DIR)", True))
        return
    r = run([KRT_PY, "-X", "utf8", KRT_DIR / script, PCB])
    last = [l for l in (r.stdout or "").splitlines() if l.strip()
            and "=" * 5 not in l]
    summary = last[-1] if last else "(no output)"
    results.append((label, r.returncode == 0, summary, True))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--erc-baseline", type=int, default=ERC_BASELINE,
                    help=f"expected ERC message count (default {ERC_BASELINE})")
    ap.add_argument("--no-restore-pro", action="store_true",
                    help="don't restore project.kicad_pro afterwards")
    args = ap.parse_args()

    print(f"kicad-cli:          {CLI}")
    print(f"KiCadRoutingTools:  {KRT_DIR if KRT_DIR else '(not found -- conn/clear skipped)'}\n")

    results = []  # (label, ok|None, note, is_hard_gate)
    pro_snapshot = PRO.read_bytes() if PRO.exists() else None
    try:
        check_drc(results)
        run_krt("check_connected.py", "Connectivity (all nets)", results)
        run_krt("check_drc.py", "Clearance / shorts", results)
        check_erc(results, args.erc_baseline)
    finally:
        if pro_snapshot is not None and not args.no_restore_pro:
            if PRO.read_bytes() != pro_snapshot:
                PRO.write_bytes(pro_snapshot)
                print("! WARNING: kicad-cli modified project.kicad_pro -- restored it "
                      "(unexpected; a KiCad-version change may have re-normalised it).")

    print(f"{'CHECK':34} {'RESULT':8} DETAIL")
    print("-" * 78)
    hard_fail = False
    for label, ok, note, hard in results:
        tag = "SKIP" if ok is None else ("PASS" if ok else "FAIL")
        print(f"{label:34} {tag:8} {note}")
        if hard and ok is False:
            hard_fail = True
    print("-" * 78)
    print("FAIL" if hard_fail else "PASS",
          "-- " + ("a hard check failed" if hard_fail else "all hard checks passed"))
    sys.exit(1 if hard_fail else 0)


if __name__ == "__main__":
    main()
