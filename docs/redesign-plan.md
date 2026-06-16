# SimpleFOCMini — 60 V Redesign Plan

Working plan for reworking the SimpleFOCMini (TI DRV8313PWPR) from its v1.1
8–24 V rating to the DRV8313's full voltage range. Derived from the audit of
the imported KiCad project (`KiCad/project/`).

## Target specification

| Parameter | Value |
| --- | --- |
| Supply voltage | **8–60 V** (DRV8313: 60 V recommended, 65 V abs max) |
| Continuous current | **1.2 A RMS per phase** (matches TI's datasheet design example) |
| Peak current | up to the DRV8313 limit (2.5 A peak; OCP trips ~5 A) |
| Board size | **≤ 50 × 50 mm** (cheap-fab tier; ~35 mm expected) |
| Stackup | **4-layer, Top / GND / GND / Bottom, 1 oz, 1.6 mm** |
| Library compatibility | SimpleFOC (unchanged pinout/interface) |

Note: "2.5 A per phase" in the DRV8313 datasheet is a **peak** figure; TI
publishes no continuous/RMS rating (it is thermally limited). 1.2 A continuous
is chosen as a thermally realistic target on a small board.

## BOM changes

| Ref | Current | Issue | Change to |
| --- | --- | --- | --- |
| **C3** (VM bulk) | 100 µF **35 V** Al-elec | Hard fail — 35 V on a 60 V rail | 100 µF **100 V** (≥80 V); larger can, reserve area |
| **C1** (charge-pump flying, CP1–CP2) | 100 nF **50 V** X7R | Sees ~VM; must be VM-rated | 100 nF **100 V** X7R. Verify value: TI recommends **10 nF** here |
| **C2** (VCP→VM reservoir) | 100 nF 50 V X7R | Only sees ~11 V (VCP−VM) | **No change** (50 V is fine; TI spec is 16 V) |
| **C4** (V3P3 decouple) | 470 nF **10 V** Y5V | 3.3 V only — voltage OK; Y5V unstable | Optional: 470 nF **16–25 V X7R** |
| **R5 + LED1** (power LED) | across VM via 0603 | At 60 V the 0603 burns 0.7–3.4 W | Re-site LED to **3.3 V (V3P3OUT)** rail, ~680 Ω 0603. Resolve value (BOM 1 k vs part-number 4.7 k) |
| **P1** (motor out) | 2.54 mm 3-pin header | Marginal for 2.5 A peak / 60 V, no retention | **3-pos 5 mm terminal block** (match TB_PWR1) |
| R1–R4, TB_PWR1, U1 | — | OK | None |

## Layout / stackup requirements

- **4-layer** Top / GND / GND / Bottom. Outer layers carry signal + power copper; inner layers are solid GND for thermal spreading and as the return plane for the 60 V switching nodes.
- **Thermal vias under U1's exposed pad (EP):** the current board has **zero** — add a ~4×4 grid of 0.3 mm vias tying the EP to the inner/bottom GND copper. This is the single most important thermal fix.
- **Trace widths at 1.2 A (1 oz):** ≥0.39 mm meets a 10 °C rise; existing 0.5 mm phase traces pass. Widen the **VM trace (currently 0.254 mm → ~0.9 A)** to ≥0.5 mm or distribute via planes.
- **Clearance for 60 V:** current min is 0.20 mm (passes IPC-2221 but thin). Open power-net clearance to **≥0.25–0.3 mm**.
- **Bulk cap:** place close to U1's VM pins, wide/short high-current path, multiple vias (datasheet §10.1).

## Thermal budget (1.2 A, sanity check)

- Conduction loss ≈ 3 × I² × RDS(on): ~1.0 W (25 °C) to ~1.7 W (hot). Call it ~1.5 W with switching.
- With EP vias + GND planes (RθJA ≈ 20 °C/W achievable), ΔTj ≈ 30 °C → Tj ≈ 55 °C at 25 °C ambient. Comfortable vs Tj(max) = 150 °C.

## Open items to verify

- **R5 value** — BOM value column says 1 kΩ; the listed manufacturer part number decodes to 4.7 kΩ. Confirm against the physical board / schematic before reusing.
- **C1 value** — board uses 100 nF for the CP1–CP2 flying cap; DRV8313 datasheet recommends 10 nF. Confirm intended value.
- Charge-pump cap connectivity (C1 across CP1/CP2; C2 across VCP/VM) in the final layout.

## Status

Audit complete; target finalized. Next: apply BOM/value changes in the
schematic, then re-layout on a 4-layer stackup in KiCad.
