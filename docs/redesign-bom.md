# SimpleFOCMini 60 V redesign — BOM / part-selection worklist

Actionable parts list for the 8–60 V / 1.5 A redesign. Rationale and thermal/voltage
analysis are in [`redesign-plan.html`](./redesign-plan.html); this file tracks **which part each
reference needs** and its decision status.

**Status legend:** ✅ keep · 🔁 reselect (spec given) · ⚠️ decision needed · 🛠️ PCB/layout work

| Ref | Qty | Function | v1.1 part (current) | Redesign requirement | Status |
| --- | --- | --- | --- | --- | --- |
| **U1** | 1 | DRV8313PWPR motor driver | DRV8313PWPR (HTSSOP-28) | None — already 8–60 V rated | ✅ |
| **C3** | 1 | VM bulk | 100 µF **35 V** SMD Al-elec (`VT1V101M-CRE77`, BD6.3) | **100 µF ≥80 V** (target 100 V) SMD Al-elec. Larger can (~10×10 mm); reserve board area. Verify ripple-current rating at 1.5 A. | 🔁 |
| **C1** | 1 | Charge-pump flying cap (CP1–CP2) | 100 nF **50 V** X7R 0603 (`CL10B104KB8NNNC`) | **100 V X7R**, 0603/0805. **Value: 10 nF (TI datasheet) vs 100 nF (current board) — decide.** | ⚠️🔁 |
| **C2** | 1 | VCP→VM charge-pump reservoir | 100 nF 50 V X7R 0603 (`CL10B104KB8NNNC`) | None — only sees VCP−VM (~11 V); 50 V is fine (TI spec 16 V). After C1 is reselected these two no longer share a part. | ✅ |
| **C4** | 1 | V3P3OUT decouple | 470 nF **10 V Y5V** 0603 | **Optional** upgrade to 470 nF **16–25 V X7R** 0603 (voltage already OK on 3.3 V; Y5V is just unstable). | 🔁 (optional) |
| **R1–R4** | 4 | Logic pull-ups / dividers | 10 kΩ 0603 | None | ✅ |
| **R5** | 1 | Indicator-LED series resistor | 1 kΩ 0603 (BOM value) — **but listed MPN decodes to 4.7 kΩ** | Resolve true value against the physical board, then size for the **3.3 V** rail (LED re-sited): ~470 Ω–1 kΩ 0603. | ⚠️ |
| **LED1** | 1 | Power indicator | 0603 LED, currently across **VM** via R5 | **Re-site to the 3.3 V (V3P3OUT) rail.** At 60 V the VM-fed 0603 R5 would dissipate 0.7–3.4 W. LED part itself unchanged. | 🛠️ (schematic topology) |
| **H1** | 1 | Control header (IN1–3, EN, GND, 3V3…) | 2×5 2.54 mm female header | None | ✅ |
| **P1** | 1 | Motor phase output | 3-pin 2.54 mm header (`Header-Female-2.54_1x3`) | **3-position 5 mm terminal block → `TB002-500-03BE`** (3-pos sibling of TB_PWR1's `TB002-500-02BE`; same family/footprint pitch). | 🔁🛠️ |
| **TB_PWR1** | 1 | VM / GND power input | `TB002-500-02BE` (2-pos, 5 mm terminal block) | None — already a 5 mm terminal block; confirm its current/voltage rating covers 60 V / phase current (5 mm blocks are typically ≥300 V / ≥10 A). | ✅ |

## Already applied to the schematic
- **C3** `Value` → `100uF 100V`, **C1** `Value` → `100nF 100V` (records the required rating on the symbol).
- The schematic's `Manufacturer Part` / `Supplier Part` fields still reference the **old 35 V/50 V parts** for C1/C3 — they were left untouched because those MPN strings are shared across multiple symbols in the EasyEDA import (editing by string would corrupt C2). **Update the MPN fields when the new parts are chosen** (do it in the schematic editor, per-symbol).

## Sourcing shortlist (researched 2026-06-16 against live LCSC/JLCPCB — re-verify stock at order time)

All 100 V parts below are JLCPCB **Extended** (there is no 100 V X7R MLCC or HV SMD electrolytic in the Basic tier), so expect the one-time extended-part load fee.

**C1 — charge-pump flying cap (100 V X7R 0603):**

| Value | MPN | LCSC | Note |
| --- | --- | --- | --- |
| **10 nF** (TI rec, lead choice) | Samsung **CL10B103KC8NNNC** | **C84709** | ~298k stock; exactly the datasheet value |
| 100 nF (fallback) | Samsung **CL10B104KC8NNNC** | **C15725** | the original 50 V part with the voltage code bumped (B8→C8) |

**C3 — VM bulk electrolytic (Ø10 mm SMD can; a true 100 µF @ 100 V is NOT stocked — pick one):**

| Option | MPN | LCSC | Spec | Ripple | Note |
| --- | --- | --- | --- | --- | --- |
| **A (default)** | Ymin **VKME1001K101MV** | **C487410** | 100 µF / **80 V**, 10×10 mm | **744 mA**@100 kHz | best ripple + full bulk value; 60 V on 80 V = 75 % derating (acceptable); 10000 h@105 °C |
| B | Honor **RVT2A470M1010** | **C87862** | 47 µF / **100 V**, 10×10.2 mm | unpublished | true 100 V, full margin, half the bulk; cheap (~$0.09) |
| C | A ∥ B in parallel | — | 147 µF total | — | same Ø10 footprint family; 100 µF/80 V for bulk + 47 µF/100 V for margin |

Footprint for all C3 options: `Capacitor_SMD:CP_Elec_10x10` (or `CP_Elec_10x10.5`) — larger than the old Ø6.3 BD6.3 can, OK given the freed area.

**C4 — 3.3 V decouple (optional, move off Y5V):** Samsung **CL10B474KA8NNNC** (470 nF 25 V X7R 0603), LCSC **C1623** *(verify Basic tier)*; backup Fenghua **C172758** (Extended).

## Open decisions (blocking specific part orders)
1. **C1 value** — 10 nF (TI's recommended CP flying cap, and what I've sourced as the lead) or 100 nF (what the board shipped)? Both work and both are stocked at 100 V.
2. **C3 bulk-cap rating** — no 100 µF @ 100 V exists in stock. Choose **A** (100 µF/80 V, best ripple, 75 % derating), **B** (47 µF/100 V, full margin), or **C** (both in parallel). Default: **A**.
3. **R5 value** — BOM says 1 kΩ, the manufacturer part number decodes to 4.7 kΩ. Confirm from the physical board before reusing; then size for the 3.3 V rail.
4. **LED1 re-site** — confirm moving the indicator from VM to the 3.3 V rail (recommended).

## Notes
- Original parts were sourced from **LCSC** (see `Supplier Part` C-numbers in the schematic / the 2024 BOM CSV). For the new caps, pick **JLCPCB/LCSC in-stock** equivalents at the target voltage so assembly stays cheap — specific stock numbers should be taken from JLCPCB's catalogue at order time rather than hard-coded here.
- `U1`, `TB_PWR1`, `H1`, and `R1–R4` carry over unchanged.
