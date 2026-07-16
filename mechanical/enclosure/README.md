# Agent Deck V1 enclosure fit-check

Status: printable mechanical fit-check, not a production enclosure release.

## Parts

| File | Purpose | Recommended print orientation |
| --- | --- | --- |
| `agent-deck-v1-bottom.stl` | PCB tray, M3 bosses, provisional side service opening | base flat on bed |
| `agent-deck-v1-top-bezel.stl` | perimeter bezel and replaceable-plate ledge | widest flat face on bed |
| `agent-deck-v1-mx-plate.stl` | 12-key MX control plate; K11 2u stabilizer geometry remains open | top face on bed for a clean touch membrane |

The files are under `mechanical/exports/v1-fit-check/`. Import as millimetres without scaling.

## Nominal dimensions

- PCB source envelope: 118.0 mm × 118.0 mm × 1.6 mm.
- Case body: 125.8 mm × 125.8 mm × 17.0 mm before keycaps and knobs.
- Wall/base: 2.4 mm.
- PCB bottom above case floor: 5.5 mm.
- Plate: 118.8 mm × 118.8 mm × 1.5 mm.
- MX openings: 14.2 mm square at the PCB's 19 mm pitch.
- Key stack: 5-pin MX-compatible switch holes with bottom-mounted Kailh `CPG151101S11-16` hot-swap sockets; 1.25 mm nominal socket-to-floor clearance.
- Touch feature: 18.0 mm recess with a provisional 0.8 mm membrane.
- K11 sits immediately right of the touch center at a 29.0 mm center pitch and is rendered as a 36.2 mm-wide 2u push-to-talk keycap. Its MX switch and per-key RGB remain single matrix/LED positions.
- Nominal touch-to-K11 separation: 12.9 mm to the centered MX plate opening and 1.9 mm to the 2u keycap envelope.
- The microphone pictogram is render-only. K11 opens host-side voice capture while held; the device design does not add or claim an onboard microphone.
- The exact 2u keycap and stabilizer family are not selected. The current plate keeps only the center MX opening, so stabilizer cutouts/PCB holes must be added from the selected manufacturer's drawing before fabrication.
- C30 candidate clearance to the plate underside: 2.1 mm nominal.
- Navigation control: provisional ALPS `RKJXM1015004` 11 mm body, 12 mm plate opening, and 14 mm low round concave cap.
- Side service opening: 26.0 mm × 7.6 mm, provisional.

The machine-readable dimensions and manifold results are in `mechanical/exports/v1-fit-check/dimensions.json`.

## Prototype print settings

- PLA or PETG for the first fit check.
- 0.20 mm layer height.
- At least three perimeters and four top/bottom layers.
- 20% infill is adequate for the dimension coupon; increase around the control plate if flex is observed.
- No supports should be required in the documented orientation, but slicer bridge preview remains mandatory.
- Use M3 fasteners only after measuring printed hole shrinkage; the 3.4 mm model holes are clearance candidates, not a guaranteed printer profile.

## Blocking checks before calling this an enclosure revision

- Select the exact MX switch, 1u/2u keycaps, K11 stabilizer, encoder, and knob; verify the selected Kailh socket and RKJXM candidate samples.
- Confirm the plate-to-PCB stack against physical switch samples.
- Lock the MCU adapter connector orientation and replace the broad service slot with the exact USB-C cable envelope.
- Add the selected battery volume, swelling allowance, retention, and cable path.
- Print touch coupons around 0.6, 0.8, 1.0, and 1.2 mm membrane thickness and measure recognition during RGB switching and charging.
- Check antenna clearance using the exact XIAO board, adapter, plate material, fasteners, and battery.
- Perform a first-article assembly before adding snaps, heat-set inserts, cosmetic textures, or production tolerances.

## Regeneration

The authoritative source is `mechanical/scripts/generate_enclosure.py`. It creates all three STL files, assembled/exploded preview images, `dimensions.json`, and an ignored Blender artifact for inspection.
