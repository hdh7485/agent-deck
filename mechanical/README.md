# Mechanical design structure

## Stack baseline

- Separate 1.5 mm MX switch/control plate for the V1 fit-check.
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

- Exact MX switch/keycap MPN, travel, and retention tolerance; family, 19 mm pitch, 14.2 mm cutout, and Kailh socket candidate are selected.
- Encoder shaft/body/tab/knob dimensions and target protrusion.
- Navigation switch body, cap, travel, and support surfaces.
- Touch diameter, overlay thickness, and finger clearance.
- Adapter connector stack height and XIAO component/antenna envelopes.
- Battery dimensions, swelling allowance, connector, and retention.
- Fastener diameter, insert/boss geometry, and assembly order.

Build a low-cost plate and enclosure fit check before committing to final material or finish.

## V1 printable fit-check

![Agent Deck V1 top control layout](../docs/images/mechanical/agent-deck-v1-controls-top.png)

![Agent Deck V1 enclosure](../docs/images/mechanical/agent-deck-v1-enclosure-assembled.png)

The repository now includes a parametric Blender generator and three manifold STL fit-check parts:

- bottom tray with common-PCB and MCU-adapter support geometry;
- top bezel with a replaceable plate ledge;
- 1.5 mm MX plate with twelve 14.2 mm switch openings, K11 2u stabilizer cutouts, encoder and navigation openings, and a 0.8 mm touch membrane.

![Agent Deck V1 internal stack](../docs/images/mechanical/agent-deck-v1-internal-stack.png)

The common PCB is 100 mm square and the body is 107.8 mm × 107.8 mm × 33.17 mm before controls. All keycaps use one blank black-smoke translucent render material. Their centers follow a 19 mm lattice; 17.2 mm 1u and 36.2 mm 2u envelopes retain a nominal 1.8 mm key-to-key gap.

The generated assembly now models:

- Jauch `LP603443JU` battery candidate envelope and cable space.
- 81 mm × 43 mm MCU adapter PCB.
- Samtec HLE/TSM 7.47 mm fit-check mating stack.
- Common PCB, MCP23017 body, C30, reverse-mount RGB and hot-swap sockets.
- XIAO board, onboard USB-C, cable insertion envelope, and RF keep-out.
- EC11-class encoder, RKJXM-class navigation body/cap, and K11 2u stabilizer.

Nominal clearances include 1.5 mm from the battery envelope to the adapter PCB, 7.2 mm from the common PCB top to the plate bottom, and 4.4 mm from C30 to the plate underside. These are CAD fit-check values, not measured production tolerances.

The generator reports zero non-manifold edges for the bottom tray, bezel, and plate. Physical samples are still required for connector mating force, USB shell/cable protrusion, battery protection-board and swelling envelope, touch overlay sensitivity, RF performance, and stabilizer retention.

Generate the STL files and preview images with:

```sh
blender --background --factory-startup --python mechanical/scripts/generate_enclosure.py
```

See `mechanical/enclosure/README.md` for print orientation, dimensions, and the explicit fit-check limitations.
