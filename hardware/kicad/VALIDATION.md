# KiCad V1 draft validation

Validated with KiCad CLI 10.0.4 on 2026-07-16.

## Result

| Project | ERC | DRC violations | Unconnected | Interpretation |
| --- | ---: | ---: | ---: | --- |
| Common input PCB | 0 | 69 errors, 37 warnings | 115 | Square placement/netlist draft; not fabrication-ready |
| ESP32-S3 Plus adapter | 0 | 0 errors, 11 warnings | 15 | Placement/netlist draft; routing intentionally open |
| nRF52840 Plus adapter | 0 | 0 errors, 11 warnings | 15 | Placement/netlist draft; routing intentionally open |

The common-board errors are limited to the 12 reverse-mount SK6812 Mini-E footprints:

- 48 copper-to-local-cutout edge-clearance findings from KiCad's standard reverse-mount LED footprint.
- 21 courtyard overlaps because the reverse-mount LEDs intentionally sit under a key-envelope edge or between adjacent rows on the uniform 19 mm pitch.

No shorting-item or track-crossing finding remains. The remaining warnings are silkscreen/courtyard/library hygiene items expected in the placement draft.

## What passed

- All three `.kicad_sch` files parse and report zero ERC violations.
- All three `.kicad_pcb` files parse, refill copper zones, run DRC, and render through the KiCad CLI.
- The two adapter boards have zero DRC errors before routing.
- The main PCB has no reported shorting-item, inter-net clearance, hole-clearance, or track-crossing finding in its retained local matrix routing. `K11`'s column segment remains intentionally unrouted until the sample socket footprint is frozen.
- The common board outline, copper-zone inset, mounting holes, and enclosure source agree on an independent 118 mm × 118 mm PCB datum and the same top-side control map: encoder, two keys, navigation; four keys; four keys; touch, 2u PTT, auxiliary key.
- D16 is isolated as `BAT_SENSE_D16_RESERVED` on both adapters.

## Stop condition

Do not generate Gerbers or order boards from this revision. Release routing starts only after the exact switch/socket, five-way switch, adapter connector stack height, touch overlay, and plate geometry are locked. Before fabrication, all open connections must be routed, the LED cutout/land pattern must receive a documented rule review, and the required ERC/DRC/3D gates in `AGENTS.md` must pass.

## Reproduction

```sh
KICAD=/opt/homebrew/Caskroom/kicad/10.0.4/KiCad/KiCad.app/Contents/MacOS/kicad-cli

$KICAD sch erc hardware/kicad/input-main/input-main.kicad_sch
$KICAD pcb drc --refill-zones hardware/kicad/input-main/input-main.kicad_pcb
```

Repeat the commands for each project under `hardware/kicad/adapters/`.
