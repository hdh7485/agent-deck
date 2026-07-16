# Agent Deck V1 verification specification

Status: provisional, executable after exact parts are selected  
Date: 2026-07-16

## Evidence format

Each test run records hardware revision, adapter revision, MCU board revision, firmware commit, bridge commit, host OS, instruments, supply voltage/current limit, test steps, raw observations, result, and linked logs or photos. A pass without this metadata is not release evidence.

## Test matrix

Every applicable test runs once with XIAO ESP32-S3 Plus and once with XIAO nRF52840 Plus. USB tests run on both. BLE tests run on both when supported by the selected stack. ESP32-S3 Wi-Fi tests are comparative and do not become a V1 product requirement automatically.

## A. Static hardware review

- A01: Cross-check every XIAO pad and adapter net against the exact official schematic revision.
- A02: Confirm D16 remains dedicated to the board battery-sense path.
- A03: Confirm ESP32-S3 strapping pins are not externally forced to invalid reset levels.
- A04: Confirm nRF52840 NFC pins are either unused or explicitly configured as GPIO.
- A05: Verify USB, antenna, switch, encoder, navigation switch, and battery mechanical clearances from 3D models.
- A06: KiCad ERC and DRC report zero unexplained errors.
- A07: Verify diode direction, hot-swap socket orientation, RGB pin 1, IC orientation, and connector keying from fabrication outputs.

## B. Power safety

- B01: With no MCU installed, apply current-limited 5 V and verify 5 V, switched RGB rail, and 3.3 V expectations.
- B02: Exercise USB-only, battery-only, USB-plus-battery, unpowered host, and disconnected battery cases; observe no reverse current outside component limits.
- B03: Toggle `RGB_PWR_EN` and verify the LED rail reaches its off target and powers up without resetting the MCU.
- B04: Command worst-case RGB output, verify hardware current limiting, then verify normal firmware clamps output to the declared budget.
- B05: Measure sleep, idle connected, active input, BLE connected, Wi-Fi connected where applicable, and representative 12-LED state currents.
- B06: Run 30 minutes active and 2 hours idle without unexplained reset, over-temperature, or rail drift.
- B07: Verify battery voltage read against a calibrated meter at at least three cell voltages; follow each board's documented enable sequence.

## C. Inputs

- C01: Each of 12 keys produces only its assigned key ID across 100 actuations.
- C02: Defined two-key and three-key combinations show no ghost input; diode orientation is verified if any failure occurs.
- C03: A rapid 10-second key test does not leave a logically stuck key after release.
- C04: Rotate the encoder 200 detents in each direction at normal speed and 50 detents rapidly; compare reported delta to physical count.
- C05: Press the encoder 100 times without false rotation exceeding the documented tolerance.
- C06: Each navigation contact produces the correct event across 100 actuations; simultaneous contacts follow the documented rejection/priority rule.
- C07: Touch tap, long press, and double tap each reach at least 95% recognition in a 20-trial scripted human test after calibration.
- C08: Touch does not self-trigger during representative RGB switching, USB traffic, enclosure contact, or charger connection tests.
- C09: K11 press starts one host-side push-to-talk session, release stops it, and lost transport/heartbeat also stops it without leaving capture active.

## D. RGB

- D01: Address each of 12 LEDs independently with red, green, blue, and off, and confirm the physical key-to-index map.
- D02: Verify logical agent states map to the documented palette and selected-agent indication.
- D03: Disconnect/reconnect transport while LEDs are active; stale state expires to a safe disconnected pattern.
- D04: Verify brightness limit persists across reboot and cannot exceed the firmware current budget.
- D05: Command all 12 LEDs simultaneously at maximum requested white and verify the transmitted frame is scaled or clamped to the declared aggregate current budget before the hardware limiter intervenes.

## E. USB and BLE

- E01: USB HID keyboard enumerates with stable report descriptors and sends a non-destructive test key.
- E02: Vendor HID capability request and protocol ping complete after cold boot and reset.
- E03: Composite USB reconnects after 20 unplug/replug cycles without manual reflashing.
- E04: BLE HID bonds, disconnects, and reconnects after host sleep and device reset.
- E05: Custom GATT state update and input event round-trip without duplicate sequence acceptance.
- E06: Transport loss causes no buffered destructive action to execute after reconnection.
- E07: If USB and BLE are both connected, the ownership policy prevents duplicate host actions.

## F. Protocol and bridge

- F01: Firmware and bridge golden vectors encode and decode every message type identically.
- F02: Unknown version, unknown message type, oversized length, invalid enum, stale sequence, and malformed payload are rejected safely.
- F03: The bridge maps fixture inputs to all six normalized agent states plus `unknown/disconnected` behavior.
- F04: Session selection remains stable while the tmux list changes and rejects a stale session identifier.
- F05: Restarting the bridge causes capability renegotiation and a full state resync.
- F06: Codex, Hermes, OMX, and tmux integrations are isolated adapters; one parser failure does not crash the transport loop.

## G. Dangerous actions

- G01: Approve succeeds only while the selected session is in `waiting_approval` and the configured confirmation gesture completes.
- G02: Reject succeeds only in a compatible pending state.
- G03: Interrupt targets the selected running session and requires an acknowledgement or explicit timeout state.
- G04: Push, deploy, and delete cannot be bound to an unconfirmed short press.
- G05: A session change between button-down and confirmation cancels the pending action.
- G06: Device reset, bridge reset, duplicate packet, and reconnect do not replay a dangerous action.

## H. Mechanical endurance smoke tests

- H01: Plate and enclosure support encoder and navigation switch actuation without visible PCB pad flex.
- H02: Perform 500 actuations each on the encoder click, navigation center, and one representative key; inspect solder joints and mounting tabs.
- H03: USB cable insertion/removal does not lift or twist the adapter beyond the enclosure support allowance.
- H04: Battery and antenna remain retained after normal handling and enclosure reassembly.

## MCU selection scorecard

Record measured values and score 1–5 for:

- BLE reconnect success and latency
- USB enumeration/recovery
- Active and idle current
- Estimated battery life from measured duty cycle
- Protocol/transport implementation complexity
- Debugging and update recovery
- Wi-Fi value versus power cost
- Host bridge complexity
- Available GPIO headroom and adapter complexity
- Observed faults over the complete test matrix

Do not select the final MCU from advertised specifications alone.
