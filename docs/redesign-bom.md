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
- **C1** `Value` → `10nF 100V`; **C3** `Value` → `47uF 100V` (the chosen 100 V parts).
- **LED1 re-sited to 3.3 V**: the power symbol `#PWR01` on the R5 branch was swapped `VCC` → `3.3V`. Verified by netlist export — `R5.1` is now on net **3.3V** (with C4.2, H1.2, R1–R3, U1.15), and **VCC still carries U1.4 / U1.11** (VM). ERC unchanged at 87 (all pre-existing import artifacts).
- **R5** left at `1kΩ` (suits the 3.3 V rail).

## Remaining work (schematic/PCB rework, GUI)
The EasyEDA import **shares strings across symbols** — `Manufacturer Part` / `Supplier Part` and the resistor `lib_id` are reused by multiple parts — so these must be set **per-symbol in the editor**, not by text edit:
- **Add C5** = second 47 µF / 100 V (`C87862`) in parallel with C3.
- Set new **MPN / Supplier Part** fields: C1 → `C84709`, C3 & C5 → `C87862`, C4 → `C1623`, R5 → a 1 kΩ 0603. (The schematic still shows the old 35 V/50 V part numbers.)
- **P1** → `TB002-500-03BE` 3-pos terminal-block footprint (PCB-side; footprints live only in the PCB).

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
