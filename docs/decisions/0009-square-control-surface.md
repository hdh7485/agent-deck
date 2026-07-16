# ADR-0009: Use a square V1 control surface

Status: superseded in control placement by ADR-0010 and in dimensions by ADR-0012
Date: 2026-07-16

## Decision

Change the common input PCB from a 132 mm × 92 mm rectangle to an independent 118 mm × 118 mm square datum. Use a matching 118.8 mm square control plate and a 125.8 mm × 125.8 mm enclosure body. Rebalance the keys and right-side controls inside the new datum while preserving all thirteen MX hot-swap keys, thirteen RGB LEDs, the touch-plus-K13 grouping, encoder, and round navigation cap.

The square silhouette is a user-experience choice informed by public product imagery. It is not a claim about unpublished Codex Micro dimensions, PCB geometry, component placement, or internal construction.

## Drivers

- The requested visual language is a compact square controller rather than a wide macro pad.
- A square PCB, plate, and case keep the mechanical coordinate contract honest; a square cosmetic shell around the previous rectangular PCB would waste internal volume and hide the actual layout constraint.
- The added rear quadrant gives the MCU connector and logic/power parts a distinct region away from repeated control loads.

## Constraints

- The V1 square side length is a prototype choice, not a dimension inferred from photographs.
- Control centers, mounting holes, copper zones, case bosses, plate openings, and render proxies must move together.
- The XIAO USB service opening remains provisional until the adapter connector height and board orientation are physically frozen.
- The navigation land pattern, touch overlay, battery volume, and first-article fit remain fabrication blockers.

## Rejected alternatives

- Square enclosure around the existing 132 mm × 92 mm PCB: produces a square exterior but preserves an unnecessarily wide internal architecture.
- Scale every coordinate uniformly: changes the standard 19 mm MX pitch and invalidates the selected switch/keycap stack.
- Copy dimensions from exterior imagery: photographs do not provide reliable manufacturing dimensions.

## Consequences

- This decision established the first 118 mm square source envelope; ADR-0012 later reduced it to 100 mm without scaling the controls.
- The original enclosure body was 125.8 mm square; ADR-0012 reduced it to 107.8 mm square, and ADR-0013 later superseded the 17.0 mm height placeholder with the complete 33.17 mm internal-stack body.
- Firmware matrix mapping and the shared device protocol do not change.
- Existing rectangular STL files are superseded by regenerated square fit-check exports with the same filenames.
