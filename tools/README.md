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
`board-3d-{top,bottom}.png`, `schematic.svg`, `pcb-{top,bottom}.svg`.

It snapshots and **restores `project.kicad_pro`** (kicad-cli rewrites it on
load — and `pcb drc` resets the custom min-via rules). It only *generates*;
it does not run DRC/ERC. Override the toolchain with `$env:KICAD_CLI`.

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
