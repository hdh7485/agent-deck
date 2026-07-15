# Agent Deck device protocol v1 draft

## Goals

- Carry the same semantic messages over USB Vendor HID, BLE GATT, and optional Wi-Fi WebSocket.
- Keep USB reports bounded to 64 bytes.
- Recover cleanly from disconnects and process restarts.
- Prevent duplicated or stale sensitive actions.
- Allow firmware and bridge versions to negotiate capabilities.

USB HID keyboard reports are separate from this control protocol. CDC logs are diagnostics only.

## Envelope

The transport-independent v1 envelope is 8 bytes plus up to 56 payload bytes:

| Byte | Field | Meaning |
| --- | --- | --- |
| 0 | `major` | Breaking protocol version; v1 is `1` |
| 1 | `type` | Message type ID |
| 2 | `flags` | `ACK_REQUIRED`, `RESPONSE`, `ERROR`, reserved bits |
| 3 | `length` | Payload length, 0–56 |
| 4–5 | `sequence` | Little-endian sender sequence, wraps modulo 65536 |
| 6–7 | `request_id` | Correlates commands and results; zero for unsolicited state |
| 8–63 | `payload` | Message-specific fixed fields or compact TLV fields |

USB uses fixed 64-byte reports with zero padding. BLE uses the exact `8 + length` bytes in GATT characteristics. WebSocket uses one binary message per envelope. Transport security and integrity are not replaced by this header.

## Lifecycle

1. Transport connects.
2. Each side sends `HELLO` with implementation ID, protocol minor, capability bits, maximum payload, and a random connection epoch.
3. The bridge sends a complete `STATE_SNAPSHOT`.
4. Both sides exchange `HEARTBEAT` while idle.
5. Disconnect or heartbeat expiry cancels pending confirmations and action requests.

Sequence numbers are checked within one connection epoch. A new epoch invalidates all pending request IDs.

## Message types

| ID | Name | Direction | Purpose |
| --- | --- | --- | --- |
| `0x01` | `HELLO` | Both | Version, capabilities, connection epoch |
| `0x02` | `HELLO_ACK` | Both | Negotiated features or rejection reason |
| `0x03` | `HEARTBEAT` | Both | Liveness and monotonic uptime |
| `0x04` | `ACK` | Both | Generic receipt/reject status |
| `0x10` | `STATE_SNAPSHOT` | PC → device | Complete current device-visible state |
| `0x11` | `SET_AGENT_STATE` | PC → device | Update one agent/session state |
| `0x12` | `SET_SELECTED_AGENT` | PC → device | Selected stable session ID |
| `0x13` | `SET_LED` | PC → device | Explicit LED override with expiry |
| `0x14` | `SET_BRIGHTNESS` | PC → device | Global brightness/current policy |
| `0x15` | `SET_MODE` | PC → device | Named interaction/display mode |
| `0x16` | `ACTION_RESULT` | PC → device | Result of a semantic action request |
| `0x17` | `SET_BATTERY_DISPLAY_MODE` | PC → device | Battery indication policy |
| `0x20` | `KEY_EVENT` | Device → PC | Key ID, press/release, duration, modifiers |
| `0x21` | `ENCODER_DELTA` | Device → PC | Signed delta and acceleration class |
| `0x22` | `ENCODER_CLICK` | Device → PC | Press/release and duration |
| `0x23` | `JOYSTICK_EVENT` | Device → PC | Direction/center press/release |
| `0x24` | `TOUCH_EVENT` | Device → PC | Tap, double tap, long press, raw press/release |
| `0x25` | `DEVICE_STATUS` | Device → PC | Firmware, adapter, transport, fault flags |
| `0x26` | `BATTERY_LEVEL` | Device → PC | Millivolts, percent estimate, charge flags |
| `0x27` | `ACTION_INTENT` | Device → PC | Guarded semantic action for a stable session |

## Stable identifiers and state versions

The bridge assigns a 32-bit `session_id` valid for its current runtime epoch and a monotonically increasing 32-bit `state_version`. Device display updates carry both. Sensitive `ACTION_INTENT` payloads include:

- bridge connection epoch
- selected `session_id`
- last displayed `state_version`
- action code
- gesture class (`short`, `long`, `double`, `chord`)
- measured hold duration where applicable

The bridge rejects the intent if the epoch, session, or state version is stale. A visual selection alone is not authorization.

## Normalized states

| Code | Name | Default display meaning |
| --- | --- | --- |
| 0 | `idle` | Available, no active work |
| 1 | `running` | Work in progress |
| 2 | `waiting_approval` | Explicit approval decision required |
| 3 | `waiting_input` | User content/input required |
| 4 | `completed` | Last work completed |
| 5 | `failed` | Work failed or integration error |
| 6 | `disconnected` | Bridge heartbeat lost; device-local state |

Color values are configurable. State codes are stable protocol semantics; specific colors are not.

## Sensitive action policy

- `approve`, `reject`, `interrupt`, `push`, `deploy`, and `delete` are sent as `ACTION_INTENT`, never as raw Enter.
- The bridge owns the required session state and confirmation rule.
- Every accepted intent produces one terminal `ACTION_RESULT` or times out visibly.
- Duplicate `request_id` in the same epoch returns the previous result without executing twice.
- A reconnect never replays a pending sensitive action.

## Capability examples

- USB keyboard HID
- USB Vendor HID
- BLE HID
- custom BLE GATT
- Wi-Fi WebSocket
- battery measurement
- 13 independently addressable RGB key LEDs
- touch gestures
- firmware update mechanism

Capability bits are additive within a major protocol version. Unknown bits are ignored; missing required capabilities cause a clear negotiation failure.

## Golden-vector requirement

Before either implementation is considered compatible, firmware and bridge tests must share byte-for-byte golden vectors for every message, boundary length, malformed packet, duplicate sequence, stale epoch, and unknown enum case.
