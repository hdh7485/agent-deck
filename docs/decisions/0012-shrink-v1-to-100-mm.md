# ADR-0012: Shrink the V1 common PCB to 100 mm square

Status: accepted for the V1 fit-check; not a fabrication release
Date: 2026-07-16

## Decision

Reduce the common input PCB from 118 mm × 118 mm to 100 mm × 100 mm. Use a 90 mm square mounting-hole pattern, a 100.8 mm square control plate, and a 107.8 mm × 107.8 mm enclosure body.

Do not scale the controls. Preserve the 19 mm key lattice, 17.2 mm 1u and 36.2 mm 2u keycap envelopes, 12-key matrix, per-key RGB, encoder, round five-way navigation control, and circular touch electrode. The enclosure generator translates the existing control map by `-5 mm` in X and `-2 mm` in Y; the KiCad source uses the equivalent coordinate transform in its inverted Y datum.

Repack the low-profile RGB power components into the back-side top strip and the MCP23017 logic into the bottom strip. Move the provisional common-adapter connector to the back-side top strip to avoid the encoder and rightmost key/LED area. Its physical mating orientation, adapter overhang, USB opening, and RF clearance remain unresolved and block fabrication.

The dimension is an independent prototype choice. It is not inferred from an unpublished OpenAI or Codex Micro internal dimension.

## Drivers

- The 118 mm board contains removable perimeter space around a 77.6 mm × 74.6 mm visible control envelope.
- A 100 mm square retains about 11.2 mm horizontal and 12.7 mm vertical margin around that envelope before enclosure walls.
- PCB area drops from 13,924 mm² to 10,000 mm², a 28.2% reduction, while all interaction targets remain full size.
- A smaller square better matches the intended compact desktop-controller experience and commonly available prototype-panel limits.

## Constraints

- Exact 2u stabilizer, navigation, adapter connector, XIAO, USB cable, battery, and antenna envelopes are not frozen.
- The current PCB is a placement/netlist engineering draft with intentionally open long routes.
- Mounting holes, copper zones, plate openings, case bosses, render proxies, and documentation must use the same 100 mm datum.
- C30 remains the documented 2.8 mm low-profile candidate; shrinking the board must not reintroduce a plate-height bulge.

## Rejected alternatives

- 96 mm square: geometrically possible for the visible controls, but leaves too little provisional margin for the adapter connector, 2u stabilizer, antenna, and first-article tolerance work.
- Uniformly scale the 118 mm design: would break standard MX pitch and reduce target sizes.
- Keep the 118 mm PCB inside a smaller cosmetic shell: cannot reduce the physical enclosure and hides the actual mechanical constraint.
- Freeze a final connector location during this shrink: the XIAO adapter stack and USB/RF envelopes do not yet provide enough evidence.

## Consequences

- The control-surface-only fit-check initially remained 17.0 mm high before controls; ADR-0013 and the full internal-stack model supersede that placeholder with a 33.17 mm body.
- Firmware matrix mapping, LED count, device protocol, and host intent mapping do not change.
- PCB component placement and mechanical exports must be regenerated and revalidated together.
- The later full-stack enclosure models J1/U1, the MCU adapter, XIAO/USB/RF envelopes, and a battery candidate, while physical samples remain required for release.
- A later reduction below 100 mm requires a new decision after physical adapter, stabilizer, navigation, USB, antenna, and battery samples are checked.
