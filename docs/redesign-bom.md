# SimpleFOCMini 60 V redesign — BOM / part-selection worklist

Actionable parts list for the 8–60 V / 1.5 A redesign. Rationale and thermal/voltage
analysis are in [`redesign-plan.html`](./redesign-plan.html); this file tracks **which part each
reference needs** and its decision status.

**Status legend:** ✅ keep · ✔ decided/applied · 🛠️ rework (schematic/PCB) work remaining

> ## ⚑ Current status (2026-06-18) — read this first
>
> The brushed/solenoid + comparator redesign is **implemented and committed** (branch `kicad-import`); the
> sections further down were written *during* the design and describe earlier intermediate states — **trust
> this banner and CLAUDE.md over them.**
>
> - **Schematic: done** (commit `d0eca99`) — comparator current-sense network, P1 → 5-pos, H1 → 2×7 with
>   independent EN1/EN2/EN3. Netlist-verified (92 nodes).
> - **PCB: routed and electrically clean** (commits `4f38a5c`…`455a958`) — all 92 connections, 0 unconnected,
>   **0 error-severity DRC (0 shorts / 0 clearance / 0 courtyard)**. Board **enlarged to 40×45 mm** (the 5-pos
>   block didn't fit 40×40 between the corner M3 holes). Both inner layers are GND planes; EP + GND pads
>   stitched. The 3 divider shorts, the U1 HTSSOP fine-pitch clearances, and the C3/R4 overlap were all
>   cleared 2026-06-18. **Remaining: cosmetic only** — ~248 silk/text/HTSSOP-padstack import warnings, and
>   schematic footprint fields still empty (29 footprint-parity items). See CLAUDE.md "Divider + fine-pitch +
>   C3/R4 cleanup" for detail.
> - **Actual reference designators** (this doc's placeholders → as-built): R_SENSE = **R8** (50 mΩ 2512);
>   reference divider R_top/R_x/R_bot = **R9 (43 k) / R10 (62 k) / R11 (1 k)**; C_ref = **C6** (0.47 µF on
>   COMPN/VREF); R_pull = **R12** (10 k on nCOMPO); **SJ1/SJ2** as named.
> - **Divider verified:** with R8 = 50 mΩ — SJ1+SJ2 intact → 0.125 V → **2.5 A**; cut SJ1 → 0.075 V → **1.5 A**;
>   cut SJ2 → VREF floats → **disabled**. Topology follows datasheet **Fig. 12** (COMPP=pin12=sense,
>   COMPN=pin13=reference) — the §8.2.2.2.1 prose contradicts its own Fig. 12; don't swap COMPP/COMPN.
> - **BOM: COMPLETE (2026-06-18).** Every line now carries an MPN + LCSC id (JLCPCB Basic-preferred). The 10
>   new parts were sourced; **R1–R4 were corrected** (the import left them on the 4.7 k part `C23162` despite a
>   10 kΩ value → now `C25804`); **P1 was corrected** (its LCSC `C146243` was actually a 3-pin *header*, a v1.1
>   leftover → now the 5-pos block `DB126V-5.0-5P-GN-P`/`C2835160`). See the as-built table in `../README.md`
>   and CLAUDE.md "BOM finalization + 3D enrichment". The Ø10 mm can resize for C3/C5 is also **done** (board
>   now uses the BD10.0 cans, matching part `C87862`).

| Ref | Qty | Function | v1.1 part (current) | Redesign part | Status |
| --- | --- | --- | --- | --- | --- |
| **U1** | 1 | DRV8313PWPR motor driver | DRV8313PWPR (HTSSOP-28) | None — already 8–60 V rated | ✅ |
| **C3 + C5** | 2 | VM bulk | 100 µF 35 V SMD Al-elec (`VT1V101M-CRE77`, BD6.3) | **2× 47 µF / 100 V** in parallel (Honor `C87862`) ≈ 94 µF at full 100 V margin; two Ø10 mm cans. C3 `Value` updated; **C5 to be added** in rework. | ✔ / 🛠️ |
| **C1** | 1 | Charge-pump flying cap (CP1–CP2) | 100 nF 50 V X7R 0603 (`CL10B104KB8NNNC`) | **10 nF / 100 V X7R 0603** (Samsung `C84709`) — TI datasheet value. `Value` updated. | ✔ |
| **C2** | 1 | VCP→VM charge-pump reservoir | 100 nF 50 V X7R 0603 (`CL10B104KB8NNNC`) | None — only sees VCP−VM (~11 V); 50 V is fine (TI spec 16 V). | ✅ |
| **C4** | 1 | V3P3OUT decouple | 470 nF 10 V Y5V 0603 | Optional: **470 nF 25 V X7R 0603** (Samsung `C1623`) — moves off unstable Y5V. | 🛠️ (optional) |
| **R1–R4** | 4 | Logic pull-ups / dividers | 10 kΩ 0603 | None | ✅ |
| **R5** | 1 | Indicator-LED series resistor | 1 kΩ 0603 (Value) / MPN decodes to 4.7 kΩ | **Keep 1 kΩ** — on the 3.3 V rail that's ~1.3 mA (fine for an indicator). | ✔ |
| **LED1** | 1 | Power indicator | 0603 LED, was across **VM** via R5 | **Re-sited to the 3.3 V rail** (done — see below). LED part unchanged. | ✔ |
| **H1** | 1 | Control header (IN1–3, EN, GND, 3V3…) | 2×5 2.54 mm female header | None | ✅ |
| **P1** | 1 | Motor / load output | 3-pin 2.54 mm header (`Header-Female-2.54_1x3`) | **5-position 5 mm terminal block `[GND M1 M2 M3 VM]` → `TB002-500-05BE`** (`TerminalBlock_MaiXu_MX126-5.0-05P`) — see the brushed/solenoid section. *(Superseded the earlier 3-pos plan.)* Swapped on the PCB. | ✔ |
| **TB_PWR1** | 1 | VM / GND power input | `TB002-500-02BE` (2-pos, 5 mm terminal block) | Part unchanged (5 mm blocks are ≥300 V / ≥10 A). **But the import never created a PCB footprint for it** — added 2026-06-17 as `TerminalBlock_MaiXu_MX126-5.0-02P_1x02_P5.00mm` (pad 1→GND, pad 2→VCC), parked off-board pending placement. | ✔ / 🛠️ (place) |

## Decisions (resolved)
1. **C1 → 10 nF / 100 V** (TI datasheet value; Samsung `C84709`).
2. **C3 → 2× 47 µF / 100 V in parallel** (Honor `C87862`) ≈ 94 µF at full 100 V margin. Same part number twice ⇒ a **single** JLCPCB extended-part fee, and ripple current is shared across two cans. (A true 100 µF @ 100 V is not stocked at JLCPCB/LCSC.)
3. **R5 → 1 kΩ** on the 3.3 V rail (~1.3 mA indicator current). No physical board available, so standardized on the schematic's 1 kΩ value.
4. **LED1 → re-sited to 3.3 V** (done, verified).

## Already applied to the schematic
- **Values:** C1 → `10nF 100V`, C3 → `47uF 100V`.
- **MPNs set per-symbol** (anchored edits, not global replace — the import shares part-number strings, so each was scoped to its own symbol instance): C1 → Samsung `CL10B103KC8NNNC` / `C84709`; C3 → Honor `RVT2A470M1010` / `C87862`; C4 → Samsung `CL10B474KA8NNNC` / `C1623`; R5 → UniOhm `0603WAF1001T5E` / `C21190` (the 1 kΩ of the same series; was the 4.7 kΩ part).
- **C5 added** — second 47 µF/100 V (`C87862`) in parallel with C3, placed at (96.52, 158.75) with its own VCC/GND power symbols. Netlist-verified: `C5.1` on **VCC**, `C5.2` on **GND**.
- **LED1 re-sited to 3.3 V**: power symbol `#PWR01` on the R5 branch swapped `VCC` → `3.3V`. Netlist-verified: `R5.1` now on net **3.3V**; **VCC still carries U1.4 / U1.11** (VM).
- **R5** kept at `1kΩ` (suits the 3.3 V rail).
- ERC is 92 (was 87): the +5 are the same import-artifact categories (`lib_symbol_issues` empty-library, `pin_to_pin` Unspecified) inherent to adding symbols to this not-yet-cleaned import; they clear when the symbol libraries/pin-types are fixed.

## Applied to the PCB
- **EP thermal vias tied to GND.** U1's footprint already had an 8-pad PTH thermal-via array (4×2, 0.3 mm, under the exposed pad) but it was assigned `<no net>` (floating). All 8 are now netted to **GND** — the EP now conducts to the ground planes. (This is why the earlier audit read "zero vias": they existed but were unconnected.)
- **Inner GND planes** added on `In1.Cu` (GND1) and `In2.Cu` (GND2), each filling ~365 mm² (near-full-board), plus the existing top/bottom GND pours. With the EP vias this gives the 4-layer thermal spreading the redesign needs.
- **VM trace widened** 0.254 → **0.8 mm** (Power-class). No shorts; adds ~3 clearance flags on the cramped layout that the re-route clears.
- **C5 footprint added** (clone of C3, netted VCC/GND), parked below the board outline at (152.95, 124) pending placement — it shows as 2 ratsnest/"unconnected" until routed.
- **Phase traces left at 0.5 mm.** Widening them to 0.8 mm *shorts* `U1_8`↔`U1_9` at the 0.65 mm-pitch HTSSOP escape — they must neck down at the IC and widen away from it, which is a routing task. 0.5 mm already carries 1.5 A.
- **Outline enlarged to 40×40 mm with 3 mm rounded corners** (2026-06-17, step 1). Parts/routing untouched (cluster in the upper-left; right/bottom is empty canvas).
- **4× M3 mounting holes (3.2 mm NPTH, MH1–MH4)** at the new corners, symmetric 32×32 mm pattern (inset 4 mm). No net assigned — switch to the `_Pad` + GND variant in the GUI if chassis grounding is wanted (the original corner holes were GND). MH1 (top-left) overlaps H1 / the old corner pad until H1 is moved.
- **TB_PWR1 footprint added** — it was in the schematic but the import never laid it out. Now `TerminalBlock_MaiXu_MX126-5.0-02P` (pad 1→GND, pad 2→VCC), parked off-board pending placement (2 ratsnest).
- **Orphan `Pad_gge*` pads identified (7).** 4× Ø2 mm GND through-holes at the old corners = the original mounting holes (now mid-board, **superseded by MH1–MH4**); 3× small VCC/GND wire-solder pads near the right edge = the original power-input pads (**superseded by TB_PWR1**). Candidates to delete in the GUI (they hold GND/VCC tracks, so script-deleting would strand routing).
- DRC now: **0 shorting_items, 4 unconnected** (C5 ×2 + TB_PWR1 ×2). Of 228 total, ~216 are pre-existing import artifacts (silk/text ~172, clearance 21, padstack 14, annular 4, mask-bridge 5) and 12 are the MH1-vs-H1 transient (clears on placement).

## Remaining work (PCB, needs the re-layout)
> **⚠ Superseded (historical).** This section predates the 40×45 re-layout + routing. Most of it is now **done**: the board was enlarged, parts spread, P1 swapped to the 5-pos terminal block, all 92 nets routed, and the board is electrically clean (0 error-severity DRC). Trust the top banner + CLAUDE.md. The only genuinely-open items are the **order-time** ones (LCSC numbers/stock; optional Ø10 mm can resize for C3/C5 — the board kept the BD6.3 cans) and the **cosmetic** silk/text pass.

These need component re-placement on a larger board (they overlap or short on the current 26 mm layout), so they belong to the interactive re-layout.

**Recommended approach — enlarge the board first, then improve the layout incrementally.** The items below aren't impossible; they only fail because they're packed into the original 26×21 mm outline. The plan allows ≤50×50 mm, so:
1. ✅ **Enlarge the `Edge.Cuts` outline** — **DONE 2026-06-17.** Outline is now a clean ~40×40 mm rectangle (x[134,174] y[90,130]); parts/routing untouched (cluster in the upper-left, empty canvas to the right/bottom). DRC after: 207 violations, 0 shorting_items, 2 unconnected (C5) — all 207 pre-existing import artifacts.
2. **Spread the parts out** — move the Ø10 mm caps and the 5 mm terminal block toward the board edges with clearance around them. *Do this in the GUI:* dragging a footprint in pcbnew leaves its tracks/vias behind (strands them), so interactive placement (ratsnest follows the part) is the right tool.
3. **Then apply each blocked change** (resize cans, swap P1, place + route C5, neck/widen the phase traces). Each is a small, DRC-checkable step, so the layout gets better one increment at a time instead of in a single big re-route.
4. **Re-pour the GND zones** to the new outline and re-run DRC. The fills were re-poured after the outline change, but the zone *boundary* polygons still cover only the original ~26 mm area — redraw them to the new outline here so the planes fill the full board.

The individual blocked items:
- **Route C5** to VCC/GND once it's placed.
- **Neck/widen the phase traces** at the U1 escape during routing.
- **Resize C3 + C5** from the BD6.3 (6.3 mm) can to the Ø10 mm can (`CP_Elec_10x10`) for the C87862 part.
- **P1 → terminal block.** Use KiCad footprint `TerminalBlock_MaiXu_MX126-5.0-03P_1x03_P5.00mm` (a 5 mm 3-pos block, the TB002-500-03BE class; pads 1/2/3 = the U1_9/U1_8/U1_5 phases). *Confirmed: swapping it in place shorts/overlaps badly (9 shorting_items + courtyard overlaps) because the 5 mm block is much larger than the 2.54 mm header — place it at a board edge during re-layout, then re-route the 3 phases.*
- `C1623` (C4) LCSC number and JLCPCB stock/tier for every line: verify at order time.

> **Why these are re-layout tasks:** each was attempted by script and reverted — the 60 V redesign's bigger parts (Ø10 mm caps, 5 mm terminal block) and wider traces don't fit the original 26 × 21 mm layout without shorting/overlapping. They need component re-placement on a larger board (the plan allows ≤50 × 50 mm), which is interactive routing work. **The fix is to enlarge the outline first and then iterate** (see "Recommended approach" above) — once the parts have room, these changes stop conflicting and can be made and DRC-checked one at a time. The thermal vias, inner GND planes, C5, and VM-trace widening *did* fit and are applied.

## Sourcing reference (researched 2026-06-16 vs live LCSC/JLCPCB — re-verify stock at order time)

| Ref | Part | LCSC | Spec | JLCPCB tier | ~Unit price |
| --- | --- | --- | --- | --- | --- |
| C1 | Samsung CL10B103KC8NNNC | **C84709** | 10 nF 100 V X7R 0603 | Extended | ~$0.01 |
| C3, C5 | Honor RVT2A470M1010 | **C87862** | 47 µF 100 V, Ø10×10.2 mm | Extended | ~$0.09 |
| C4 | Samsung CL10B474KA8NNNC | **C1623** *(verify Basic)* | 470 nF 25 V X7R 0603 | Basic? | ~$0.003 |

- Footprint for C3/C5: `Capacitor_SMD:CP_Elec_10x10` (or `CP_Elec_10x10.5`).
- 100 nF 100 V fallback for C1 (if not going with 10 nF): Samsung `CL10B104KC8NNNC` (`C15725`).
- **Cost note:** the caps are pennies; at low volume the real cost is JLCPCB's **~$3 one-time extended-part fee per unique part number** — here C1 and C3 (one fee even with 2× C87862) ⇒ ~$6 added; C4 is likely Basic (free).
- `U1`, `TB_PWR1`, and `R1–R3` carry over unchanged. **(H1, P1, and R4 change — see the next section.)**

## Brushed-DC / solenoid support + comparator current limit (designed + implemented 2026-06-17 — see status banner for as-built refs)

Extends the board beyond 3-phase BLDC to also drive **brushed-DC motors and solenoids**, and adds a
**user-configurable hardware current limit** built on the DRV8313's uncommitted comparator. All of this is
explicitly supported by the datasheet: §8.2.3 "Brushed-DC and Solenoid Load" (Fig. 16), §8.2.4 "Three
Solenoid Loads" (Fig. 17, Tables 8–12), and §7.3.1 (separate PGND pins for a low-side sense resistor).

### H1 → 2×7 header (break out all three EN pins + expose the comparator)

Today EN1/EN2/EN3 (U1 26/24/22) are **ganged** onto one `EN` net through a single series R4, brought out on
one header pin. New design breaks them into three independent nets, **each with its own series 10 k** (keep
R4 for EN1, **add R6 → EN2, R7 → EN3**), and exposes the comparator. Single GND (down from two). Pinout:

```
 1 GND     2 3V3        9 nRES   10 nSLP
 3 IN1     4 EN1       11 nFLT   12 nCOMPO
 5 IN2     6 EN2       13 COMPP  14 COMPN
 7 IN3     8 EN3
```

Connector part: female 2×7 2.54 mm (replaces the 2×5 `C30419`); footprint `…2x07…`. User ties the EN pins
together at the header to restore ganged enable, or drives them independently.

### Comparator current-limit network (TI Fig. 12 topology)

- **Sense:** tie **PGND1/2/3 together → one shunt R_SENSE (50 mΩ) → GND** (§7.3.1 explicitly blesses a single
  combined low-side shunt). **Constraint:** PGND voltage must stay **≤ ±500 mV**, so R_SENSE ≤ 100 mΩ even at
  the chip's ~5 A internal OCP; 50 mΩ → ≤250 mV at 5 A, ~0.3 W at 2.5 A (use a 1 W 2512). COMPP taps the shunt.
- **Reference (COMPN):** divider off 3V3 with two cut-jumpers for selectable threshold —
  **default 2.5 A; cut SJ1 → 1.5 A; cut SJ2 → no limit** (COMPN pulls to 3V3, never trips). Starting values
  R_top 43 k, R_x 62 k (in series with SJ1, parallel to R_top), R_bot 1 k (in series with SJ2 to GND), plus a
  0.47 µF filter cap on COMPN. COMPN is also on the header, so firmware can set an arbitrary threshold.
- **Output:** nCOMPO is open-drain → **10 k pull-up to 3V3** → header pin 12 (MCU reads; low = over-current).
  Optional jumper to route nCOMPO → nRESET for autonomous hardware shutdown.
- **Bonus:** COMPP on the header is a free **analog current monitor** (I = V_COMPP / R_SENSE) for the MCU ADC.
- **Caveat:** the comparator is an **instantaneous peak** trip, not an RMS/thermal limit. 2.5 A default sits
  above the ~2.1 A peak of 1.5 A-RMS sinusoidal BLDC (no nuisance trips) and below the chip's fixed ~5 A OCP;
  a BLDC user raises it, a DC-load user can drop it to 1.5 A.

### P1 → 5-position output terminal block `[GND M1 M2 M3 VM]`

Both supply references at the output so the user picks per the datasheet load tables:
- **Sensed load → wire to VM** (low-side load, Table 12; energize INx **low**): current returns through the
  low-side FET → shunt → **sensed** by the current limit.
- **Simple/safe load → wire to GND** (high-side load, Tables 9/11; energize INx **high**): **not** sensed.
- **Brushed motor on M1+M2** (H-bridge) is sensed either way (its current always crosses one low-side FET).
- M1/M2/M3 = OUT1/OUT2/OUT3. 5-pos 5 mm block (`TB002-500-05BE` class). Exposes VM (≤60 V) at the terminal —
  same rail already on TB_PWR1.

### New / changed parts summary

| Ref | Change |
| --- | --- |
| **H1** | 2×5 → **2×7** female header |
| **P1** | 3-pin header → **5-pos 5 mm terminal block** `[GND M1 M2 M3 VM]` |
| **R4** | repurposed: series R on **EN1** only (was the single ganged-EN series R) |
| **R6, R7** | **new** 10 k series resistors for EN2, EN3 |
| **R_SENSE** | **new** 50 mΩ ≥1 W shunt (PGND1/2/3 → GND) |
| **R_top / R_x / R_bot** | **new** reference divider (43 k / 62 k / 1 k) |
| **C_ref** | **new** 0.47 µF on COMPN |
| **R_pull** | **new** 10 k pull-up on nCOMPO |
| **SJ1, SJ2** | **new** solder jumpers (threshold select / disable) |

PGND1/2/3 are no longer tied directly to GND — they go through R_SENSE, which re-works the low-side ground
near U1 (the EP/thermal-pad area). EP (29) stays on GND.
