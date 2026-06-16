# SimpleFOCMini v1.1

<img height="200px" src="./images/side.png"  /><img height="200px" src="./images/top.png" /><img height="200px" src="./images/bottom.png"  />

<img height="350px" src="./images/schema.png" align="right"/>


## Features
- DRV8313 based - [datasheet](https://www.ti.com/lit/ds/symlink/drv8313.pdf?ts=1650461862269&ref_url=https%253A%252F%252Fwww.google.com%252F)
  - Power supply: 8-24V
  - Max current: 2.5A per phase
  - Onboard 3.3V LDO
- Small size 26x21 mm
- Fully compatible with the *Simple**FOC**library*
- Fully open-source: [EasyEDA link](https://easyeda.com/the.skuric/simplefocmini)
- Low-cost: JLCPCB production cost ~3-5€
- Available in the [shop](https://www.simplefoc.com/shop) 10-15€ 

## New features in v1.1
- Aligned motor output header with the input header so that it can be stacked in the protoboard
- Input header updated to be easier to use with arduino UNO, nucleos, but also with qtpy...
  - Changed the order of the IN1,IN2,IN3 and EN: 
  - Added an additional GND pin 
- First batch of the SimpleFOCMini V1.1 will be available in the [shop](https://www.simplefoc.com/shop) soon: Price: 10-15€ 

## Getting started with SimpleFOCMini

See the documentation in the [SimpleFOC documentation](https://docs.simplefoc.com/simplefocmini) page. 
- The docs explain how to start with the SimpleFOCMini board and how to use it with the SimpleFOC library. 
- They also describe how you can order it directly from the JLCPCB.

## Design files

The board design is provided in several formats:

| Path | Contents |
| --- | --- |
| [`Altium/`](./Altium/) | Altium schematic (`.schdoc`) and PCB (`.pcbdoc`), dated 2024-04-26 |
| [`EasyEDA/`](./EasyEDA/) | EasyEDA Standard schematic and PCB JSON exports (editor v6.5) |
| [`Gerber/`](./Gerber/) | Fabrication Gerbers and Excellon drill files |
| [`KiCad/project/`](./KiCad/project/) | KiCad 10 project, imported from the EasyEDA Standard JSON files |
| [`3D model/`](./3D%20model/) | Board 3D model (`.obj` + `.mtl`) |
| [`BOM_simplefocmini_2024-04-26.csv`](./BOM_simplefocmini_2024-04-26.csv) | Bill of materials |
| [`Pick and Place/`](./Pick%20and%20Place/) | Pick-and-place / centroid file |
| [`Schematic_simplefocmini.pdf`](./Schematic_simplefocmini.pdf) | Rendered schematic |

The KiCad 10 project was created by importing the EasyEDA Standard files; KiCad 10 does not import the Altium `.pcbdoc`/`.schdoc` format.

### Fork: 60V / 2.5A redesign (in progress)

This fork is reworking the board toward the DRV8313's full operating range. The DRV8313 is rated 8–60V / 2.5A peak per phase ([datasheet](https://www.ti.com/lit/ds/symlink/drv8313.pdf)); the v1.1 design above is specified at 8–24V. The KiCad project under [`KiCad/project/`](./KiCad/project/) is the working design for this effort.

## Release log

Release | Date | Description
--- | --- | ---
v1.1 | 2024-04 | A quick iteration with a few changes: <p> 1. Aligned motor output header with the input header so that it can be stacked in the protoboard<br>2. Input header updated to be easier to use with arduino UNO, nucleos, but also with qtpy...<br> - Changed the order of the IN1,IN2,IN3 and EN: <br>    - Added an additional GND pin <br>
v1.0 | 2022-04 | Initial release

## Size comparison

<img  src="https://user-images.githubusercontent.com/36178713/164240473-5abd7453-9d38-4f25-9195-378c39180054.jpg" />
