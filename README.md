# DRV8313 Board

An open-hardware **3-phase motor driver module** built around the Texas Instruments
[**DRV8313**](https://www.ti.com/lit/ds/symlink/drv8313.pdf) (three half-bridges, 8–60 V).
It drives BLDC/PMSM motors (3-PWM / FOC, e.g. with [SimpleFOC](https://simplefoc.com)),
and — because the three half-bridges and their enables are broken out independently —
also brushed-DC motors, solenoids, and 6-step/trapezoidal loads.

<img src="images/board-3d-top.png" height="300"/> <img src="images/board-3d-bottom.png" height="300"/>

> Derived from the [SimpleFOCMini](https://github.com/simplefoc/SimpleFOCMini) board
> ([EasyEDA source](https://easyeda.com/the.skuric/simplefocmini)) and re-engineered for
> the DRV8313's full voltage range. It has since diverged substantially from the original
> (higher voltage, larger 4-layer board, on-board current limit, independent half-bridge
> enables), hence the separate project.

## Specifications

| | |
| --- | --- |
| Driver | DRV8313PWPR (HTSSOP-28, exposed thermal pad) |
| Supply voltage | **8–60 V** |
| Continuous current | **~1.5 A / phase** (1 oz copper, Tj ≤ 125 °C; ~2 A with airflow). The datasheet's 2.5 A/phase is a *peak* rating. |
| Logic level | 3.3 V (DRV8313 on-chip `V3P3OUT` regulator; no separate LDO) |
| Board | **50 × 45 mm**, 4-layer (Top / GND / GND / Bottom, 1 oz) |
| Control | 3× IN (PWM) + 3× independent EN; nRESET / nSLEEP / nFAULT |
| Current limit | On-board comparator, cycle-by-cycle (50 mΩ shunt + reference divider) |
| Connectors | 2×7 control header, 5-pos motor/VM terminal block, 2-pos power terminal block |

### Features beyond the original SimpleFOCMini

- **8–60 V** input (vs. 8–24 V) on a 4-layer board with inner ground planes.
- **On-board over-current limit** using the DRV8313's internal comparator (`COMPP`/`COMPN`):
  a 50 mΩ low-side shunt and a 3.3 V reference divider, with two solder jumpers to set the
  trip point — both intact ≈ 2.5 A, cut `SJ1` ≈ 1.5 A, cut `SJ2` disables the limit. The
  comparator output (`nCOMPO`) is brought out on the header.
- **Independent half-bridge enables** (`EN1`/`EN2`/`EN3` on their own series resistors) so the
  board can run brushed-DC / solenoid / 6-step loads. Tie them together at the header to get
  the original ganged 3-PWM/FOC enable.

## Renders

| Schematic | PCB (top) | PCB (bottom) |
| --- | --- | --- |
| <img src="images/schematic.svg" width="260"/> | <img src="images/pcb-top.svg" width="220"/> | <img src="images/pcb-bottom.svg" width="220"/> |

## Repository layout

| Path | Contents |
| --- | --- |
| [`KiCad/project/`](./KiCad/project/) | KiCad 10 source — schematic, PCB, project, and the `simplefocmini.pretty` footprint library |
| [`manufacturing/`](./manufacturing/) | Fabrication outputs: [`gerbers/`](./manufacturing/gerbers/) (Gerber + Excellon drill), [BOM](./manufacturing/drv8313-board-BOM.csv), [pick-and-place CPL](./manufacturing/drv8313-board-CPL.csv), and a [STEP](./manufacturing/drv8313-board.step) 3D model |
| [`docs/`](./docs/) | [`redesign-plan.html`](./docs/redesign-plan.html) (target spec + analysis), [`redesign-bom.md`](./docs/redesign-bom.md) (part-selection worklist), [`datasheets/`](./docs/datasheets/) (DRV8313 datasheet) |
| [`tools/`](./tools/) | Headless helper scripts — JLCPCB part search, manufacturing-file regeneration, silk version bump ([`tools/README.md`](./tools/README.md)) |
| [`images/`](./images/) | Renders used above |

The design is maintained **only** in KiCad now; the original Altium / EasyEDA / PDF exports
have been removed. The manufacturing files are regenerated from the KiCad project with
[`tools/build_manufacturing.py`](./tools/build_manufacturing.py) (a `kicad-cli` wrapper).

## Ordering

The board is designed to be fabricated and assembled at [JLCPCB](https://jlcpcb.com):

1. Upload `manufacturing/gerbers/` (zipped) for fabrication — 4-layer, 1 oz.
2. Use `manufacturing/drv8313-board-BOM.csv` and `manufacturing/drv8313-board-CPL.csv`
   for assembly. Every line carries an LCSC part number. Most parts are **fee-free** on
   JLCPCB — Basic or Preferred, no per-part setup fee — including the 43 k/62 k divider
   resistors (Preferred). The unavoidable **Extended** parts are the DRV8313 itself, the
   10 nF/100 V and 47 µF/100 V capacitors, the 50 mΩ current-sense shunt, and the three
   connectors. The connectors — `H1` (2×7 header), `P1` and `TB_PWR1` (5 mm screw terminal
   blocks) — are **through-hole**: order them via JLCPCB's through-hole assembly add-on or
   solder them by hand. Re-verify live stock before ordering — `tools/jlc_search.py` checks
   live stock/price (note: the 10 kΩ Basic resistor occasionally reads out of stock).

> **Status:** functional design — schematic and PCB are complete and pass DRC/ERC
> (0 errors, fully routed). Not yet fabricated/validated in hardware. Review before ordering.

## License

See [`LICENSE`](./LICENSE). This project inherits from the open-source SimpleFOCMini; please
also credit the original authors.

## Credits

Based on [**SimpleFOCMini**](https://github.com/simplefoc/SimpleFOCMini) by the
[SimpleFOC](https://simplefoc.com) project (Antun Skuric et al.).
