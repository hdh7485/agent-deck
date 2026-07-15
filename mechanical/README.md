# Mechanical design structure

## Stack baseline

- Separate switch/control plate, approximately 1.5 mm until the switch family is locked.
- Common input PCB, nominally 1.6 mm.
- MCU adapter below or beside the input PCB with the XIAO USB-C accessible from the enclosure.
- Enclosure support around encoder, navigation switch, USB connector, and other repeated-load parts.

## Proposed tree

```text
mechanical/
  references/      # manufacturer STEP/DXF with source notes
  plate/           # plate source and exports
  enclosure/       # top/bottom enclosure source and exports
  fixtures/        # assembly and touch/force test fixtures
  exports/         # release-only STEP/DXF/STL when versioned
```

## Locked constraints

- No OLED/LCD window.
- All keys, LEDs, encoder, navigation switch, and touch electrode originate from PCB coordinates.
- The plate or enclosure carries repeated encoder/navigation force instead of relying only on solder pads.
- RF antenna regions remain free of metal plate, battery, dense copper, and enclosure features that violate the board guidance.
- Reset/boot/SWD service access remains possible without destructive disassembly during V1.
- USB cable shell and strain envelope are modeled, not just the receptacle body.

## Dimensions required before CAD release

- Switch/keycap family, pitch, travel, and plate cutout.
- Encoder shaft/body/tab/knob dimensions and target protrusion.
- Navigation switch body, cap, travel, and support surfaces.
- Touch diameter, overlay thickness, and finger clearance.
- Adapter connector stack height and XIAO component/antenna envelopes.
- Battery dimensions, swelling allowance, connector, and retention.
- Fastener diameter, insert/boss geometry, and assembly order.

Build a low-cost plate and enclosure fit check before committing to final material or finish.

