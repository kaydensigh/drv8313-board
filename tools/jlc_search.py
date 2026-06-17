#!/usr/bin/env python3
"""Find JLCPCB / LCSC parts ranked for this board's BOM policy.

JLCPCB charges a per-part feeder/setup fee only for *plain Extended* parts;
**Basic** and **Preferred** parts incur no extra charge. So the selection rule is:

    1. prefer fee-free parts  (Basic OR Preferred)
    2. among those, pick the cheapest unit price
    3. require live stock

This queries the live JLCPCB component API (the same data the assembly
parts-picker uses), so stock/price/library-type are current. No catalogue
download needed (cf. https://yaqwsx.github.io/jlcparts which mirrors the same
JLC data into a static DB -- handy for browsing, heavier to script against).

Examples
--------
    python tools/jlc_search.py "10kohm 0603 1%"
    python tools/jlc_search.py "43kohm 0603 1%" --qty 50
    python tools/jlc_search.py "C92482"                 # search by LCSC id / MPN
    python tools/jlc_search.py "62kohm 0603 1%" --json   # machine-readable

Only the Python standard library is used, so any Python 3 runs it.
"""
import argparse
import json
import sys
import urllib.request

API = ("https://jlcpcb.com/api/overseas-pcb-order/v1/"
       "shoppingCart/smtGood/selectSmtComponentList")

# Substrings that flag a part we should not auto-recommend.
_EOL_MARKERS = ("停产", "discontinu", "end of life", " eol")  # 停产


def fetch_page(keyword, page, page_size, extra=None):
    payload = {"keyword": keyword, "currentPage": page, "pageSize": page_size}
    if extra:
        payload.update(extra)
    body = json.dumps(payload).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (drv8313-board jlc_search)",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def price_at(prices, qty):
    """Unit price for the tier covering `qty` (endNumber -1 == infinity)."""
    if not prices:
        return None
    best = None
    for t in prices:
        lo = t.get("startNumber", 0)
        hi = t.get("endNumber", -1)
        if hi == -1:
            hi = float("inf")
        if lo <= qty <= hi:
            return t.get("productPrice")
        # remember the lowest-tier price as a fallback (qty below first tier)
        p = t.get("productPrice")
        if p is not None and (best is None or lo < best[0]):
            best = (lo, p)
    return best[1] if best else None


def classify(rec):
    if rec.get("componentLibraryType") == "base":
        return "Basic"
    if rec.get("preferredComponentFlag"):
        return "Preferred"
    return "Extended"


def is_eol(rec):
    blob = " ".join(str(rec.get(k, "")) for k in
                    ("erpComponentName", "describe", "noBuyReason")).lower()
    return any(m in blob for m in _EOL_MARKERS)


# API-side library filters (probed: the parts-picker accepts these in the body).
_LIB_FILTERS = {
    "basic":     [{"componentLibraryType": "base"}],
    "preferred": [{"preferredComponentFlag": 1}],
    # fee-free = Basic OR Preferred -> two server-side passes, merged.
    "fee-free":  [{"componentLibraryType": "base"}, {"preferredComponentFlag": 1}],
}


def gather(keyword, qty, pages, page_size, min_stock, package,
           attr, include_eol, lib_filter=None):
    out = []
    seen = set()
    extras = _LIB_FILTERS.get(lib_filter, [None])
    for extra in extras:
        _gather_pass(keyword, qty, pages, page_size, min_stock, package,
                     attr, include_eol, extra, out, seen)
    return out


def _gather_pass(keyword, qty, pages, page_size, min_stock, package,
                 attr, include_eol, extra, out, seen):
    for page in range(1, pages + 1):
        d = fetch_page(keyword, page, page_size, extra)
        info = (d.get("data") or {}).get("componentPageInfo") or {}
        rows = info.get("list") or []
        if not rows:
            break
        for rec in rows:
            code = rec.get("componentCode")
            if not code or code in seen:
                continue
            seen.add(code)
            stock = rec.get("stockCount") or 0
            if stock < min_stock:
                continue
            desc = rec.get("describe") or ""
            spec = rec.get("componentSpecificationEn") or ""
            if package and package.lower() not in (spec + " " + desc).lower():
                continue
            if attr and attr.lower() not in desc.lower():
                continue
            eol = is_eol(rec)
            if eol and not include_eol:
                continue
            lib = classify(rec)
            out.append({
                "lcsc": code,
                "mpn": rec.get("componentModelEn") or "",
                "brand": rec.get("componentBrandEn") or "",
                "lib": lib,
                "fee_free": lib in ("Basic", "Preferred"),
                "stock": stock,
                "unit_price": price_at(rec.get("componentPrices"), qty),
                "package": spec,
                "type": rec.get("componentTypeEn") or "",
                "desc": desc,
                "eol": eol,
                "url": rec.get("lcscGoodsUrl") or "",
            })
        total = info.get("total") or 0
        if page * page_size >= total:
            break
    return out


def rank_key(r):
    # fee-free first, then cheapest, then most stock
    price = r["unit_price"] if r["unit_price"] is not None else float("inf")
    return (0 if r["fee_free"] else 1, price, -r["stock"])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("keyword", help="value/MPN/LCSC id, e.g. '10kohm 0603 1%' or C92482")
    ap.add_argument("--qty", type=int, default=50, help="quantity for the unit-price tier (default 50)")
    ap.add_argument("--min-stock", type=int, default=1, help="drop parts below this stock (default 1)")
    ap.add_argument("--package", default=None, help="require this package substring, e.g. 0603")
    ap.add_argument("--attr", default=None, help="require this substring in the description, e.g. 1%")
    ap.add_argument("--pages", type=int, default=3, help="API pages to scan (default 3)")
    ap.add_argument("--page-size", type=int, default=100, help="results per page (default 100)")
    ap.add_argument("--max-results", type=int, default=12, help="rows to print (default 12)")
    ap.add_argument("--include-eol", action="store_true", help="include discontinued parts")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--fee-free", dest="lib", action="store_const", const="fee-free",
                   help="only Basic OR Preferred parts (no per-part fee) -- server-side filter")
    g.add_argument("--basic", dest="lib", action="store_const", const="basic",
                   help="only Basic parts (server-side filter)")
    g.add_argument("--preferred", dest="lib", action="store_const", const="preferred",
                   help="only Preferred parts (server-side filter)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = ap.parse_args()

    rows = gather(args.keyword, args.qty, args.pages, args.page_size,
                  args.min_stock, args.package, args.attr, args.include_eol,
                  lib_filter=args.lib)
    rows.sort(key=rank_key)
    rows = rows[:args.max_results]

    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return

    if not rows:
        print(f"No matches for {args.keyword!r} (try --include-eol or relax --min-stock).")
        return

    print(f"Top {len(rows)} for {args.keyword!r}  (unit price @ qty {args.qty}; "
          f"* = recommended: cheapest fee-free in-stock)\n")
    hdr = f"{'':1} {'LCSC':10} {'lib':9} {'unit$':>8} {'stock':>8}  {'MPN / description'}"
    print(hdr)
    print("-" * len(hdr))
    recommended_done = False
    for r in rows:
        mark = " "
        if not recommended_done and r["fee_free"] and r["unit_price"] is not None:
            mark, recommended_done = "*", True
        price = f"{r['unit_price']:.4f}" if r["unit_price"] is not None else "?"
        eol = "  [EOL]" if r["eol"] else ""
        print(f"{mark} {r['lcsc']:10} {r['lib']:9} {price:>8} {r['stock']:>8}  "
              f"{r['mpn']} - {r['brand']}{eol}")
        print(f"  {'':40}{r['desc'][:90]}")
    print("\nFee policy: Basic & Preferred = no per-part fee; plain Extended = setup fee.")


if __name__ == "__main__":
    main()
