#!/usr/bin/env python3
"""Generate the README Bill-of-materials table from the BOM + live JLCPCB prices.

Reads manufacturing/drv8313-board-BOM.csv, looks up every LCSC part on JLCPCB
(via jlc_search) for its current unit price and library type (Basic / Preferred
/ Extended = fee status), and prints a Markdown table:

    | Designator | Value | Qty | MPN | Unit price | Library |

with each MPN linked to its LCSC product page, followed by an estimated
component-cost total for one board. Paste the output into README.md.

    & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tools/gen_readme_bom.py
    python tools/gen_readme_bom.py --price-qty 100 > table.md

Prices are live, so the table is a dated snapshot; re-run to refresh. Reuses
tools/jlc_search.py for the API. Network required.
"""
import argparse
import csv
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jlc_search as jlc

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BOM = ROOT / "manufacturing" / "drv8313-board-BOM.csv"


def lookup(code):
    d = jlc.fetch_page(code, 1, 10)
    rows = ((d.get("data") or {}).get("componentPageInfo") or {}).get("list") or []
    return next((r for r in rows if r.get("componentCode") == code),
                rows[0] if rows else None)


def lcsc_url(rec, code):
    u = (rec or {}).get("lcscGoodsUrl") or ""
    return u if u.startswith("http") else f"https://www.lcsc.com/product-detail/{code}.html"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bom", default=str(DEFAULT_BOM))
    ap.add_argument("--price-qty", type=int, default=100,
                    help="unit-price tier to quote (default 100)")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.bom, encoding="utf-8-sig")))
    out, total, n_ext = [], 0.0, 0
    for r in rows:
        code = r["LCSC"].strip()
        qty = int(r["Qty"])
        rec = lookup(code)
        lib = jlc.classify(rec) if rec else "?"
        unit = jlc.price_at(rec.get("componentPrices"), args.price_qty) if rec else None
        mpn = r["MPN"].replace("*", r"\*")  # don't let * start markdown emphasis
        out.append((r["Designator"], r["Value"], qty, mpn, lcsc_url(rec, code),
                    f"${unit:.4f}" if unit is not None else "?", lib))
        total += (unit or 0) * qty
        n_ext += lib == "Extended"

    print("| Designator | Value | Qty | MPN | Unit price | Library |")
    print("| --- | --- | --- | --- | --- | --- |")
    for desig, val, qty, mpn, url, price, lib in out:
        print(f"| {desig} | {val} | {qty} | [{mpn}]({url}) | {price} | {lib} |")
    today = datetime.date.today().isoformat()
    print(f"\n**Estimated component cost ≈ ${total:.2f} per board** "
          f"(unit prices at JLCPCB's {args.price_qty}-piece tier, {today}). "
          f"{n_ext} **Extended** parts each incur a one-time JLCPCB setup fee; "
          f"the rest are fee-free. Excludes PCB fabrication and assembly.")


if __name__ == "__main__":
    main()
