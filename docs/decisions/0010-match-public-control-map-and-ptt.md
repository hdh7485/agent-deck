# ADR-0010: Match the observable control map and retain push-to-talk

Status: accepted for V1 fit-check
Date: 2026-07-16

## Decision

Use twelve MX hot-swap key positions and twelve addressable RGB LEDs. Arrange the visible controls as an encoder, two 1u keys, and a round five-way navigation control on the top row; two rows of four 1u keys; then a circular touch control, one 2u push-to-talk key (`K11`), and one 1u auxiliary key (`K12`) on the bottom row.

The encoder click and navigation-center click remain separate inputs, so removing the extra top-row MX position does not remove either click action. This is an independent implementation of an observable exterior control map. It does not claim or copy unpublished Codex Micro circuitry, dimensions, switch construction, firmware, or protocol.

## Evidence and drivers

- Public Codex Micro product imagery reproduced by The Verge visibly shows two keycaps between the upper-left encoder and upper-right round control, not three.
- The same imagery shows a wide microphone-labelled key immediately right of the circular touch control.
- Axios independently reports push-to-talk as a configurable key function.
- Preserving the earlier thirteen-key count placed an extra MX key where the round navigation control belongs and produced the wrong user-facing layout.

## Constraints

- V1 has no onboard microphone. `K11` controls a host-side audio path through the bridge.
- All twelve key switches use the same bottom-mounted Kailh hot-swap socket candidate, including the single switch under the 2u keycap.
- The exact 2u keycap and stabilizer are not selected. Stabilizer holes and plate cutouts must come from the selected manufacturer's drawing and remain a fabrication blocker.
- The navigation footprint remains an electrical placeholder until the selected part's official land pattern is transcribed and checked.
- Transport loss, heartbeat expiry, reset, bridge restart, or maximum-hold timeout must end capture even if the PTT release event is lost.

## Rejected alternatives

- Keep thirteen MX keys by retaining three top-row keycaps: conflicts with the observable encoder–two-key–navigation grouping.
- Hide the thirteenth key elsewhere: adds a control unsupported by the intended exterior map and complicates the square layout.
- Keep a 1u PTT key with only a software mapping: preserves function but weakens the prominent hold-to-talk affordance.
- Add an onboard microphone: expands power, privacy, acoustic, USB/BLE audio, and enclosure scope beyond the requested controller.

## Consequences

- The key matrix uses twelve of sixteen positions; `K11` remains `ROW3/COL1` and `K12` uses `ROW3/COL3`.
- The serial RGB chain ends at `LED12`; the common MCU interface and `RGB_DATA` GPIO requirement do not change.
- The PCB, switch plate, enclosure renders, protocol documentation, firmware contract, bridge policy, and tests share the same twelve-key control map.
- GPIO pressure decreases slightly; no extra MCU GPIO is required because the MCP23017 still scans the key matrix and navigation contacts.
- The fit-check plate retains only the centered MX opening beneath `K11` until the stabilizer is selected; it is not a fabrication release.
