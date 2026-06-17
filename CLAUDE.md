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

- Created 2026-06-16 by importing the `EasyEDA/*.json` (EasyEDA Standard) files with KiCad 10's importer. The Altium files could **not** be used instead, but the reason is narrower than "KiCad can't read Altium" — verified 2026-06-17 against `kicad-cli` 10.0.3:
  - `kicad-cli pcb import` **does** exist and **does** support Altium (`--format altium`, also eagle/cadstar/pads/pcad/fabmaster/solidworks). But our `Altium/simplefocmini_2024-04-26.pcbdoc` is the **legacy Protel ASCII** record format (file magic `|RECORD=Board|KIND=Protel_Advanced_PCB…`), not the modern binary `.PcbDoc` (OLE2/CFBF) the importer expects: `--format altium` → `Error during import: Wrong file format`; `--format auto` → `No plugin found for file type 'UNKNOWN (18)'`. No importer plugin handles this old ASCII variant.
  - There is **no schematic importer at all** — `kicad-cli sch` only has `erc`/`export`/`upgrade` (no `import`), and the GUI has no Altium-schematic path either. So the `.schdoc` could never be brought in regardless.
  - ⇒ EasyEDA remains the only working import path for *this* project.
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
- Applied so far (schematic): C3 `Value` → `47uF 100V`, C1 `Value` → `10nF 100V`; **per-symbol MPNs set** (C1→`C84709`, C3→`C87862`, C4→`C1623`, R5→`C21190`/1 kΩ) via an anchored Python script (`(reference "Cx")` → back to `\n\t(symbol\n` → paren-match the block → regex-replace fields inside it — safe against the shared-string trap); **C5 added** as a parallel 47 µF/100 V cap with its own VCC/GND power symbols (netlist-verified `C5.1`=VCC, `C5.2`=GND); **LED1 re-sited to 3.3 V** by swapping power symbol `#PWR01` from `VCC` to `3.3V` (netlist-verified). R5 kept at 1 kΩ. ERC 92 (was 87; the +5 are import-category artifacts for the 3 added symbols — `lib_symbol_issues` empty-lib + `pin_to_pin` Unspecified). Remaining = PCB work (add C5 footprint, P1 footprint, EP vias, re-layout), tracked in `docs/redesign-bom.md`.
- Adding a symbol by hand: clone an existing instance block, `fresh_uuids` (symbol + each pin uuid), shift every `(at x y)` by the placement delta, rename the reference (in both the `Reference` property and the `(instances … (reference …))`). Place pins **on the 1.27 mm grid** (cap pin offset is 5.08 mm; pick symbol Y as a multiple of 1.27 or you get `endpoint_off_grid` warnings). Power-symbol pins sit at the symbol origin, so a `VCC`/`GND` symbol whose `(at)` equals a target pin coordinate connects to it.

## PCB redesign progress (pcbnew)

- **U1's EP thermal vias already exist in the footprint** — an 8-pad PTH array (4×2, 0.3 mm drill, 1 mm pitch, centered under the EP at ~(143.5,104.0)) — but the import left them `<no net>` (floating). They are now **netted to GND** (`pad.SetNet(FindNet("GND"))` for U1 pads with `GetDrillSize().x>0`, `PAD_ATTRIB_PTH`, `GetNetCode()==0`). Do **not** add free vias on top of them — that creates `shorting_items` (GND vs `<no net>`).
- **Inner GND planes** on `In1.Cu`/`In2.Cu` were created by duplicating the `B.Cu` GND zone (`src.Duplicate().Cast()`, `SetLayer(In1_Cu/In2_Cu)`, `board.Add`), then `ZONE_FILLER(b).Fill(b.Zones())`. Each fills ~365 mm².
- Current PCB DRC (no parity): **202 violations, 0 unconnected, 0 shorting_items.** Remaining = import artifacts: ~159 silk/text, 18 clearance (the 60 V `Power` net-class 0.3 mm flagged on the old 0.2 mm traces — fixed by widening/re-layout), 14 padstack (U1 footprint), few minor.
- **C5 footprint added** (clone of C3 via `c3.Duplicate(False).Cast()` — note FOOTPRINT.Duplicate needs the `addToParentGroup` bool arg, unlike ZONE.Duplicate()), netted VCC/GND, parked off-board at (152.95,124) pending placement (shows 2 ratsnest). **VM/VCC trace widened** 0.254→0.8 mm (Power-class); no shorts.
- **What does NOT fit the current 26 mm layout (attempted by script, reverted):** widening the *phase* traces to 0.8 mm shorts `U1_8`↔`U1_9` at the 0.65 mm HTSSOP escape; swapping P1 to the 5 mm terminal block (`TerminalBlock_MaiXu_MX126-5.0-03P_1x03_P5.00mm`) shorts/overlaps (9 shorting_items). These plus the Ø10 mm cap resize need component re-placement on a larger board = the interactive re-layout. Footprint swap recipe: `pcbnew.FootprintLoad(libdir, name)`, copy ref/value/pos/orientation, map pad nets by number, `board.Remove(old)`/`board.Add(new)`. Std footprint libs: `C:\Program Files\KiCad\10.0\share\kicad\footprints\*.pretty`.
- **Recommended next step — enlarge the board first, then iterate.** None of the blocked items are fundamentally impossible; they only conflict because they're squeezed into the original 26×21 mm outline. The plan allows ≤50×50 mm, so the approach is: **(1)** redraw the `Edge.Cuts` outline larger (e.g. ~40×40 mm), **(2)** spread the parts out — pull the Ø10 mm caps and the 5 mm terminal block to board edges with room around them, **(3)** then make the changes that previously shorted/overlapped (resize C3/C5 cans, swap P1 → terminal block, place C5, widen+neck the phase traces at the HTSSOP escape), **(4)** re-pour the GND zones to the new outline and re-run DRC. Each step is small and DRC-checkable, so the layout improves incrementally instead of needing one big re-route. Do this in the **GUI** (interactive routing/placement); `pcbnew` scripting can do the outline + bulk moves but hand-routing the fine-pitch escape is faster interactively.
- Board outline bbox 26.34×21.27 mm at x[133.7,160.1] y[91.9,113.1]; copper layer count 4 (F=0, In1=4, In2=6, B=2). Committed PCB DRC: 0 shorting_items, 2 unconnected (C5).
- To re-site a rail connection in this schematic: rail nets are made by **power symbols** (`#PWR` instances whose `lib_id`/`Value` = `VCC`/`3.3V`/`GND`), not net-label text. Change the specific instance's `lib_id` + `Value`, anchored on its unique `(at x y)` coords (the `lib_id "VCC"` / `Value "VCC"` strings recur across all VCC symbols). Verify with `kicad-cli sch export netlist`.

## Validation results (initial import, pre-setup-pass; from kicad-cli runs)

- DRC with `--schematic-parity`: 469 violations, **0 unconnected items**, 65 schematic-parity issues. Top categories: 173 clearance, 78 silk_overlap, 61 solder_mask_bridge, 48 hole_clearance, 30 net_conflict.
- ERC: 87 violations (was 88 before the frame symbol removal). Dominated by import artifacts: pin_to_pin (40), lib_symbol_issues (29), pin_not_driven, plus empty library associations.

## Tooling (Windows)

- `kicad-cli`: `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe` (version 10.0.3). **CLI reference:** https://docs.kicad.org/10.0/en/cli/cli.html (full command list).
- **What `kicad-cli` can/can't do** (verified against the docs, 2026-06-17). Top-level commands: `fp`, `sym`, `sch`, `pcb`, `jobset`, `version`. The CLI is **read-only with respect to design content** — it never edits nets/tracks/parts/placement:
  - **Validate:** `pcb drc`, `sch erc` (text/JSON; `--exit-code-violations` for CI).
  - **Export:** `pcb export {gerbers,drill,pos,pdf,svg,dxf,ps,step,glb,vrml,gencad,ipc2581,ipcd356,odb,stats,…}`, `sch export {netlist,bom,pdf,svg,dxf,ps,python-bom}`, `fp/sym export svg`, `pcb render` (raytraced PNG/JPEG).
  - **Convert formats:** `pcb import` (Altium/Eagle/CADSTAR/PADS/PCAD/Fabmaster/SolidWorks → `.kicad_pcb`; see import caveat above — there is **no `sch import`**); `fp/sym/sch/pcb upgrade` (bump an existing KiCad file to the current format version). `jobset run` batches predefined export jobs.
  - **No content editing.** There is no CLI command to move parts, route, change the board size, edit a netclass, or add a footprint. Those go through the `pcbnew` Python API (PCB) or s-expression text edits (schematic) — the CLI only validates/exports the result.
- The PCB (`.kicad_pcb`) can be edited programmatically via the `pcbnew` Python module. The schematic (`.kicad_sch`) has **no** scripting API and **no** CLI editor — edit it as s-expression text, or use **kicad-skip** (below).
- **`kicad-skip` is installed** (v0.2.5; pure-Python s-expr editor, dep `sexpdata`; **no running KiCad needed**). Installed into the bundled Python's *user* site-packages (Program Files is read-only), so it imports from `& "C:\Program Files\KiCad\10.0\bin\python.exe"` as `import skip`. Use it for **schematic edits** instead of anchored-regex s-expr hacking: it gives a structured per-instance API (`Schematic("…kicad_sch").symbol`, search by reference/value/connection), which sidesteps the shared-MPN-string trap by editing the specific symbol object rather than a global string. It can also read `.kicad_pcb` (partial), but use `pcbnew` for PCB work. Verified 2026-06-17: loads `project.kicad_sch` (32 symbols) and reads properties.
- **KiCad must be closed before editing the project files.** While open it holds `KiCad/project/~project.kicad_pro.lck` and will overwrite external edits on save. Check with `Get-Process kicad` and the `.lck` file.
- **All text is on the default font** (commit `a9c4908`). The EasyEDA import hard-coded font faces — `Arial`/`Times New Roman` in the schematic and an **uninstalled `NotoSerifCJKsc-Medium`** on the PCB; the missing CJK face popped a modal font-substitution dialog that **stalled headless `kicad-cli`/`pcbnew` runs**. All `(face …)` overrides were stripped. Don't re-introduce named faces; if a headless run hangs, suspect a missing-font dialog.
- `pcbnew`/`kicad-cli` first-load is slow on Windows (~30–60 s) and `pcbnew` block-buffers stdout — use `-u`. Backgrounded runs are normal; wait for them.
- **Bash heredocs strip backslashes here** (`<<'PY'` mangled `'\\'` in Python). Write scripts to a file with the Write tool and run them, rather than piping via heredoc.

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
