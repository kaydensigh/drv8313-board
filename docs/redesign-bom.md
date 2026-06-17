# SimpleFOCMini 60 V redesign — BOM / part-selection worklist

Actionable parts list for the 8–60 V / 1.5 A redesign. Rationale and thermal/voltage
analysis are in [`redesign-plan.html`](./redesign-plan.html); this file tracks **which part each
reference needs** and its decision status.

**Status legend:** ✅ keep · ✔ decided/applied · 🛠️ rework (schematic/PCB) work remaining

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
| **P1** | 1 | Motor phase output | 3-pin 2.54 mm header (`Header-Female-2.54_1x3`) | **3-position 5 mm terminal block → `TB002-500-03BE`** (3-pos sibling of TB_PWR1's `TB002-500-02BE`). | 🛠️ (PCB footprint) |
| **TB_PWR1** | 1 | VM / GND power input | `TB002-500-02BE` (2-pos, 5 mm terminal block) | None — already a 5 mm block; 5 mm blocks are typically ≥300 V / ≥10 A. | ✅ |

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
- DRC now: **0 shorting_items, 2 unconnected** (just C5's two pads). The rest are pre-existing import artifacts (silk/text ~160, clearance 21, padstack 14).

## Remaining work (PCB, needs the re-layout)
These need component re-placement on a larger board (they overlap or short on the current 26 mm layout), so they belong to the interactive re-layout.

**Recommended approach — enlarge the board first, then improve the layout incrementally.** The items below aren't impossible; they only fail because they're packed into the original 26×21 mm outline. The plan allows ≤50×50 mm, so:
1. **Enlarge the `Edge.Cuts` outline** (e.g. ~40×40 mm) to create room.
2. **Spread the parts out** — move the Ø10 mm caps and the 5 mm terminal block toward the board edges with clearance around them.
3. **Then apply each blocked change** (resize cans, swap P1, place + route C5, neck/widen the phase traces). Each is a small, DRC-checkable step, so the layout gets better one increment at a time instead of in a single big re-route.
4. **Re-pour the GND zones** to the new outline and re-run DRC.

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
- `U1`, `TB_PWR1`, `H1`, and `R1–R4` carry over unchanged.
