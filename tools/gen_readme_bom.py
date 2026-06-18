#!/usr/bin/env python3
"""Generate the README Bill-of-materials table from the BOM + live JLCPCB prices.

Reads manufacturing/drv8313-board-BOM.csv, looks up every LCSC part on JLCPCB
(via jlc_search) for its current unit price and library type (Basic / Preferred
/ Extended = fee status), and prints a Markdown table:

    | Designator | Value | Qty | MPN | Unit price | Library |

with each MPN linked to its LCSC product page, followed by two cost estimates:
a per-board figure at volume, and a realistic small-batch total (default 10
boards) that applies JLCPCB's per-part assembly minimum (`leastPatchNumber`) and
attrition (`lossNumber`), prices each part at its purchased-quantity tier, and
adds the one-time Extended-part setup fee. Paste the output into README.md.

    & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tools/gen_readme_bom.py
    python tools/gen_readme_bom.py --batch 10 --extended-fee 3 > table.md

Prices are live, so the table is a dated snapshot; re-run to refresh. The
Extended-part fee is not returned by the API (JLCPCB's setup/feeder fee, ~$3 at
writing) -- override with --extended-fee. Reuses tools/jlc_search.py. Network
required.
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
                    help="unit-price tier for the table column (default 100)")
    ap.add_argument("--batch", type=int, default=10,
                    help="board count for the realistic small-batch estimate (default 10)")
    ap.add_argument("--extended-fee", type=float, default=3.0,
                    help="JLCPCB one-time fee per unique Extended part (default $3)")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.bom, encoding="utf-8-sig")))
    out, bulk_total, n_ext = [], 0.0, 0
    batch_comp, ext_codes = 0.0, set()
    for r in rows:
        code = r["LCSC"].strip()
        qty = int(r["Qty"])
        rec = lookup(code) or {}
        lib = jlc.classify(rec) if rec else "?"
        prices = rec.get("componentPrices")
        unit = jlc.price_at(prices, args.price_qty) if rec else None
        mpn = r["MPN"].replace("*", r"\*")  # don't let * start markdown emphasis
        out.append((r["Designator"], r["Value"], qty, mpn, lcsc_url(rec, code),
                    f"${unit:.4f}" if unit is not None else "?", lib))
        bulk_total += (unit or 0) * qty
        n_ext += lib == "Extended"
        # Realistic batch: JLCPCB charges max(used + attrition, assembly minimum),
        # priced at that quantity's tier; Extended parts add a one-time setup fee.
        used = qty * args.batch
        buy = max(used + (rec.get("lossNumber") or 0), rec.get("leastPatchNumber") or 0)
        batch_comp += buy * (jlc.price_at(prices, buy) or 0)
        if lib == "Extended":
            ext_codes.add(code)

    print("| Designator | Value | Qty | MPN | Unit price | Library |")
    print("| --- | --- | --- | --- | --- | --- |")
    for desig, val, qty, mpn, url, price, lib in out:
        print(f"| {desig} | {val} | {qty} | [{mpn}]({url}) | {price} | {lib} |")

    ext_fees = len(ext_codes) * args.extended_fee
    batch_total = batch_comp + ext_fees
    today = datetime.date.today().isoformat()
    print(f"\n**Component cost ≈ ${bulk_total:.2f}/board in volume** "
          f"(unit prices at JLCPCB's {args.price_qty}-piece tier, {today}; U1 dominates). "
          f"{n_ext} parts are **Extended** (one-time setup fee each); the rest are fee-free.")
    print(f"\n**A small batch of {args.batch} boards ≈ ${batch_total:.2f} in parts "
          f"(~${batch_total / args.batch:.2f}/board)**: ${batch_comp:.2f} of components "
          f"(JLCPCB per-part assembly minimums + attrition applied) plus "
          f"{len(ext_codes)} × ${args.extended_fee:.0f} Extended-part setup fees "
          f"(${ext_fees:.0f}). The fixed fees amortise over larger runs. "
          f"Excludes PCB fabrication, assembly labour and shipping.")


if __name__ == "__main__":
    main()
