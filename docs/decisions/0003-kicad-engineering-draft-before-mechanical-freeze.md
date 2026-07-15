# ADR-0003: Keep the first KiCad revision as a placement and netlist engineering draft

Status: accepted for V1 prototype planning  
Date: 2026-07-16

## Decision

Create the common input PCB and both XIAO adapter projects now, but stop before release routing. The draft fixes the functional circuit, semantic connector, footprint candidates, board envelope, and control placement. Long traces remain unrouted until the switch/socket, five-way navigation part, adapter connector stack, touch overlay, plate, and enclosure datums are locked.

## Drivers

- A real KiCad model exposes footprint, keep-out, power, and connector problems earlier than prose alone.
- Routing around provisional mechanical parts would create false confidence and expensive rework.
- The two XIAO candidates must remain isolated behind identical semantic connectors without asserting pin compatibility.
- A rendered board is useful for layout review even when it is explicitly marked not fabrication-ready.

## Rejected alternatives

- Automatically complete long routing before mechanical freeze: the first experiment produced genuine crossings and was removed.
- Suppress all DRC findings: this would hide the reverse-mount LED cutout and under-key courtyard decisions that still need review.
- Copy a product teardown or unpublished design: outside the independent functional-design boundary.

## Consequences

- The repository has reviewable KiCad source and images now.
- ERC can validate the block schematics, while DRC records the exact open routing and footprint-review debt.
- Gerber generation and board ordering remain blocked until the mechanical checklist and final routing gates pass.
