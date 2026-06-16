# CLAUDE.md

Guidance for agents working in this repository. Only verified facts are recorded here.

## What this is

SimpleFOCMini — a DRV8313-based 3-phase BLDC motor driver board, compatible with the SimpleFOC library. This is a hardware/PCB repository (no firmware, no build system). Original source on EasyEDA: https://easyeda.com/the.skuric/simplefocmini

v1.1 board specification (from README): 8–24V supply, 2.5A per phase max, onboard 3.3V LDO, 26×21 mm.

## Current goal

Redesign the board for the DRV8313's full voltage range. Finalized target (see `docs/redesign-plan.html`): **8–60V, 1.5A continuous per phase, ≤50×50 mm, 4-layer (Top/GND/GND/Bottom, 1 oz)**. The v1.1 design is 8–24V. Note: the datasheet's "2.5A per phase" is a *peak* figure (no continuous rating is published). The continuous rating is set by the DRV8313 junction temperature (RθJA), not the copper; ~1.5A is the realistic 1oz/small-board limit at Tj≤125°C, with thermal headroom designed toward ~2A.

The KiCad project under `KiCad/project/` is the working design. When cleaning up the imported project, only address what blocks redesign progress — import artifacts (clearance/silk/parity/ERC pin-types) will be redone during re-layout.

## Repository layout

- `Altium/` — Altium `.schdoc` + `.pcbdoc` (dated 2024-04-26)
- `EasyEDA/` — EasyEDA Standard schematic + PCB JSON (editor v6.5)
- `Gerber/` — fabrication Gerbers + Excellon drill files
- `KiCad/project/` — KiCad 10 project (`.kicad_pro/.kicad_sch/.kicad_pcb`); the editable working design
- `3D model/` — board `.obj` + `.mtl`
- `BOM_simplefocmini_2024-04-26.csv`, `Pick and Place/`, `Schematic_simplefocmini.pdf`

## Components (from BOM + pick-and-place)

13 placed parts: U1 = DRV8313PWPR (HTSSOP-28); C1, C2 = 100nF (0603); C3 = 100µF (CAP-SMD BD6.3); C4 = 470nF (0603); R1–R4 = 10kΩ (0603); R5 = 1kΩ (0603); LED1 (0603); H1 = 2×5 header; P1 = 3-pin header. (BOM lists 7 line items; H1/P1 appear in the pick-and-place file but not the BOM.)

## KiCad project facts

- Created 2026-06-16 by importing the `EasyEDA/*.json` (EasyEDA Standard) files with KiCad 10's importer. KiCad 10 does **not** import the Altium `.pcbdoc`/`.schdoc` format ("format not supported").
- Import brought across: all 13 components (schematic + PCB), board outline on `Edge.Cuts`, 112 track segments, 70 vias, nets, 77 schematic wires.
- The board has **5 board-level copper zones**: GND + VCC on `F.Cu` and `B.Cu` (the ground/power pours). `pcbnew` `Board.Zones()` returns 5.
- The ~120 other `(zone)` blocks in `project.kicad_pcb` are **footprint-internal** cosmetic shapes (component/lead outlines on `User.3`/`User.4`, plus paste/silk), not loose board objects.
- KiCad 10 writes zone/track/via nets as `(net "NAME")` (name inline), not the older `(net N) (net_name "...")` form.
- The imported EasyEDA drawing frame came in as an unresolved 291×204 mm placeholder symbol (`lib_id "Unknown_0_-806"`, ref `A1`); it has been removed from the schematic.

## Project setup for redesign (done 2026-06-16)

A project-setup pass configured the project for the 60 V target. **Board files only — no copper has been re-routed yet.**

- **Stackup is now 4 copper layers** (`Board.SetCopperLayerCount(4)` via `pcbnew`). Layer table: `F.Cu` (id 0, "TopLayer"), `In1.Cu` (id 4, named **GND1**), `In2.Cu` (id 6, named **GND2**), `B.Cu` (id 2, "BottomLayer"); thickness still 1.6 mm. Inner layers are renamed to encode the Top/GND/GND/Bottom intent — pour GND zones on them during layout. KiCad copper-layer IDs in v10: F.Cu=0, B.Cu=2, inner copper = even numbers (In1=4, In2=6, …). No explicit `(stackup)` block is written; KiCad applies a default 4-layer stack (set physical dielectric thicknesses in Board Setup → Physical Stackup if a specific stack is needed).
- **A `Power` net class** was added in `project.kicad_pro`: `track_width` 0.8 mm, `clearance` 0.3 mm (for 60 V), `via_diameter`/`via_drill` 0.8/0.4 mm. Assigned via `netclass_patterns` to nets **VCC** (the VM rail) and **U1_5 / U1_8 / U1_9** (the three phase outputs). `Default` is left at 0.2 mm clearance / 0.2 mm track so fine-pitch HTSSOP escape stays routable; KiCad uses the larger of two classes' clearances for a pair, so VM↔GND already resolves to 0.3 mm. **If the phase/VM nets are renamed during re-layout, update these patterns.**
- Editing the PCB via `pcbnew` (`LoadBoard`/`SaveBoard`) **rewrites the entire `.kicad_pcb` in canonical format** — expect a large diff even for a small logical change. Content round-trips intact (verified after the layer change: 4 copper layers, 5 board zones with correct nets, thickness 1.6 mm, loads clean).
- Run `pcbnew` scripts via **PowerShell** with the call operator and `-u` (unbuffered): `& "C:\Program Files\KiCad\10.0\bin\python.exe" -u script.py`. The Bash tool failed to exec the space-containing exe path (exit 127) and block-buffers stdout, so prints never appeared.

### Schematic / BOM facts (for the redesign)

- The schematic stores each part's voltage rating **only implicitly, via the chosen `Manufacturer Part` / `Supplier Part` (LCSC) fields** — there is no separate voltage field, and `Footprint` fields are all empty (footprints live only in the PCB). So a "raise to 100 V" change means **re-selecting the part**, not editing a field.
- Component **MPN strings are shared across symbols** in the import (e.g. C1 and C2 both carry `CL10B104KB8NNNC`; `VT1V101M-CRE77`/`CL10B104KB8NNNC` appear 5×/10× across lib-cache + instances). **Do not blank/replace MPNs by global string match** — it corrupts sibling parts. Edit per-symbol in the schematic editor.
- Each part appears twice in `project.kicad_sch`: once in the `(lib_symbols)` cache (deeper indent) and once as a placed `(symbol)` instance. The **placed instance** property is authoritative for the netlist/BOM.
- Applied so far (schematic): C3 `Value` → `47uF 100V`, C1 `Value` → `10nF 100V`; **LED1 re-sited to 3.3 V** by swapping power symbol `#PWR01` (the R5-branch supply) from `VCC` to `3.3V` — verified by netlist (`R5.1` now on net `3.3V`; `VCC` still has `U1.4/U1.11`). R5 kept at 1 kΩ. ERC unchanged at 87 (all pre-existing import artifacts). Remaining part changes (add C5, set MPNs, P1 footprint) are tracked in `docs/redesign-bom.md`.
- To re-site a rail connection in this schematic: rail nets are made by **power symbols** (`#PWR` instances whose `lib_id`/`Value` = `VCC`/`3.3V`/`GND`), not net-label text. Change the specific instance's `lib_id` + `Value`, anchored on its unique `(at x y)` coords (the `lib_id "VCC"` / `Value "VCC"` strings recur across all VCC symbols). Verify with `kicad-cli sch export netlist`.

## Validation results (initial import, pre-setup-pass; from kicad-cli runs)

- DRC with `--schematic-parity`: 469 violations, **0 unconnected items**, 65 schematic-parity issues. Top categories: 173 clearance, 78 silk_overlap, 61 solder_mask_bridge, 48 hole_clearance, 30 net_conflict.
- ERC: 87 violations (was 88 before the frame symbol removal). Dominated by import artifacts: pin_to_pin (40), lib_symbol_issues (29), pin_not_driven, plus empty library associations.

## Tooling (Windows)

- `kicad-cli`: `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe` (version 10.0.3).
- Bundled Python with working `pcbnew` API: `C:\Program Files\KiCad\10.0\bin\python.exe`.
- The PCB (`.kicad_pcb`) can be edited programmatically via the `pcbnew` Python module. The schematic (`.kicad_sch`) has **no** scripting API — edit it as s-expression text.
- **KiCad must be closed before editing the project files.** While open it holds `KiCad/project/~project.kicad_pro.lck` and will overwrite external edits on save. Check with `Get-Process kicad` and the `.lck` file.

### Useful commands

```sh
KCLI="C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
PY="C:/Program Files/KiCad/10.0/bin/python.exe"

# Design rule check (with schematic parity)
"$KCLI" pcb drc --schematic-parity --format report --output drc.txt KiCad/project/project.kicad_pcb
# Electrical rule check
"$KCLI" sch erc --format report --output erc.txt KiCad/project/project.kicad_sch
# Plot a copper layer to PDF (visual inspection; PDFs are readable)
"$KCLI" pcb export pdf --layers "F.Cu,Edge.Cuts" --mode-single --output top.pdf KiCad/project/project.kicad_pcb
# Run a pcbnew script
"$PY" my_pcb_script.py
```

## Git

- Import + cleanup work is on branch `kicad-import` (off `main`).
- `KiCad/project/.gitignore` excludes `*.kicad_prl`, `*.lck`, `.history/`, and backups — do not commit those.
