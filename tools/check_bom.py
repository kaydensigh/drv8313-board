#!/usr/bin/env python3
"""Check the BOM against live JLCPCB stock and library (fee) status.

Reads manufacturing/drv8313-board-BOM.csv and looks up every LCSC part number
on JLCPCB, reporting stock, Basic/Preferred/Extended (= fee status) and unit
price. Flags parts that are out of stock or discontinued -- the exact failure
modes that bit this BOM (LED1 went out of stock; the 10 k Basic part read 0).

Exit code is nonzero if any part is out of stock (or below --min-stock), so it
works as a pre-order gate. Reuses tools/jlc_search.py for the API calls.

    & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tools/check_bom.py
    python tools/check_bom.py --min-stock 100        # also fail on low stock
    python tools/check_bom.py --bom path/to/other-BOM.csv
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jlc_search as jlc

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BOM = ROOT / "manufacturing" / "drv8313-board-BOM.csv"


def lookup(code):
    """Return the JLCPCB record for an exact LCSC code, or None."""
    d = jlc.fetch_page(code, 1, 10)
    rows = ((d.get("data") or {}).get("componentPageInfo") or {}).get("list") or []
    return next((r for r in rows if r.get("componentCode") == code),
                rows[0] if rows else None)


def find_col(fieldnames, *candidates):
    low = {f.lower(): f for f in fieldnames}
    for c in candidates:
        if c in low:
            return low[c]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bom", default=str(DEFAULT_BOM), help="BOM CSV path")
    ap.add_argument("--qty", type=int, default=50, help="qty for the unit-price tier")
    ap.add_argument("--min-stock", type=int, default=1,
                    help="fail parts with less than this stock (default 1 = only flag 0)")
    args = ap.parse_args()

    with open(args.bom, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        cols = reader.fieldnames or []
    c_lcsc = find_col(cols, "lcsc", "supplier part")
    c_ref = find_col(cols, "designator", "reference", "refs")
    c_val = find_col(cols, "value", "val")
    if not c_lcsc:
        sys.exit(f"No LCSC column found in {args.bom} (have: {cols})")

    print(f"BOM: {args.bom}\n")
    hdr = f"{'Designator':18} {'Value':12} {'LCSC':10} {'lib':9} {'stock':>9} {'unit$':>8}  flags"
    print(hdr)
    print("-" * len(hdr))

    out_of_stock, extended_codes, missing = [], set(), []
    for row in rows:
        code = (row.get(c_lcsc) or "").strip()
        ref = (row.get(c_ref) or "").strip() if c_ref else ""
        val = (row.get(c_val) or "").strip() if c_val else ""
        val = val[:12]
        if not code:
            print(f"{ref:18} {val:12} {'(none)':10} -- no LCSC part number")
            missing.append(ref)
            continue
        try:
            rec = lookup(code)
        except Exception as e:
            print(f"{ref:18} {val:12} {code:10} lookup error: {e}")
            missing.append(ref)
            continue
        if not rec:
            print(f"{ref:18} {val:12} {code:10} NOT FOUND on JLCPCB")
            missing.append(ref)
            continue
        lib = jlc.classify(rec)
        stock = rec.get("stockCount") or 0
        price = jlc.price_at(rec.get("componentPrices"), args.qty)
        ps = f"{price:.4f}" if price is not None else "?"
        flags = []
        if stock < args.min_stock:
            flags.append("OUT OF STOCK" if stock == 0 else f"LOW (<{args.min_stock})")
            out_of_stock.append((ref, code, stock))
        if jlc.is_eol(rec):
            flags.append("DISCONTINUED")
        if lib == "Extended":
            extended_codes.add(code)
        flagstr = ("  ** " + ", ".join(flags)) if flags else ""
        print(f"{ref:18} {val:12} {code:10} {lib:9} {stock:>9} {ps:>8}{flagstr}")

    print("-" * len(hdr))
    n = len(rows)
    fee_free = n - len(extended_codes) - len(missing)
    print(f"{n} BOM lines | {len(extended_codes)} unique Extended part(s) "
          f"(= {len(extended_codes)} JLCPCB setup fee(s)); the rest are fee-free")
    if out_of_stock:
        print("OUT OF STOCK / LOW: " + ", ".join(f"{r}={s}" for r, c, s in out_of_stock))
    if missing:
        print("Could not verify: " + ", ".join(missing))
    ok = not out_of_stock
    print("\n" + ("PASS -- all parts in stock" if ok
                  else "FAIL -- some parts out of stock (re-source before ordering)"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
