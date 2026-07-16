# ADR-0005: Replace the tall radial RGB reservoir with a low-profile SMD candidate

Status: superseded in MPN by ADR-0013; low-profile geometry decision remains accepted
Date: 2026-07-16

## Decision

Replace the provisional 470 uF, 8 mm × 11.5 mm radial capacitor with a D3L low-profile 150 uF geometry. This ADR originally named Panasonic `10TPF150ML`; ADR-0013 retains it only as an NRFND geometry reference and promotes `10TAE150ML` to the replacement fit-check candidate. Keep the aggregate RGB budget near 120 mA, add a 10 uF X7R local LED-rail capacitor, and add a separate 10 uF X7R local 3.3 V capacitor.

## Drivers

- The radial component protruded above the planned PCB-to-plate clearance and forced unnecessary enclosure height.
- Panasonic's official model table lists `10TPF150ML` as 150 uF, 10 V, and 7.3 mm × 4.3 mm × 2.8 mm.
- The hardware current limiter and firmware frame clamp reduce the need to assume a 470 uF reservoir before transient measurements exist.

## Constraints

- The selected capacitor is polarized; polarity must be visible in the schematic, footprint, assembly drawing, and inspection checklist.
- The draft EIA-7343-31 footprint is not asserted to be Panasonic's approved land pattern.
- Capacitance, ESR, inrush, USB droop, and all-LED switching remain bench-test requirements.

## Rejected alternatives

- Keep the radial 470 uF part: avoidable 11.5 mm height and poor enclosure fit.
- Remove the bulk capacitor entirely: transient behavior has not been measured.
- Increase the enclosure height around C30: solves the symptom while preserving an unverified electrical assumption.

## Consequences

- The PCB control-side height target for C30 drops from 11.5 mm to approximately 2.8 mm for the candidate body.
- The enclosure fit-check can keep a sub-5 mm PCB-to-plate component gap at C30.
- Fabrication remains blocked until the exact Panasonic drawing, land pattern, sourcing, and transient behavior are reviewed.
