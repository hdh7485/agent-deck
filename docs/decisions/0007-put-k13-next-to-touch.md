# ADR-0007: Put K13 immediately beside the touch control

Status: superseded in part by ADR-0010
Date: 2026-07-16

## Decision

Move K13 from the provisional lower-right position to the position immediately right of the circular touch control. Use a 22 mm touch-to-key center pitch, reduce the case touch recess from 22 mm to 18 mm, and map K13 to matrix position `ROW3/COL1`.

This is an independent layout decision for the intended user experience. Public exterior references may inform the control grouping, but no unpublished OpenAI Micro dimensions, circuitry, or protocol are assumed or copied.

## Drivers

- The previous lower-right K13 coordinate left an unintended blank control position beside the touch surface.
- A 22 mm center pitch preserves the intended grouping while keeping the bottom-mounted socket lands outside the 11.5 mm touch quiet zone.
- An 18 mm recess leaves a nominal 5.9 mm plate ligament to the 14.2 mm MX opening and a 4.4 mm visible gap to the 17.2 mm keycap proxy.

## Constraints

- The PCB touch electrode remains the current 14 mm candidate; only the enclosure recess changes.
- Touch sensitivity through the 0.8 mm membrane and the effect of the adjacent switch, LED, ground, and hand position require physical coupon testing.
- K13's diode, LED, decoupling capacitor, data trace, and matrix mapping must move together.
- C30 moves away from K13's new footprint but remains on the same LED supply rail.

## Rejected alternatives

- Keep K13 at the lower right: preserves an accidental gap and weakens the intended touch-plus-key control cluster.
- Preserve the grid's 19 mm pitch: leaves insufficient margin between the touch quiet zone and the hot-swap socket copper.
- Guess a product-specific pitch from exterior imagery: public images are insufficient mechanical evidence.

## Consequences

- The PCB, LED chain, switch plate, enclosure renders, and firmware matrix map use one consistent K13 location.
- The lower-right case area becomes available for the navigation/adapter region rather than an isolated key.
- Fabrication remains blocked until touch and plate coupons confirm the nominal ligament and sensing margin.
