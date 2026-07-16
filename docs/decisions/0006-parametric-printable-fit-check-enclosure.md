# ADR-0006: Build a parametric printable enclosure fit-check before mechanical freeze

Status: accepted for V1 prototype planning  
Date: 2026-07-16

## Decision

Create a three-piece, script-generated enclosure consisting of a bottom PCB tray, top perimeter bezel, and replaceable 1.5 mm MX plate. Derive all control and mounting coordinates from the current common PCB, export manifold STL files, and label the result as a fit-check rather than a production enclosure.

## Drivers

- A physical print reveals PCB, switch, touch, fastener, and connector problems earlier than a cosmetic shell alone.
- A replaceable plate allows the switch family, touch membrane, and control openings to change without discarding the tray.
- Parametric generation keeps PCB and enclosure datums reviewable in source control.
- Lowering C30 to a 2.8 mm candidate body makes a 17 mm enclosure body feasible without a local bulge.

## Constraints

- Exact switch/socket, keycap, encoder, navigation, adapter connector, USB cable, battery, and antenna envelopes are not frozen.
- The broad side opening is a service slot, not a final USB-C port.
- The 0.8 mm touch membrane and 14.2 mm MX cutouts require physical coupons and printer-specific compensation.
- The model assumes plastic plate/bezel material; metal plate RF and touch behavior requires a separate review.

## Rejected alternatives

- Cosmetic monolithic shell first: obscures fit problems and makes every mechanical change a full reprint.
- Final snap fits now: printer/process and assembly tolerances are unknown.
- Add a battery pocket from a guessed cell: would encode an unsafe unselected battery volume.

## Consequences

- Three STL files and machine-readable dimensions are available for a low-cost fit print.
- Enclosure source remains editable without proprietary CAD files.
- Production release remains blocked by the checklist in `mechanical/enclosure/README.md` and the hardware verification specification.
