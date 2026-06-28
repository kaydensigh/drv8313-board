# tools/

Headless helper scripts for the DRV8313 board. They run against the KiCad
project under [`../KiCad/project/`](../KiCad/project/) and need only KiCad 10's
bundled Python / `kicad-cli` — no GUI. On Windows:

```powershell
$PY = "C:\Program Files\KiCad\10.0\bin\python.exe"
& $PY tools\<script>.py ...
```

`jlc_search.py` is stdlib-only (any Python 3); the other two need KiCad's
`pcbnew` / `kicad-cli`, so use the bundled interpreter above.

---

## `jlc_search.py` — pick JLCPCB / LCSC parts

Queries the **live** JLCPCB parts API and ranks matches the way this BOM is
sourced: **fee-free first**, then **cheapest unit price**, in stock only.
JLCPCB charges a per-part setup fee only for plain **Extended** parts — **Basic**
and **Preferred** parts incur no extra charge — so those rank first.

```powershell
& $PY tools\jlc_search.py "10kohm 0603 1%"            # ranked table
& $PY tools\jlc_search.py "100nF 0603 X7R" --fee-free  # Basic OR Preferred only
& $PY tools\jlc_search.py "47uF 100V" --fee-free       # confirm no fee-free option exists
& $PY tools\jlc_search.py C92482                       # look up one part by LCSC id
```

Flags: `--fee-free` / `--basic` / `--preferred` apply a **server-side** library
filter — the reliable way to surface no-fee parts, since a plain keyword search
ranks cheap Extended parts first and buries the Basic/Preferred ones. Also
`--package 0603`, `--attr 1%` (substring in the description), `--qty N`
(unit-price tier, default 50), `--min-stock N`, `--pages N`, `--json`.

> The [yaqwsx/jlcparts](https://yaqwsx.github.io/jlcparts) browser mirrors the
> same JLC catalogue into a static database — handy to browse, heavier to
> script against. This script hits the source API live, so stock/price are
> current and no catalogue download is needed.

## `build_manufacturing.py` — regenerate all fabrication outputs

Rebuilds the JLCPCB fab package **and** the README visuals from the project, so
a design change never leaves stale outputs behind.

```powershell
& $PY tools\build_manufacturing.py            # everything
& $PY tools\build_manufacturing.py --fab      # gerbers / drill / zip / CPL / BOM / STEP only
& $PY tools\build_manufacturing.py --images   # 3D renders + SVGs only
```

Produces, under [`../manufacturing/`](../manufacturing/): `gerbers/` (Protel
extensions) + Excellon drill, `drv8313-board-gerbers.zip` (upload-ready),
`drv8313-board-CPL.csv` (pick-and-place), `drv8313-board-BOM.csv` (grouped, with
MPN + LCSC), `drv8313-board.step`; and under [`../images/`](../images/):
`board-3d-{top,bottom}.png` (straight top-down / bottom-up 3D renders),
`schematic.svg`, and `pcb-{top,bottom}.svg` (2D copper + silk plots on a dark
background — KiCad's SVG export is always transparent, so a background rect is
injected for legibility).

It keeps a **defensive snapshot of `project.kicad_pro`** — a no-op on the current
canonical file (kicad-cli leaves it byte-identical; verified), restored with a
warning only if a future KiCad version re-normalises it. It only *generates*; it
does not run DRC/ERC. Override the toolchain with `$env:KICAD_CLI`.

## `set_silk_version.py` — bump the silkscreen version stamp

```powershell
& $PY tools\set_silk_version.py --show        # current: v1.0 / Board v1.0 / 06/26
& $PY tools\set_silk_version.py 2.1           # -> v2.1 (front), Board v2.1 (back)
& $PY tools\set_silk_version.py 2.1 --date auto   # also stamp this month as MM/YY
```

Rewrites the `vN.M` token wherever it appears on a silk layer (preserving a
surrounding label like `Board `) plus the `MM/YY` date stamp. Silk **text only**
— copper/geometry untouched; does not edit README/docs version references.
After bumping, regenerate the board images with `build_manufacturing.py`.

---

## `check_design.py` — verify DRC / connectivity / ERC

Runs the checks the board is validated against and prints a PASS/FAIL summary;
**exits nonzero if any hard check fails** (drop into CI or a pre-commit hook).

```powershell
& $PY tools\check_design.py
```

| Check | Tool | Gate |
| --- | --- | --- |
| DRC (error severity) | `kicad-cli pcb drc --severity-error --refill-zones` | **hard** — must be 0 (authoritative: incl. unconnected, clearance, shorts) |
| Connectivity (all nets) | KiCadRoutingTools `check_connected.py` | advisory cross-check |
| Clearance / shorts | KiCadRoutingTools `check_drc.py` | advisory cross-check |
| ERC | `kicad-cli sch erc` | tripwire — flagged if `!= 53` |

kicad-cli's error-severity DRC is the authoritative connectivity/clearance/short
gate (its ratsnest understands zone fills + through-pad + off-anchor pad entries).
The two KRT checks are **advisory** only — their endpoint-graph model emits false
positives on perfectly-connected manual routing (a track ending inside a pad but
not at its anchor, or tracks meeting *through* a large pad), so they print but
never fail the build. The ERC baseline (53 = 0 err + 53 warn) and the DRC
*warning*-severity items are EasyEDA-import cosmetic artifacts (documented in
CLAUDE.md), so ERC is a **regression tripwire**, not a gate. Keeps a defensive
`project.kicad_pro` snapshot (a no-op today — kicad-cli leaves the canonical file
untouched).
Needs [KiCadRoutingTools](https://github.com/drandyhaas/KiCadRoutingTools) at
`../KiCadRoutingTools` for the connectivity/clearance checks (override with
`$env:KRT_DIR` / `$env:KRT_PYTHON`); if absent, those two are skipped and the
gate falls back to DRC + ERC.

## `check_bom.py` — verify BOM stock + fee status (live)

Looks up every LCSC part in `manufacturing/drv8313-board-BOM.csv` on JLCPCB and
reports stock, Basic/Preferred/Extended (fee status) and price; **flags
out-of-stock / discontinued parts and exits nonzero** if any part is out of
stock — the exact failures that bit this BOM (LED1 went out of stock; the 10 kΩ
Basic part periodically reads 0). Run it before ordering.

```powershell
& $PY tools\check_bom.py                  # fails on any 0-stock part
& $PY tools\check_bom.py --min-stock 100  # also fail on low stock
& $PY tools\check_bom.py --bom other.csv
```

Reuses `jlc_search.py`. Also tallies the unique Extended parts (= one JLCPCB
setup fee each). *(As of this writing it reports the 10 kΩ `C25804` out of stock
— a transient JLC condition on its most-used Basic resistor; re-run before
ordering.)*

## `gen_readme_bom.py` — Markdown BOM table for the README

Emits the README's Bill-of-materials table from the BOM CSV plus **live** JLCPCB
prices: `Designator | Value | Qty | MPN | Unit price | Library`, each MPN linked
to its LCSC page, followed by an estimated per-board component-cost total.

```powershell
& $PY tools\gen_readme_bom.py                  # paste output into README.md
& $PY tools\gen_readme_bom.py --price-qty 10   # quote a different price tier
```

Prices are live, so the table is a dated snapshot — re-run to refresh. Reuses
`jlc_search.py`.
