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
- `docs/` — `redesign-plan.html` (finalized target spec), `redesign-bom.md`, and **`drv8313.pdf` (the TI DRV8313 datasheet — authoritative part reference)**

## Components (from BOM + pick-and-place)

13 placed parts: U1 = DRV8313PWPR (HTSSOP-28); C1, C2 = 100nF (0603); C3 = 100µF (CAP-SMD BD6.3); C4 = 470nF (0603); R1–R4 = 10kΩ (0603); R5 = 1kΩ (0603); LED1 (0603); H1 = 2×5 header; P1 = 3-pin header. (BOM lists 7 line items; H1/P1 appear in the pick-and-place file but not the BOM.)

## DRV8313 pinout (datasheet: `docs/drv8313.pdf`)

Verified 2026-06-17 from the schematic netlist. **Note:** `pdftoppm` is unavailable in this environment, so the Read tool **cannot page-render the datasheet PDF** (`pcb export pdf` outputs read fine; the datasheet does not) — extract text or open `docs/drv8313.pdf` directly.

- **Power row (HTSSOP pins 1–14):** 1 CP1, 2 CP2, 3 VCP (charge pump → C4/C1/C2); **4 & 11 = VM** (net `VCC`); **5/8/9 = OUT1/OUT2/OUT3** phase outputs; 6/7/10/12/13/14 = PGND/COMP/GND; EP (29) = GND thermal pad.
- **Logic row (pins 15–28):** **15 = V3P3OUT** — the chip's *internal* 3.3 V regulator; this **is** the board's "onboard 3.3V LDO" (net `3.3V`). 16/17/18 = nRESET/nSLEEP/nFAULT; 20 = GND; **22/24/26 = EN3/EN2/EN1**; **23/25/27 = IN3/IN2/IN1**; 19 = COMPO# and 21 = NC (both correctly unconnected); 28 = a GND pin (see parity note below).
- **The three EN pins are tied together** to one `EN` net (via R4) = the standard SimpleFOC 3-PWM/FOC config (one master enable; all phases always driven, commutation on IN1/2/3). Independent enables would only matter for trapezoidal/6-step or sensorless BEMF (float one phase) — not this board, so keep them tied.

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
- **Re-layout plan — enlarge first, then iterate.** None of the blocked items are fundamentally impossible; they only conflicted because they were squeezed into the original 26×21 mm outline. The plan allows ≤50×50 mm, so the approach is: **(1)** redraw the `Edge.Cuts` outline larger (~40×40 mm) — **DONE 2026-06-17**; **(2)** spread the parts out — pull the Ø10 mm caps and the 5 mm terminal block to board edges with room around them; **(3)** then make the changes that previously shorted/overlapped (resize C3/C5 cans, swap P1 → terminal block, place C5, widen+neck the phase traces at the HTSSOP escape); **(4)** re-pour the GND zones to the new outline and re-run DRC. Each step is small and DRC-checkable, so the layout improves incrementally instead of needing one big re-route. Do steps 2–4 in the **GUI** (interactive placement/routing) — `pcbnew` scripting did the outline, but moving the *already-routed* parts by script strands their tracks/vias (the fix is to drag them in the GUI so the ratsnest follows), and hand-routing the fine-pitch escape is faster interactively.
- **Board outline enlarged to 40×40 mm (2026-06-17, step 1 of the re-layout).** New `Edge.Cuts` = rectangle x[134,174] y[90,130] with **3 mm rounded corners** (4 straight segments + 4 fillet arcs; bbox 40.1×40.1 incl. 0.1 mm line width); replaced the 12 old rounded-corner segments. Parts/routing untouched — the cluster sits in the upper-left; the new right/bottom area is empty canvas to spread into. Zones were re-poured, **but the zone *boundary* polygons still cover only the original ~26 mm area** (GND boundary ≈ x[131,162] y[91,115]) — the new expansion is bare copper-wise until the boundaries are redrawn to the new outline during placement (step 4). Copper layer count 4 (F=0, In1=4, In2=6, B=2). Note: any corner/edge change leaves the *stored* zone fills stale relative to the new edge (shows as `copper_edge_clearance` "Arc/Segment on BoardOutLine" vs Zone GND) — always re-pour (`ZONE_FILLER`) after editing `Edge.Cuts`.
- **M3 mounting holes + TB_PWR1 footprint added (2026-06-17).** **(a)** 4× `MountingHole_3.2mm_M3` (plain NPTH M3, refs **MH1–MH4**) at the new corners, inset 4 mm → a symmetric 32×32 mm pattern at (138,94)/(170,94)/(170,126)/(138,126). They carry no net; switch to `MountingHole_3.2mm_M3_Pad` + GND in the GUI if chassis-grounding is wanted (the original corner holes were GND). **MH1 (top-left) currently overlaps H1 and the old corner pad** — expected transient (12 DRC violations: hole/courtyard); clears when H1 is moved and the old pad removed during placement. **(b)** **TB_PWR1 was in the schematic but had no PCB footprint** (the import never created it; `redesign-bom.md` wrongly assumed it was already laid out). Added `TerminalBlock_MaiXu_MX126-5.0-02P_1x02_P5.00mm` (the 2-pos sibling of the P1 block), value `TB002-500-02BE`, **pad 1→GND, pad 2→VCC** (per netlist), parked off-board at (148,137) pending placement.
- **The 7 `Pad_gge*` orphan footprints are import free-pads (no schematic symbol).** Identified 2026-06-17: **4× Ø2 mm GND through-holes** at the *old* 26 mm corners ((135.56,93.68)/(158.16,93.81)/(135.56,111.34)/(158.16,111.21)) = the original mounting holes, now mid-board and **superseded by MH1–MH4**; **3× small VCC/GND wire-solder pads** near the right edge ((156.26,102.70)=VCC, (156.26,97.75)=GND, (151.56,93.94)=GND) = the original power-input pads, **superseded by TB_PWR1**. All are candidates for deletion in the GUI during placement (left in place for now — they carry GND/VCC tracks, so deleting by script would strand routing).
- PCB DRC after corners+holes+TB_PWR1 (re-poured): **228 violations, 0 shorting_items, 4 unconnected (C5 ×2 + TB_PWR1 ×2).** Breakdown: ~172 silk/text + 21 clearance (old narrow traces) + 14 padstack + 4 annular (`Pad_gge`) + 5 mask-bridge = pre-existing import artifacts; the remaining 12 (pth/npth/hole/courtyard) are the MH1-vs-H1 transient above.
- To re-site a rail connection in this schematic: rail nets are made by **power symbols** (`#PWR` instances whose `lib_id`/`Value` = `VCC`/`3.3V`/`GND`), not net-label text. Change the specific instance's `lib_id` + `Value`, anchored on its unique `(at x y)` coords (the `lib_id "VCC"` / `Value "VCC"` strings recur across all VCC symbols). Verify with `kicad-cli sch export netlist`.

## Validation results (initial import, pre-setup-pass; from kicad-cli runs)

- DRC with `--schematic-parity`: 469 violations, **0 unconnected items**, 65 schematic-parity issues. Top categories: 173 clearance, 78 silk_overlap, 61 solder_mask_bridge, 48 hole_clearance, 30 net_conflict.
- ERC: 87 violations (was 88 before the frame symbol removal). Dominated by import artifacts: pin_to_pin (40), lib_symbol_issues (29), pin_not_driven, plus empty library associations.

## Tool-driven re-layout + routing (2026-06-17, branch `kicad-import`)

A full clear → re-place → route pass using **KiCadRoutingTools** (see Tooling). The fine-pitch HTSSOP escape is the one hard spot — exactly as predicted from the start.

- **Cleared** (commit `79c6220`): removed all 112 tracks + 42 vias, the 7 `Pad_gge` import orphans (old corner mounting holes + old power-input pads, superseded by MH1–4 / TB_PWR1), all stale zones, and the `Dwgs.User` import graphics. Kept all real parts + MH1–4 + the 40×40 Edge.Cuts.
- **Macro placement** (commit `d9c2c45`, hand-placed via `pcbnew`; `place_optimize` polish in `eb4ef99`): power-in TB_PWR1 **left edge**, motor-out P1 **right edge** (opposite edges, per user), control header H1 **top** (faces U1 logic row), U1 central, bulk VM cans in the open bottom area, CP/bypass caps under the power row, logic pulls between H1 and U1, LED by the 3.3 V pin. Polish: airwire 195→180 mm, crossings 39→19. **place_optimize keeps connectors/U1/holes locked but can slide unlocked caps into mounting-hole courtyards — re-check + nudge after.**
- **Routing** (commit `f3557cf`): `route.py` on F.Cu/B.Cu only (inner layers are GND planes), **0.6 mm** power nets (VCC + the 3 phases) with neck-down. **All signals + all 3 phase outputs routed.** Key trick: **route VCC first** so it claims its escape corridor before the phases. `route_planes` → solid GND planes on In1/In2 (24/24 GND pads stitched, 0.96 mΩ / 13 A). **DRC: 0 shorts, 0 clearance.**
- **Both VM pins (4 & 11) hand-routed** (commit `d96fe0e`) with B.Cu via-jogs threaded clear of the phase escapes — pin 4 drops *above* U1_3's y114.3 kink (U1_3 = VCP→C2.2 hugs pin 4's only exit). VCC fully connected; **0 shorts, 0 clearance.** Silk also bumped 8-35V→8-60V / v1.1→v2.0. The autoroute alone was **zero-sum** at that row (6 non-GND escapes — VM×2, OUT×3, VCP — competing; VCC-first connects the VM pins but starves a phase), which is why the VM pins needed the hand-route. Used 0.6 mm power width (≈2 A in 1 oz, fine for 1.5 A) since the netclass's 0.8 mm can't escape the 0.65 mm pitch even with neck-down. **Only remaining DRC item: 1 EN ratsnest near-miss** (`check_connected` reports EN fully connected; KiCad flags a hairline gap from the aggressive autoroute) — trivial GUI snap.
- **Schematic↔PCB parity** (full connectivity diff, all 66 pads): only **two** real mismatches. (1) **R5.1 was stale on `VCC`** but the schematic has the LED on `3.3V` (V3P3OUT, pin 15) — the LED-resiting edit was never synced to the PCB; **fixed** R5.1→3.3V in `f3557cf`. The PCB nets are import-era, so do a GUI "Update PCB from Schematic" if more schematic edits land. (2) **U1 pin 28 (a GND pin)**: PCB tied it to GND but the schematic floated it — **fixed** (commit `7895b14`): added a `#PWR018` GND symbol on pin 28's endpoint (netlist-verified U1.28=GND; ERC delta is only the same import pin-type artifact every U1 GND pin shows).

## Tooling (Windows)

- `kicad-cli`: `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe` (version 10.0.3). **CLI reference:** https://docs.kicad.org/10.0/en/cli/cli.html (full command list).
- **What `kicad-cli` can/can't do** (verified against the docs, 2026-06-17). Top-level commands: `fp`, `sym`, `sch`, `pcb`, `jobset`, `version`. The CLI is **read-only with respect to design content** — it never edits nets/tracks/parts/placement:
  - **Validate:** `pcb drc`, `sch erc` (text/JSON; `--exit-code-violations` for CI).
  - **Export:** `pcb export {gerbers,drill,pos,pdf,svg,dxf,ps,step,glb,vrml,gencad,ipc2581,ipcd356,odb,stats,…}`, `sch export {netlist,bom,pdf,svg,dxf,ps,python-bom}`, `fp/sym export svg`, `pcb render` (raytraced PNG/JPEG).
  - **Convert formats:** `pcb import` (Altium/Eagle/CADSTAR/PADS/PCAD/Fabmaster/SolidWorks → `.kicad_pcb`; see import caveat above — there is **no `sch import`**); `fp/sym/sch/pcb upgrade` (bump an existing KiCad file to the current format version). `jobset run` batches predefined export jobs.
  - **No content editing.** There is no CLI command to move parts, route, change the board size, edit a netclass, or add a footprint. Those go through the `pcbnew` Python API (PCB) or s-expression text edits (schematic) — the CLI only validates/exports the result.
- The PCB (`.kicad_pcb`) can be edited programmatically via the `pcbnew` Python module. The schematic (`.kicad_sch`) has **no** scripting API and **no** CLI editor — edit it as s-expression text, or use **kicad-skip** (below).
- **`kicad-skip` is installed** (v0.2.5; pure-Python s-expr editor, dep `sexpdata`; **no running KiCad needed**). Installed into the bundled Python's *user* site-packages (Program Files is read-only), so it imports from `& "C:\Program Files\KiCad\10.0\bin\python.exe"` as `import skip`. Use it for **schematic edits** instead of anchored-regex s-expr hacking: it gives a structured per-instance API (`Schematic("…kicad_sch").symbol`, search by reference/value/connection), which sidesteps the shared-MPN-string trap by editing the specific symbol object rather than a global string. It can also read `.kicad_pcb` (partial), but use `pcbnew` for PCB work. Verified 2026-06-17: loads `project.kicad_sch` (32 symbols) and reads properties.
- **KiCadRoutingTools** (Rust-accelerated A* autorouter, https://github.com/drandyhaas/KiCadRoutingTools) is cloned at **`../KiCadRoutingTools`** (sibling of this repo; v0.15.12). **Not** pip-installable. Setup (2026-06-17): isolated venv at **`../KiCadRoutingTools/.venv`** (Python 3.11 + `numpy`/`scipy`/`shapely`) plus the prebuilt Windows Rust binary (`build_router.py` → `rust_router/grid_router.pyd`). Run as `& "..\KiCadRoutingTools\.venv\Scripts\python.exe" -X utf8 <tool>.py <board> [out] ...`. It uses its **own** `.kicad_pcb` parser (no `pcbnew`) and round-trips our 4-layer board intact (GND1/GND2 inner-layer names preserved — verified). Tools: `place_optimize.py` (routability *polish* of an existing placement — **not** a from-scratch placer; the authors found hand placement beats auto ~500×, so place by hand first), `route.py` (signals + power nets with neck-down), `route_planes.py` (plane zones + GND via stitching; pass the net once per `--plane-layers` entry, e.g. `--nets GND GND --plane-layers In1.Cu In2.Cu`), `check_connected.py`/`check_drc.py`. `place_route_loop.py` crashes on our board (`unhashable type: 'dict'`).
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
