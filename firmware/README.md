# Firmware architecture and host-verified core

V1 targets ESP-IDF on XIAO ESP32-S3 Plus and Zephyr/nRF Connect SDK on XIAO nRF52840 Plus. The domain behavior is shared; hardware and transport mechanics remain platform-specific.

The current implementation is a dependency-free C++17 common core. It compiles and runs on the host, but it has not been validated on either MCU yet.

## Tree

```text
firmware/
  boards/
    include/agent_deck/boards/
      xiao_esp32s3_plus.h
      xiao_nrf52840_plus.h
  common/
    include/agent_deck/
      board_definition.h
      debounce.h
      encoder.h
      navigation.h
      platform_port.h
      port_stubs.h
      protocol.h
      protocol_payloads.h
      rgb.h
      safety.h
      sequence.h
      state.h
      touch.h
    src/
  ports/
    esp32s3/
      bench_port_stub.cpp
      README.md
    nrf52840/
      bench_port_stub.cpp
      README.md
  tests/
    golden_vectors.h
    test_main.cpp
  Makefile
```

## Host verification

From `firmware/`:

```sh
make CXX=/usr/bin/clang++ test
make CXX=/usr/bin/clang++ sanitize
make CXX=/usr/bin/clang++ embedded-check
```

All commands compile with C++17, `-Wall -Wextra -Wpedantic -Werror`. The sanitizer target adds AddressSanitizer and UndefinedBehaviorSanitizer. `embedded-check` also disables exceptions and RTTI.

The suite covers:

- compact and fixed 64-byte USB protocol envelopes, malformed frames, flags, bounds, and zero padding
- the bridge-shared HEARTBEAT and ACTION_INTENT byte vectors
- per-epoch sequence acceptance, duplicate/stale rejection, and 16-bit wrap
- 12-key matrix debounce, forced release, and timer wrap
- navigation simultaneous-contact rejection or deterministic priority
- quadrature direction, detent accumulation, inversion, and invalid transitions
- touch raw press/release, delayed tap, double tap, and long press
- bridge heartbeat expiry to `disconnected`
- 12-pixel brightness and aggregate current-budget scaling
- semantic safety gesture classification
- conservative XIAO semantic pin tables and fail-closed port stubs

These tests are host evidence only. They do not prove USB/BLE enumeration, timing under radio traffic, touch sensitivity, current draw, boot behavior, or reconnection on physical boards.

## Port interface direction

The implemented `PlatformPort` currently exposes monotonic time, MCP23017
reads, direct encoder samples, RGB power/data writes, and bounded control-frame
transmission. Battery status, persistent storage, reset/adapter identity, and
richer transport lifecycle hooks are target interfaces for the MCU-backed
ports; they are not present in the current host stub.

The common layer must not include ESP GPIO numbers, Nordic pin names, RTOS task handles, or transport-specific connection objects.

Framework-independent behavior lives in `common/`. Chip pin numbers are confined to `boards/` and are consumed through semantic signals such as `ENC_A` and `RGB_PWR_EN`.

## Implemented shared modules

- Matrix contact debounce state machine.
- Navigation/contact debounce and simultaneous-input policy.
- Quadrature transition-table decoder.
- Touch gesture timing from one digital touch signal.
- Device-protocol encode/decode and sequence/epoch handling.
- Agent-state cache, selected-session state, heartbeat expiry.
- RGB state renderer with global power/current budget.
- Sensitive-action gesture classifier; authorization remains on the PC.

The navigation default rejects simultaneous contacts. A center-then-clockwise priority mode exists for controlled experiments, but changing the product policy requires matching bridge and test updates.

If the RGB budget cannot cover even the configured per-pixel idle allowance, the renderer requests a powered-off rail rather than pretending a valid frame fits.

## Default K11 push-to-talk behavior

- Matrix position K11 is the default hold-to-talk control. It remains a normal debounced MX input and does not add a microphone or audio path to the device.
- Firmware emits both K11 press and release `KEY_EVENT` records. It does not synthesize a keyboard shortcut or decide which host application records audio.
- Reboot, transport loss, or heartbeat expiry clears the local pressed state; the bridge independently stops any active capture on the same failures.
- The default binding is configurable at the bridge. The physical keycap remains blank black-smoke like the other keys; push-to-talk is conveyed by configuration and behavior rather than a printed legend.

## Platform responsibilities

### ESP32-S3 port

- ESP-IDF GPIO, I2C, timers, NVS, TinyUSB, BLE, optional Wi-Fi/WebSocket, and OTA spike.
- Native USB composite descriptors without taking GPIO19/20 for unrelated use.
- Wi-Fi is an optional transport and must not leak into the common state machine.
- `ports/esp32s3/bench_port_stub.cpp` is host-compilable and deliberately returns failure for every hardware operation until a selected ESP-IDF release replaces it.

### nRF52840 port

- Zephyr GPIO, I2C, timers, settings, USB device stack, BLE HID/custom GATT, and DFU spike.
- NFC-pin configuration only if D14/D15 are ever used; baseline V1 leaves them out of the common interface.
- Low-power and reconnect measurements are part of the MCU selection evidence.
- `ports/nrf52840/bench_port_stub.cpp` is host-compilable and deliberately returns failure for every hardware operation until a selected Zephyr/nRF Connect SDK release replaces it.

## Board definitions

Each adapter board definition declares the conservative semantic pins from `docs/hardware/pin-compatibility.md`. Compile-time checks reject duplicate common D-pin assignments and any common use of D16. D16 remains a separate board-specific battery-sense entry.

These definitions are a firmware mapping baseline, not proof of the exact purchased board revision. Recheck them against official drawings before target bring-up.

## Test strategy

- Host-native unit tests for protocol, debounce, gestures, state expiry, LED budget, safety, and board mappings.
- Platform tests with fake I2C/input sources before hardware.
- On-device loopback for protocol and transport reconnect.
- Hardware-in-the-loop tests aligned with `.omx/plans/test-spec-agent-deck-v1.md`.

SDK versions and target build commands remain a blocking decision. The per-port READMEs define the bring-up order without claiming an SDK-backed implementation.
