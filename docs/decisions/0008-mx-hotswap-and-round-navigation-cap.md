# ADR-0008: Use MX hot-swap keys and a low round navigation cap

Status: superseded in count and placement by ADR-0010; part-family decision remains accepted
Date: 2026-07-16

## Decision

Lock the V1 key family to 5-pin MX-compatible mechanical switches, use one bottom-mounted Kailh `CPG151101S11-16` hot-swap socket per key, and reduce the printable switch plate to 1.5 mm nominal thickness. Keep the exact MX switch force/sound MPN open until samples are tested.

Use ALPS Alpine `RKJXM1015004` as the current through-hole navigation-switch candidate and model a separate 14 mm low round concave cap. The cap follows the desired public exterior language; the internal part and dimensions remain an independent candidate, not a claim about OpenAI Micro internals.

## Drivers

- Switch replacement should not require desoldering.
- A plate-mounted MX stack supports repeated switch insertion and normal key actuation better than sockets alone.
- The newer Kailh socket drawing specifies a 1.85 mm body below the PCB. The later full internal-stack tray provides 15.12 mm nominal floor clearance; physical switch/socket and adapter-stack samples still determine the release value.
- The public exterior reference uses a low round thumb control rather than a square navigation button.
- The RKJXM candidate provides through-hole retention, center push, and separate cardinal contacts while staying close to the intended cap envelope.

## Constraints

- The socket is not compatible with Choc switches; no universal overlapping footprint is permitted in V1.
- K13 uses the same socket orientation as the other keys; its 22 mm center pitch keeps socket copper outside the adjacent touch quiet zone.
- The exact switch, keycap, socket revision, paste aperture, plate latch tolerance, and insertion force require physical samples.
- The RKJXM land pattern remains an explicit electrical placeholder until every official terminal and support hole is transcribed and independently checked.
- Diagonal stick motion is represented as simultaneous cardinal contacts and must be handled deterministically in firmware.

## Rejected alternatives

- Solder switches directly: makes switch-force comparison and replacement unnecessarily destructive.
- Universal MX/Choc footprint: increases mechanical and routing risk without a selected Choc product requirement.
- Square five-way cap: meets electrical needs but misses the requested low round thumb-control experience.
- Assume the public reference's internal joystick part: exterior images do not disclose the internal component.

## Consequences

- The PCB generator now owns a centered MX/Kailh socket footprint, so PCB and case key centers share one datum.
- All 13 keys are mechanically replaceable after the socket and plate pass sample validation.
- The enclosure renderer and dimensions expose the round navigation cap, socket height, and floor clearance.
- Fabrication remains blocked by the open land-pattern, sample-fit, and DRC gates.
