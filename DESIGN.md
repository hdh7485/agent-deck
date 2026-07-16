# Agent Deck V1 design contract

## Source of truth

- Status: active V1 fit-check contract.
- Updated: 2026-07-16.
- Evidence reviewed: `AGENTS.md`, the V1 PRD and test specification, ADR-0001 through ADR-0012, KiCad placement sources, enclosure generator, and generated control renders.
- Public OpenAI Micro imagery informs only the desired compact physical-controller experience. Unpublished dimensions, internals, firmware, and protocol are not treated as evidence.

## Brand

Agent Deck is a quiet, compact desktop instrument for supervising AI coding agents. It should feel closer to a small piece of studio equipment than a novelty macro pad: dark, legible through light and touch, and calm when nothing needs attention.

## Product goals, non-goals, and success signals

Goals:

- Make agent selection, navigation, approval, interruption, testing, diff review, and push-to-talk available without leaving the current screen.
- Communicate normalized agent state through twelve individually addressable key LEDs without adding a display.
- Support both ESP32-S3 and nRF52840 experiments from one fixed input surface.
- Fit the V1 control surface on a 100 mm × 100 mm common PCB while retaining standard 19 mm MX spacing.

Non-goals:

- Reproduce an unpublished commercial circuit, protocol, or mechanical dimension.
- Add OLED/LCD UI, a general-purpose touchscreen, or a breadboard-based final input assembly.
- Treat arbitrary keystroke injection as sufficient authorization for destructive host actions.
- Call the current placement/netlist draft fabrication-ready.

Success signals:

- Every control can be identified and operated by position and feel after a short learning period.
- State remains understandable when RGB color perception is limited, using blink/pulse behavior and host feedback in addition to hue.
- The enclosure, plate, and PCB share one coordinate contract and assemble without control, USB, antenna, battery, or component interference.
- USB/BLE reconnect, event deduplication, and state-aware confirmation tests pass on both MCU candidates before MCU selection.

## Personas, jobs, and contexts

- A developer running several Codex, Hermes, OMX, or tmux sessions needs to select a session and see which one is running, waiting, completed, or failed.
- A reviewer needs explicit approve/reject/interrupt controls that are harder to trigger accidentally than a raw Enter key.
- A voice user needs a large bottom-row 2u key that works as hold-to-talk without relying on a printed microphone legend.
- A firmware or hardware engineer needs the same input PCB to compare BLE stability, USB behavior, development effort, and battery life across the two XIAO adapters.
- The main context is a desk beside a keyboard, used in mixed lighting and often without looking directly at the device.

## Information architecture

The physical hierarchy is fixed:

1. Top row: encoder, two 1u keys, and round five-way navigation control.
2. Middle rows: two rows of four 1u action/status keys.
3. Bottom row: circular touch control, 2u push-to-talk key, and one 1u auxiliary key.
4. Host bridge: converts physical events into semantic intents, checks the selected session and state, then returns normalized status to the LED renderer.

The encoder and navigation control own selection and movement. The key grid owns context-dependent actions and state. The touch control is reserved for tap, double-tap, and long-press gestures; it does not imply swipe support with the single-electrode V1 hardware.

## Design principles

- Preserve the 19 mm control lattice; compactness comes from removing dead perimeter, not shrinking the interaction targets.
- Make dangerous actions deliberate through hold, double confirmation, and host-side state checks.
- Use light as ambient status, not as a substitute for labels, tactile structure, or host feedback.
- Keep the surface visually quiet: one square silhouette, blank black-smoke keycaps, no display, and no decorative legends.
- Keep mechanical load out of solder joints by supporting the encoder and navigation control at the plate or bezel.
- Keep common PCB nets semantic; MCU pin differences belong to the adapters.

## Visual language

- Primary form: 100 mm square PCB inside a 107.8 mm square fit-check enclosure with restrained corner radii.
- Finish: graphite/black enclosure and plate, blank black-smoke translucent 1u and 2u keycaps, dark encoder knob, and low round concave navigation cap.
- Spacing: key centers on a 19.0 mm lattice; 17.2 mm 1u and 36.2 mm 2u envelopes provide a nominal 1.8 mm adjacent gap.
- Light: low default brightness, event-driven illumination, and no high-brightness idle animation.
- Typography: board/service markings only; visible keycap legends remain absent in V1.

## Components

- Twelve PCB-mounted MX-compatible switches with Kailh hot-swap socket candidates, one matrix diode and one reverse-mount addressable RGB LED per key.
- One EC11-class rotary encoder with click and metal support tabs.
- One PCB-mounted five-way digital navigation switch with a low, round, concave cap.
- One circular PCB copper touch electrode with an external capacitive-touch controller.
- One 1.5 mm replaceable control plate, one 1.6 mm common input PCB, and one MCU-specific adapter per XIAO candidate.
- The fitted XIAO board's onboard USB-C remains the only V1 USB connector.

## Accessibility

- Encoder, navigation cap, touch recess, 1u keys, and the 2u PTT key must be distinguishable by geometry and location.
- Color is not the sole status channel; firmware must support distinct steady, pulse, and blink patterns and the bridge must expose text status on the host.
- Brightness and animation rate are configurable, including an effectively dark mode.
- All key actions are remappable at the semantic-intent layer.
- Destructive intents require a hold or second confirmation and must be rejected when the selected session state is incompatible.

## Responsive behavior

The physical layout is fixed rather than responsive. Behavior adapts to transport and host context:

- USB and BLE expose the same semantic input abstraction.
- When host status transport is unavailable, the device enters a locally recognizable disconnected state instead of showing stale success.
- ESP32-S3 may add Wi-Fi state transport; nRF52840 uses USB Vendor HID or BLE GATT through the bridge. These transports must produce the same normalized states.
- macOS, Windows, and Linux key bindings live in host profiles; dangerous actions remain semantic and state-aware on every platform.

## Interaction states

- `idle`: selected session is available; LEDs remain dim and stable.
- `running`: active work uses a restrained pulse.
- `waiting_approval`: high-salience pattern; approval controls become eligible only for the matching session.
- `waiting_input`: distinct pattern from approval to avoid accidental confirmation.
- `completed`: bounded success indication that returns to a quiet state.
- `failed`: persistent but brightness-limited error indication until acknowledged or the state changes.
- `disconnected`: device-local pattern that cannot be confused with completed or idle.
- `confirming`: hold/double-confirm progress for destructive semantic intents.

## Content and voice

Host UI and logs use short, literal labels: agent name, session, state, intent, and result. Avoid anthropomorphic or celebratory copy during approvals and failures. Error text states what was rejected and which state or connection is required.

## Implementation constraints

- Common input PCB: 100.0 mm × 100.0 mm; mounting-hole centers form a 90.0 mm square.
- Fit-check plate: 100.8 mm × 100.8 mm × 1.5 mm.
- Fit-check enclosure: 107.8 mm × 107.8 mm × 17.0 mm before controls.
- Twelve MX hot-swap keys and twelve LEDs remain on the 19 mm lattice; K11 is the 2u PTT position.
- Encoder A/B edges connect directly to the MCU. MCP23017 handles the key matrix, five-way inputs, and touch output.
- D16 remains reserved for board-specific battery sensing.
- No OLED/LCD and no second USB-C connector in V1.
- Adapter connector orientation, XIAO USB cable envelope, RF keep-out, battery volume, exact navigation footprint, and 2u stabilizer geometry remain fabrication blockers.

## Open questions

- Which exact MX switch, 1u/2u keycap family, stabilizer, encoder, knob, and navigation part will be sampled and locked?
- Can the relocated common-adapter connector mate without board overhang while preserving USB and antenna clearances?
- What touch overlay material and thickness gives reliable sensing during charging and RGB switching?
- What battery envelope, protection, retention, and power-path design will be used after USB-powered V1 verification?
- Do the reverse-mount LED cutouts need a project-specific footprint/rule waiver or a revised land pattern after manufacturer drawing review?
- Is 100 mm the final product envelope, or can a later revision shrink further after connector, stabilizer, and antenna geometry are frozen?
