# Agent Deck V1 product requirements and delivery plan

Status: planning baseline with host implementation in progress
Date: 2026-07-16  
Owner: repository maintainers

## Outcome

Build and evaluate a PCB-mounted physical AI-agent controller that can control Codex, Hermes, OMX, and tmux sessions through USB or BLE and display normalized agent state using individually addressable RGB lighting on all 12 MX keys. V1 must compare XIAO ESP32-S3 Plus and XIAO nRF52840 Plus without treating the boards as pin-compatible.

## Success criteria

V1 is complete when one common input PCB can be operated through either MCU-specific adapter, all required inputs and RGB outputs pass the bench tests, USB and BLE paths exchange the same semantic protocol, dangerous actions are guarded by host state, and measured evidence is sufficient to select one MCU for the next revision.

## Requirements summary

### Product experience

- Twelve mechanical MX keys, each capable of independent RGB status indication, plus encoder click and navigation center inputs.
- One detented rotary encoder with push switch.
- One five-direction digital navigation switch.
- One circular capacitive touch area supporting tap, long press, and double tap in firmware.
- No OLED or LCD.
- Inputs and LEDs mounted directly to the main input PCB and mechanically supported by the plate or enclosure.
- Physical controls for session selection, new task, approve, reject, interrupt, run tests, open diff, reasoning level, and push-to-talk.
- K11, immediately right of the circular touch control, uses a 2u keycap and defaults to hold-to-talk while remaining one hot-swap MX matrix position and one RGB channel.
- Destructive actions require long press, double confirmation, or another explicit state-aware guard.

### Hardware

- Approximately 1.5 mm switch plate above a 1.6 mm input PCB; final thicknesses depend on the selected switch family and socket geometry.
- Hot-swap sockets and one diode per key.
- Replaceable XIAO ESP32-S3 Plus and XIAO nRF52840 Plus through separate adapter boards.
- USB-first bring-up, followed by protected single-cell Li-Po evaluation.
- Twelve addressable RGB LEDs with level translation, local decoupling, bulk capacitance, aggregate firmware brightness limiting, and a bounded power rail.
- External capacitive-touch controller for a common circuit across both MCUs.
- No duplicate charger on the common input PCB while using XIAO onboard charging.

### Firmware and host

- USB HID keyboard support where practical.
- USB Vendor HID for bidirectional messages; CDC is optional diagnostics only.
- BLE HID plus a custom GATT service on nRF52840; ESP32-S3 may also evaluate BLE and Wi-Fi WebSocket transports.
- A shared logical input/event/state layer with platform adapters for ESP-IDF and Zephyr/nRF Connect SDK.
- A PC bridge that normalizes `idle`, `running`, `waiting_approval`, `waiting_input`, `completed`, and `failed` states.
- Transport-independent message semantics with versioning, sequence numbers, acknowledgements for commands, and explicit capability discovery.

## V1 architecture decision

Use a common input PCB plus two MCU-specific adapter boards.

The direct XIAO socket alternative is rejected for V1 because the similarly positioned D pins do not guarantee identical ADC, NFC, JTAG, battery, USB, boot, or power behavior. An adapter boundary keeps the input PCB stable, gives each board a dedicated battery and USB treatment, and makes later MCU replacement possible without rerouting every input.

See:

- `docs/architecture/system-architecture.md`
- `docs/hardware/pin-compatibility.md`
- `docs/decisions/0001-common-input-pcb-and-mcu-adapters.md`

## Proposed electrical partition

- MCP23017 at 3.3 V scans the 4×4 key matrix and reads the five navigation contacts plus the capacitive-touch output.
- Encoder A, B, and click connect directly to the MCU adapter.
- AT42QT1010-class controller converts the circular copper electrode to a digital touch signal.
- Twelve SK6812 Mini-E-compatible LEDs use one 5 V limited rail, one serial data GPIO through a 74AHCT1G125-class buffer, a 330 ohm first-LED series resistor, 100 nF per LED, and input bulk capacitance.
- Common adapter signals use semantic names: `I2C_SDA`, `I2C_SCL`, `IOX_INT`, `ENC_A`, `ENC_B`, `ENC_SW`, `RGB_DATA`, `RGB_PWR_EN`, optional UART, `3V3`, `VBUS_5V`, and ground.
- V1 exposes the selected XIAO board's onboard USB-C connector. External USB-C routing is deferred until both boards' USB pads and ESD/impedance requirements are separately reviewed.

## Open decisions before fabrication release

- Promote the selected MX switch, Kailh socket, Gateron 2u stabilizer, and keycaps from fit-check candidates to order lock.
- Verify the selected RKJXM navigation switch land pattern, force/travel, cap attachment, and support with a sample.
- Verify the selected EC11 encoder suffix, shaft/knob engagement, mounting height, and actuation support with a sample.
- Touch electrode diameter, overlay material, thickness, and sensitivity capacitor.
- RGB package/footprint, optical path, maximum firmware brightness, and battery behavior.
- Promote the HLE/TSM fit-check pair after exact-suffix CAD, mating-height, retention, and current review.
- Complete the configured Jauch battery pack envelope, connector, protection, retention, current target, and battery-mode RGB decision.
- Host platform support order and production transport/action backends.
- BLE bonding policy, USB report IDs, and Wi-Fi provisioning scope.

The complete checklist is `docs/hardware/design-inputs-checklist.md`.

## Delivery stages

### 1. Firmware and transport spikes

- Build minimal input, RGB, USB HID, Vendor HID, BLE HID, custom GATT, and reconnect experiments on each development board.
- Confirm the proposed common pin set against real boards, including boot, reset, deep sleep, battery read, and USB enumeration.
- Record current consumption with radios and LEDs in representative states.

Exit: both boards can exchange a protocol ping and one input/state round trip through at least USB, and the nRF52840 can do the same through BLE.

### 2. Schematic

- Select exact switch, encoder, navigation, touch, RGB, connector, protection, and power components.
- Create hierarchical schematics for input matrix, controls, RGB/power, common connector, and each adapter.
- Complete ERC and peer review against manufacturer schematics and data sheets.

Exit: zero unexplained ERC errors and every connector signal has a documented owner, voltage, direction, reset state, and adapter mapping.

### 3. PCB

- Place all user inputs and RGB devices on the common 1.6 mm PCB.
- Route two small adapter PCBs while protecting RF keep-outs, USB access, and battery routing.
- Run DRC, inspect return paths and current loops, and export fabrication files only after 3D interference review.

Exit: zero unexplained DRC errors and signed-off fabrication/assembly outputs for all three boards.

### 4. Plate

- Generate the plate from locked PCB coordinates.
- Ensure switch retention, encoder/joystick support, and acceptable keycap clearances.
- Produce a low-cost test plate before final material selection.

Exit: all controls actuate without plate binding and repeated actuation load is not carried only by solder pads.

### 5. Enclosure

- Provide USB-C, reset/boot access, antenna keep-out, battery retention, and service access.
- Validate the case with board and component 3D models.

Exit: the assembled stack closes without interference and cables can be inserted without stressing the adapter.

### 6. Assembly

- Inspect bare boards, verify shorts and rails, populate power sections first, then logic, LEDs, sockets, controls, and adapters.
- Use current-limited bench power for first power-on.

Exit: all rails and quiescent currents are within the calculated envelope before either XIAO is inserted.

### 7. Integrated test

- Execute `.omx/plans/test-spec-agent-deck-v1.md` for both MCUs.
- Record results in a revisioned test report, including failures and measurement setup.

Exit: sufficient passing evidence and known defects to make an MCU selection decision.

### 8. MCU selection

Score both variants on BLE reconnect, USB behavior, battery life estimate, firmware complexity, host status transport, thermal/current behavior, and failure recovery.

Exit: an ADR selects the V2 MCU or explicitly authorizes another measurement round.

## Acceptance criteria

- Exactly 12 key positions enumerate uniquely and no matrix ghost is observed in the defined multi-key test set.
- All 12 RGB positions can be addressed independently; a firmware current budget prevents unrestricted full-white output.
- Encoder direction, detents, and click are reported without observable edge loss in the specified manual and automated tests.
- All five navigation directions are distinguishable; unsupported simultaneous directions are rejected deterministically.
- Touch tap, long press, and double tap are recognized using documented timing thresholds; swipe is not claimed with a single electrode.
- The same logical message types operate over USB Vendor HID and BLE GATT without host business logic depending on the physical transport.
- USB HID and BLE HID never produce an unguarded destructive action from a single ambiguous input.
- Both adapters survive boot, reset, reconnect, and 30-minute active operation without rail faults or unexplained resets.
- Battery measurements record active, idle, radio-connected, and LED state current; no battery-life claim is made without those measurements.
- KiCad ERC/DRC and the applicable test-spec checks pass or have reviewed, documented waivers.
- Repository documentation contains no assertion about unpublished OpenAI Micro internals.

## Risks and mitigations

- Pin-map similarity hides board-specific functions. Mitigation: semantic adapter connector, reserved D16, official schematic review, and hardware spikes.
- Addressable LED current dominates battery life. Mitigation: switched rail, hardware current limit, global firmware current budget, and event-driven lighting.
- I2C scanning adds key latency or sleep complexity. Mitigation: 400 kHz evaluation, direct encoder wiring, interrupt-assisted slow controls, and an explicit remove-MCP option for V2.
- Touch sensitivity shifts with enclosure material and grounding. Mitigation: test coupons, adjustable sensitivity component, guard/keep-out study, and final overlay testing.
- USB and battery power paths back-feed. Mitigation: keep charging on adapters, review both XIAO schematics, and test every insertion/power combination with current limiting.
- Host integrations rely on unstable CLI output. Mitigation: adapter-based parsers, capability/version checks, fixtures, and graceful `unknown` state.
- Dangerous actions are mapped too directly. Mitigation: semantic action intents, session/state validation, acknowledgement, and explicit confirmation policy.

## Verification

The primary proof is the measured test matrix in `.omx/plans/test-spec-agent-deck-v1.md`. Document review alone cannot approve pin compatibility, RF performance, USB behavior, battery life, or touch sensitivity.

## Stop condition

The repository baseline is complete when this PRD, the test specification, pin compatibility note, architecture, BOM, protocol, fit-check parts, and design-input checklist agree. Host-only firmware and bridge work may proceed before hardware, but fabrication and physical transport claims remain blocked until exact board revisions and first-stage bench evidence are recorded.
