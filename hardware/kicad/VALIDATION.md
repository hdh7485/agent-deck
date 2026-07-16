# KiCad V1 draft validation

Validated with KiCad CLI 10.0.4 on 2026-07-16.

## Result

| Project | Block ERC | DRC violations | Unconnected | Interpretation |
| --- | ---: | ---: | ---: | --- |
| Common input PCB | 0 | 0 errors, 37 warnings | 117 | 100 mm square placement/netlist and mechanical fit-check; not fabrication-ready |
| ESP32-S3 Plus adapter | 0 | 0 errors, 13 warnings | 21 | 81 × 43 mm placement/netlist fit-check; routing intentionally open |
| nRF52840 Plus adapter | 0 | 0 errors, 13 warnings | 21 | 81 × 43 mm placement/netlist fit-check; routing intentionally open |

Zero DRC errors does not mean the boards are routed. KiCad reports unconnected items separately, and those open connections are a fabrication blocker.

The current `.kicad_sch` files are architecture/block schematics, not release schematics with one symbol for every PCB footprint. An additional `--schematic-parity` diagnostic therefore reports 74 extra PCB footprints on the common board and 7 on each adapter. That result is expected for this draft, but it is also a fabrication blocker: release schematics must be expanded until reviewed board/schematic parity passes.

The common board warnings are:

- 14 library-footprint mismatch warnings caused by generated/project-local fit-check footprints.
- 15 silkscreen-over-copper warnings.
- 1 silkscreen-overlap warning.
- 6 dangling-track warnings in the retained local matrix draft.
- 1 isolated `+3V3` copper-fill warning caused by the intentionally open power routing.

Each adapter has 13 warnings: 1 library-footprint mismatch, 2 silkscreen-to-board-edge, 3 silkscreen-over-copper, 2 silkscreen-overlap, 4 text-height, and 1 isolated GND copper-fill warning caused by the intentionally open routing.

## What passed

- All three `.kicad_sch` files parse and report zero ERC violations.
- All three `.kicad_pcb` files parse, refill copper zones, run DRC, and render through the KiCad CLI.
- All three boards have zero error-severity DRC violations in the current placed geometry.
- The common board outline, copper-zone inset, 90 mm square mounting-hole pattern, and enclosure source agree on an independent 100 mm × 100 mm PCB datum and the same top-side control map: encoder, two keys, navigation; four keys; four keys; touch, 2u PTT, auxiliary key.
- The `J1` adapter connector, `U1` expander, encoder, navigation candidate, K11 stabilizer holes, mounting holes, and current component envelopes have no error-severity drilled-hole or geometric collision.
- D16 is isolated as `BAT_SENSE_D16_RESERVED` on both adapters.

## Stop condition

Do not generate Gerbers or order boards from this revision. Before fabrication:

1. Route all 117 common-board and 21-per-adapter open connections.
2. Review every remaining warning and either correct it or record a narrow waiver.
3. Replace the block schematics with complete release schematics and pass reviewed board/schematic parity.
4. Lock the exact orderable switch/socket, navigation, adapter connector suffix, battery, touch overlay, stabilizer, and mechanical fasteners from physical samples.
5. Re-run ERC/DRC, fabrication-output orientation review, power-path review, and assembled 3D/first-article fit checks.

## Reproduction

```sh
KICAD=/opt/homebrew/Caskroom/kicad/10.0.4/KiCad/KiCad.app/Contents/MacOS/kicad-cli

$KICAD sch erc hardware/kicad/input-main/input-main.kicad_sch
$KICAD pcb drc --refill-zones --format json \
  --output /tmp/input-main-drc.json \
  hardware/kicad/input-main/input-main.kicad_pcb
```

Repeat the commands for each project under `hardware/kicad/adapters/`.
