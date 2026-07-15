# ADR-0001: Common input PCB with MCU-specific adapters

Status: accepted for V1 planning  
Date: 2026-07-16

## Decision

Build one common input PCB and two small adapter boards, one for XIAO ESP32-S3 Plus and one for XIAO nRF52840 Plus. The common connector carries semantic signals and power domains rather than raw XIAO D0–D19 positions.

## Drivers

- Compare both MCUs without respinning every user input.
- Contain board-specific USB, battery, reset/boot, NFC, JTAG, and RF constraints.
- Make electrical differences visible and reviewable.
- Retain a path to another MCU without discarding the mechanical input assembly.

## Alternatives considered

### Direct XIAO Plus socket on the common PCB

Lower part count and height, but it encourages false pin-compatibility assumptions and makes board-specific power/USB routing difficult to isolate.

### Two complete input PCBs

Maximum freedom for each MCU, but duplicates the largest mechanical PCB and weakens the fairness of comparative testing.

## Consequences

- The enclosure must reserve adapter volume and support the XIAO USB connector.
- Adapter connector height and retention become early mechanical decisions.
- Three PCB designs are fabricated, but only the small adapters vary by MCU.
- Pin changes are localized to adapter schematics and firmware board definitions.

## Follow-ups

- Select the adapter connector and mating height.
- Prototype USB access and antenna clearance.
- Add adapter identity and prevent wrong-firmware assumptions.
- Revisit after V1 selects the final MCU; V2 may integrate that MCU directly.

