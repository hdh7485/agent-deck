# ADR-0011: Unify the keycap finish and spacing

Status: accepted for V1 fit-check
Date: 2026-07-16

## Decision

Render all twelve keycaps with one blank black-smoke translucent material and remove the microphone pictogram from K11. Keep K11's `push_to_talk` meaning in bridge configuration and documentation rather than encoding it as permanent keycap artwork.

Place all keycap centers on a 19.0 mm lattice. Use 17.2 mm for the 1u render envelope and 36.2 mm for the 2u render envelope, producing a nominal 1.8 mm key-to-key gap in both axes. Center K11 at the midpoint of its two grid units and move the bottom row onto the same 19 mm vertical pitch as the other rows.

## Drivers

- One finish makes the control surface read as a coherent status instrument while still allowing the per-key RGB to show through.
- Blank caps avoid locking configurable agent actions to permanent artwork.
- The previous bottom row used a 24 mm vertical pitch, and K11 was offset 0.5 mm from the two-unit grid center, producing visibly uneven gaps.
- A single lattice makes PCB, plate, keycap, and enclosure collision checks easier to audit.

## Constraints

- Black-smoke translucency is a visual and optical intent, not a qualified resin, keycap process, or transmission percentage.
- Exact keycap wall thickness, diffuser behavior, RGB brightness, legends, and supplier parts require physical samples.
- K11 remains one centered MX switch under a 2u keycap; stabilizer geometry remains blocked on the selected manufacturer's drawing.
- The circular touch surface occupies the first bottom-row unit but is not treated as a keycap when calculating the 1.8 mm key-to-key gap.

## Consequences

- Mechanical-local bottom-row centers become touch `(28, 24)`, K11 `(56.5, 24)`, and K12 `(85, 24)`.
- KiCad top-side centers become touch `(38, 104)`, K11 `(66.5, 104)`, and K12 `(95, 104)`.
- The touch-to-K11 center pitch becomes 28.5 mm; the nominal touch-recess-to-MX-cutout ligament is 12.4 mm.
- Firmware, protocol, matrix assignments, LED indices, and the K11 default action do not change.
