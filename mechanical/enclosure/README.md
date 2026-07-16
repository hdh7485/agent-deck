# Agent Deck V1 enclosure fit-check

Status: printable mechanical fit-check, not a production enclosure release.

## Parts

| File | Purpose | Recommended print orientation |
| --- | --- | --- |
| `agent-deck-v1-bottom.stl` | PCB/adapter/battery tray, support bosses, exact fit-check USB opening | base flat on bed |
| `agent-deck-v1-top-bezel.stl` | perimeter bezel and replaceable-plate ledge | widest flat face on bed |
| `agent-deck-v1-mx-plate.stl` | 12-key MX control plate with K11 2u stabilizer cutouts | top face on bed for a clean touch membrane |

The files are under `mechanical/exports/v1-fit-check/`. Import as millimetres without scaling.

## Nominal dimensions

- PCB source envelope: 100.0 mm × 100.0 mm × 1.6 mm.
- Case body: 107.8 mm × 107.8 mm × 33.17 mm before keycaps and knobs.
- Wall/base: 2.4 mm.
- Main PCB bottom above case floor: 19.37 mm.
- MCU adapter: 81.0 mm × 43.0 mm × 1.6 mm with bottom at 10.3 mm.
- Battery fit-check: protected Jauch `LP603443JU`, 34.5 mm × 45.0 mm × 6.0 mm, with 1.5 mm nominal clearance to the adapter PCB.
- Adapter connector fit-check: Samtec `HLE-110-02-G-DV-A` and `TSM-110-04-L-DV-A`, 7.47 mm nominal mated stack.
- Plate: 100.8 mm × 100.8 mm × 1.5 mm.
- MX openings: 14.2 mm square at the PCB's 19 mm pitch.
- Key stack: 5-pin MX-compatible switch holes with bottom-mounted Kailh `CPG151101S11-16` hot-swap sockets; 15.12 mm nominal socket-to-floor clearance.
- Touch feature: 18.0 mm recess with a provisional 0.8 mm membrane.
- All keycap centers use a 19.0 mm lattice. The 17.2 mm 1u and 36.2 mm 2u envelopes preserve a nominal 1.8 mm gap horizontally and vertically.
- Every keycap is rendered with the same blank black-smoke translucent finish. K11 retains its host-side hold-to-talk mapping without a microphone legend.
- K11 sits immediately right of the touch center at a 28.5 mm center pitch and is rendered as a 36.2 mm-wide 2u keycap. Its MX switch and per-key RGB remain single matrix/LED positions.
- Nominal touch-to-K11 separation: 12.4 mm to the centered MX plate opening and 1.4 mm to the 2u keycap envelope.
- K11 fit-check stabilizer: Gateron `KS-52B200T-01`, 23.8 mm center spacing. Plate cutouts and PCB mounting holes are modeled but remain sample-dependent.
- C30 candidate clearance to the plate underside: 4.4 mm nominal.
- Navigation control: provisional ALPS `RKJXM1015004` 11 mm body, 12 mm plate opening, and 14 mm low round concave cap.
- XIAO onboard USB-C opening: 12.5 mm × 8.0 mm centered on the adapter USB datum. Cable shell/strain envelope is included in the internal fit-check render.

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
- Verify the selected HLE/TSM suffixes, mating force, tolerance, and solder-joint inspection access with samples.
- Verify the XIAO USB shell protrusion, cable strain relief, U.FL cable bend, shield height, and RF keep-out with the exact purchased board revision.
- Verify the battery lead/protection-board protrusion, swelling allowance, retention, and charge-cycle temperature.
- Verify the Gateron stabilizer screw/washer stack and first-article plate retention.
- Print touch coupons around 0.6, 0.8, 1.0, and 1.2 mm membrane thickness and measure recognition during RGB switching and charging.
- Check antenna clearance using the exact XIAO board, adapter, plate material, fasteners, and battery.
- Perform a first-article assembly before adding snaps, heat-set inserts, cosmetic textures, or production tolerances.

## Regeneration

The authoritative source is `mechanical/scripts/generate_enclosure.py`. It creates all three STL files, assembled/top/exploded/internal-stack preview images, `dimensions.json`, and an ignored Blender artifact for inspection.
