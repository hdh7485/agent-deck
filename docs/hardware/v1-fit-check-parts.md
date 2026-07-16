# V1 fit-check parts and release gates

This document locks a small set of physical candidates for the 100 mm × 100 mm V1 assembly. It does not claim that the public OpenAI or Codex Micro product uses these internal parts.

## Meaning of lock states

`Fit-check candidate locked` means:

- use the named part and official geometry in the PCB, plate, and enclosure models;
- purchase a small sample quantity when practical;
- reject alternatives that do not fit the same verified envelope without a new review.

`Production/order locked` additionally requires:

- exact orderable MPN and suffix, lifecycle, authorized source, and lead time;
- current formal manufacturer drawing or configured-pack delivery drawing;
- land pattern, polarity, assembly side, tolerance, and 3D orientation review;
- physical sample fit and the applicable electrical or durability test.

No part in this document is production/order locked yet.

## Candidate register

| Function | Fit-check candidate | Official or derived fit facts | State and remaining gate |
| --- | --- | --- | --- |
| MX key switch | CHERRY `MX2A-L1NB` | Officially the RGB Red 5-pin PCB-mount variant; 45 cN actuation, 2 mm pretravel, 4 mm total travel, and an opening for a PCB-mounted SMD LED | Fit-check candidate locked. Verify the exact purchased revision with the Kailh socket, 1.5 mm plate, keycap, LED, and switch-removal clearance |
| MX hot-swap socket | Kailh `CPG151101S11-16` | Official drawing: bottom-side assembly, 14.50 ±0.15 mm × 5.89 ±0.10 mm body, 1.85 ±0.10 mm height, and 6.35 ±0.10 mm switch-contact center spacing | Fit-check candidate locked. Transcribe the complete recommended land pattern, confirm genuine revision, and test switch insertion/removal |
| 2u stabilizer | Gateron `KS-52B200T-01` screw-in stabilizer | Official product supports normal 2 mm/4 mm switch travel and supplies 2u wires. Measurement from the official STEP gives 23.8 mm between stabilizer centers | Fit-check candidate locked. Import the STEP on the PCB datum and derive holes, screw access, wire sweep, socket clearance, and keycap fit. The raw CAD bounding box is not a released clearance |
| Encoder | ALPS Alpine `EC11E15244G1` | Vertical, 30 detents/15 pulses, push-on, nominal 20 mm actuator, Ø6 mm flat shaft, approximately 11.7 mm × 12 mm body, and 12.5 ±0.05 mm stabilizer-tab span in the official drawing | Fit-check candidate locked. Confirm mounting holes, board-to-top height, knob engagement, tab support, and actuation load using a sample |
| Navigation switch | ALPS Alpine `RKJXM1015004` | Official body 11 mm × 11 mm × 6.6 mm; 8-direction plus center push; nominal 15 ±0.4 mm actuator height and official mounting-side hole pattern | Fit-check candidate locked. Transcribe and independently check every terminal/support hole, then test the custom 14 mm cap and case support. ALPS calls the catalog dimensions outline specifications |
| Adapter socket | Samtec `HLE-110-02-G-DV-A` | 2 × 10 contacts on 2.54 mm pitch; low-profile vertical HLE `-02` lead style | Fit-check candidate locked only as part of the pair below. Check exact series print, alignment-pin holes, footprint, current, retention, and availability |
| Adapter header | Samtec `TSM-110-04-L-DV-A` | 2 × 10 contacts on 2.54 mm pitch; vertical surface-mount TSM `-04` lead style | Fit-check candidate locked only as part of the pair below. Check exact series print, alignment-pin holes, footprint, coplanarity, and availability |
| Adapter mated stack | HLE `-02` plus TSM `-04` | Samtec's official characterization report identifies a 7.47 mm stack for `TSM-130-04-L-DV-A` and `HLE-130-02-G-DV` | Use 7.47 mm as the nominal PCB-to-PCB fit-check target. The report uses 30-position parts and does not replace CAD/sample measurement of the exact 10-position `-A` pair |
| Battery | Jauch `LP603443JU` | Official list: 3.7 V, 850 mAh, catalog cell envelope 6.0 mm × 34.5 mm × 45.0 mm. Jauch states that its Li-polymer batteries include overcharge protection circuitry | Fit-check candidate locked. The enclosure must additionally allow the configured protection PCB, lead exit, connector, padding, strain relief, and pouch swelling. Obtain a project-specific delivery drawing and sample |
| RGB bulk geometry | Panasonic `10TPF150ML` | Official table: 150 µF, 10 V, D3L, 7.3 mm × 4.3 mm × 2.8 mm, 15 mΩ maximum ESR | Geometry reference only. Panasonic marks it NRFND, so it must not be promoted to order lock |
| RGB bulk replacement | Panasonic `10TAE150ML` | Official table: 150 µF, 10 V, D3L, 7.3 mm × 4.3 mm × 2.8 mm, 25 mΩ maximum ESR | Replacement fit-check candidate. Revalidate lifecycle, authorized stock, land pattern, polarity, inrush, ESR effect, and transient performance before order lock |
| RGB bulk comparison | Panasonic `10TVE150ML` | Same 150 µF, 10 V, D3L 7.3 mm × 4.3 mm × 2.8 mm envelope and 25 mΩ maximum ESR | Geometry/electrical comparison only. The current Panasonic North American TV-series page is marked discontinued |

## Adapter and XIAO envelope

Both official XIAO Plus board resources use a 21 mm × 17.8 mm board outline. That common outline does not make the boards electrically or mechanically interchangeable.

The enclosure model must reserve separate adapter-specific volumes for:

- exact XIAO board maximum height and bottom-pad/socket construction;
- USB-C shell, board-edge overhang, plug body, cable bend, and user insertion clearance;
- ESP32-S3 Plus U.FL plug, coax bend, and external antenna placement;
- nRF52840 Plus onboard antenna and RF keep-out;
- reset, boot, SWD/UART, and battery-service access.

The official Seeed board resources do not provide every assembled USB, shield, cable, and antenna maximum envelope needed to close the case. Those values remain physical-sample measurements.

## Required physical fit assembly

Build one non-powered mechanical stack before PCB fabrication release:

1. A 1.6 mm common-PCB coupon with the exact HLE socket footprint.
2. The exact HLE/TSM pair and a 1.6 mm adapter coupon.
3. One of each purchased XIAO Plus revision, fitted exactly as intended for V1.
4. The CHERRY switch, Kailh socket, 1.5 mm plate coupon, blank black-smoke keycap, and Gateron 2u stabilizer.
5. The encoder with intended knob and the navigation switch with multiple printed cap-bore tolerances.
6. The configured Jauch battery sample or an inert dimensional dummy that includes the delivery-drawing protection board, wire exit, connector, padding, and swelling allowance.

Record:

- actual mated PCB-to-PCB height and connector seating;
- maximum assembled Z on both sides of each PCB;
- insertion/removal access and force;
- USB and antenna interference;
- switch, stabilizer, encoder, and navigation load transfer into the plate/case;
- battery removal path and absence of compression, sharp edges, screw intrusion, or hot-component contact.

## Promotion to order lock

A candidate may be promoted only after:

1. The exact MPN and suffix match the current official source.
2. Lifecycle and orderability are checked immediately before purchase.
3. The manufacturer drawing or configured delivery drawing is attached to the review evidence.
4. KiCad footprint and 3D orientation are independently checked.
5. A purchased sample fits the PCB/plate/case stack.
6. Electrical ratings and the applicable bench tests pass.

Alternatives sharing nominal dimensions are not assumed to be pin-, footprint-, optical-, or tolerance-compatible.
