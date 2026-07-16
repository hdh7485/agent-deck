# Firmware architecture

V1 targets ESP-IDF on XIAO ESP32-S3 Plus and Zephyr/nRF Connect SDK on XIAO nRF52840 Plus. The domain behavior is shared; hardware and transport mechanics remain platform-specific.

## Proposed tree

```text
firmware/
  common/
    include/agent_deck/
    input/
    gestures/
    protocol/
    state/
    rgb/
    safety/
    tests/
  ports/
    esp32s3/
    nrf52840/
  boards/
    xiao_esp32s3_plus_adapter/
    xiao_nrf52840_plus_adapter/
  tools/
```

Directories are created when the selected build systems are bootstrapped; this document avoids committing empty generated projects before SDK versions are chosen.

## Common interfaces

- `clock`: monotonic milliseconds and deadlines.
- `input_bus`: MCP23017 register access and interrupt notification.
- `encoder`: timestamped raw A/B/click samples from direct GPIO.
- `rgb_sink`: bounded frame submission and power enable.
- `battery`: millivolt/charge status with board-specific validity flags.
- `transport`: connect, send envelope, receive envelope, MTU/capabilities.
- `storage`: validated small configuration records.
- `system`: reset reason, adapter identity, firmware/build identity.

The common layer must not include ESP GPIO numbers, Nordic pin names, RTOS task handles, or transport-specific connection objects.

## Shared modules

- Matrix scanner and debounce state machine.
- Navigation/contact debounce and simultaneous-input policy.
- Quadrature transition-table decoder.
- Touch gesture timing from one digital touch signal.
- Device-protocol encode/decode and sequence/epoch handling.
- Agent-state cache, selected-session state, heartbeat expiry.
- RGB state renderer with global power/current budget.
- Sensitive-action gesture classifier; authorization remains on the PC.

## Default K11 push-to-talk behavior

- Matrix position K11 is the default hold-to-talk control. It remains a normal debounced MX input and does not add a microphone or audio path to the device.
- Firmware emits both K11 press and release `KEY_EVENT` records. It does not synthesize a keyboard shortcut or decide which host application records audio.
- Reboot, transport loss, or heartbeat expiry clears the local pressed state; the bridge independently stops any active capture on the same failures.
- The default binding is configurable at the bridge, but the physical 2u keycap and microphone legend make the shipped V1 intent explicit.

## Platform responsibilities

### ESP32-S3 port

- ESP-IDF GPIO, I2C, timers, NVS, TinyUSB, BLE, optional Wi-Fi/WebSocket, and OTA spike.
- Native USB composite descriptors without taking GPIO19/20 for unrelated use.
- Wi-Fi is an optional transport and must not leak into the common state machine.

### nRF52840 port

- Zephyr GPIO, I2C, timers, settings, USB device stack, BLE HID/custom GATT, and DFU spike.
- NFC-pin configuration only if D14/D15 are ever used; baseline V1 leaves them out of the common interface.
- Low-power and reconnect measurements are part of the MCU selection evidence.

## Board definitions

Each adapter board definition declares semantic pins from `docs/hardware/pin-compatibility.md`, active levels, available battery sensing, transport capabilities, and service interfaces. Compile-time checks should fail if a required semantic pin is missing or assigned to D16.

## Test strategy

- Host-native unit tests for protocol, debounce, gestures, state expiry, and LED budget.
- Platform tests with fake I2C/input sources before hardware.
- On-device loopback for protocol and transport reconnect.
- Hardware-in-the-loop tests aligned with `.omx/plans/test-spec-agent-deck-v1.md`.

SDK versions and exact build commands remain a blocking decision; do not generate both projects until supported releases and CI host requirements are selected.
