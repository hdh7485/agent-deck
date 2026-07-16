# ADR-0013: Use a low-profile adapter pair and a bounded battery fit candidate

Status: accepted for the V1 fit-check; not a fabrication or procurement release
Date: 2026-07-16

## Decision

Replace the provisional Samtec `TSW-110-07-G-D` plus `SSW-110-02-G-D` adapter pair with a low-profile 2 × 10, 2.54 mm-pitch fit-check pair:

- common-PCB socket: Samtec `HLE-110-02-G-DV-A`;
- MCU-adapter header: Samtec `TSM-110-04-L-DV-A`.

Use 7.47 mm as the nominal PCB-to-PCB stack-height target for enclosure modeling. Samtec's official HLE/TSM characterization report explicitly uses the same `HLE -02` and `TSM -04` lead styles at 7.47 mm, but its test articles are 30-position parts. The exact 10-position `-A` pair remains subject to official CAD/series-print review and physical measurement.

Use Jauch `LP603443JU` as the V1 battery fit-check candidate. Its official catalog cell envelope is 6.0 mm × 34.5 mm × 45.0 mm at 3.7 V and 850 mAh. This is not the complete enclosure allowance: the configured protection board, wire exit, connector, strain relief, padding, and pouch swelling must be added from the delivery drawing and sample.

Retain Panasonic `10TPF150ML` only as the existing 7.3 mm × 4.3 mm × 2.8 mm RGB-bulk geometry reference because Panasonic marks it NRFND. Evaluate `10TAE150ML` as the same-envelope replacement candidate. `10TVE150ML` remains a comparison only because Panasonic's current North American TV-series page is marked discontinued.

## Drivers

- The earlier calculated TSW/SSW stack was approximately 11.05 mm and consumed unnecessary internal height.
- The Samtec HLE/TSM combination has manufacturer evidence for a 7.47 mm stack using the selected lead styles.
- A named battery envelope is required to evaluate whether the 100 mm square PCB, adapter, USB, antenna, and battery can coexist.
- The enclosure must not be frozen around a capacitor MPN that the manufacturer no longer recommends for a new design.

## Constraints

- `Fit-check candidate locked` does not mean `production/order locked`.
- The exact 10-position connector models, alignment-pin holes, footprints, tolerance stack, current rating, retention, insertion cycles, assembly side, and regional availability remain open.
- Both MCU adapters must use the same semantic connector interface, but XIAO pin mapping remains adapter-specific.
- XIAO USB-C, ESP32 U.FL/coax/external antenna, nRF onboard antenna keep-out, reset/boot/debug access, and maximum assembled Z require official CAD plus purchased-board measurements.
- The battery may not be clamped, pierced by screws, bent around a sharp edge, placed against a hot part, or used without verified polarity and charger compatibility.
- The capacitor replacement still requires approved land pattern, polarity, ESR, inrush, USB-droop, and RGB-transient tests.

## Rejected alternatives

- Keep the TSW/SSW pair: mechanically simple, but its approximately 11.05 mm stack conflicts with the lower enclosure target.
- Treat 7.47 mm as guaranteed for every HLE/TSM suffix: the official report does not cover the exact 10-position `-A` pair.
- Choose a generic “850 mAh pouch” by nominal dimensions: it omits protection-board, lead, connector, swelling, and delivery-drawing differences.
- Continue using `10TPF150ML` as the procurement preference: its NRFND status makes it unsuitable for a new-design order lock.
- Use `10TVE150ML` as the replacement without review: the current official series page is discontinued.

## Consequences

- The enclosure and adapter models may use a 7.47 mm nominal connector stack and the Jauch cell body as controlled fit-check inputs.
- The lower connector stack recovers approximately 3.58 mm relative to the earlier 11.05 mm calculated TSW/SSW stack before tolerances and seating differences.
- Modeling the complete battery–adapter–connector–main-PCB–plate stack increases the generated case body from the earlier control-surface-only 17.0 mm placeholder to 33.17 mm before controls.
- PCB fabrication remains blocked until the exact connector CAD/footprints and sample stack are checked.
- Battery-backed enclosure release remains blocked until a configured pack delivery drawing and physical sample establish the complete protected-pack envelope.
- `10TAE150ML` becomes the capacitor replacement candidate, while `10TPF150ML` and `10TVE150ML` are excluded from order lock.
