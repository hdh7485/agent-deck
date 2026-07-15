# KiCad project structure

Create separate KiCad projects so common-input changes and board-specific adapter changes remain reviewable.

```text
hardware/kicad/
  input-main/
    input-main.kicad_pro
    input-main.kicad_sch
    input-main.kicad_pcb
  adapters/
    xiao-esp32s3-plus/
      xiao-esp32s3-plus.kicad_pro
      xiao-esp32s3-plus.kicad_sch
      xiao-esp32s3-plus.kicad_pcb
    xiao-nrf52840-plus/
      xiao-nrf52840-plus.kicad_pro
      xiao-nrf52840-plus.kicad_sch
      xiao-nrf52840-plus.kicad_pcb
  libraries/
    agent-deck.kicad_sym
    agent-deck.pretty/
    3dmodels/
  templates/
  scripts/
```

## Main schematic hierarchy

- `00_interface`: semantic adapter connector, test points, board identity.
- `10_keys`: 13 switches, diodes, 4×4 matrix.
- `20_io_expander`: MCP23017, address/reset, I2C, interrupts.
- `30_controls`: encoder, navigation, touch controller/electrode.
- `40_rgb`: LEDs, buffer, data resistor, decoupling.
- `50_power`: RGB load switch/current limit, rail test points, optional battery-RGB experiment kept isolated.

## Adapter schematic hierarchy

- XIAO symbol/footprint from the matching official Seeed design resources.
- Semantic connector mapping.
- USB-C access and enclosure reference.
- Battery connector/board charger interface.
- Reset/boot/debug/SWD test pads.
- Antenna keep-out and mechanical outline.
- Adapter identity.

## Library policy

- Copy only project-used symbols/footprints into the project library when licensing permits, preserving attribution and source revision.
- Verify every pad number and courtyard against the selected component drawing.
- Do not trust community footprints for XIAO bottom pads, hot-swap sockets, encoders, or navigation switches without a dimension check.
- Keep generated fabrication outputs out of Git unless a release process explicitly snapshots them.

## Coordinate contract

The common PCB origin, key centers, plate origin, mounting holes, adapter connector, USB datum, encoder axis, navigation axis, and touch center form a versioned mechanical interface. Mechanical CAD imports these coordinates; it must not re-create them by eye.

## Gates

No board is ordered until exact components pass `docs/hardware/design-inputs-checklist.md`, ERC/DRC pass, official XIAO mappings are rechecked, 3D interference is reviewed, and first-article power tests are prepared.

## Generated V1 draft

The repository now contains all three KiCad projects described above. The main PCB has complete component placement and electrical net assignments, plus safe local matrix routing. Long routes remain as ratsnest until the blocking mechanical selections are locked. This is deliberate: the first automatic long-route experiment produced real crossings and was discarded rather than hidden with exclusions.

Regenerate with KiCad 10.0.4's bundled Python:

```sh
/opt/homebrew/Caskroom/kicad/10.0.4/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 \
  hardware/kicad/scripts/generate_design.py
```

The generator transcribes the XIAO Plus physical land pattern from Seeed's official Plus baseboard resource and uses the conservative semantic mapping in `docs/hardware/pin-compatibility.md`. It does not claim that the two MCU boards are electrically interchangeable.

See `VALIDATION.md` for the fresh ERC/DRC evidence and the explicit fabrication stop condition.
