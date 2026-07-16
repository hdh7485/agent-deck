from __future__ import annotations

import json
from pathlib import Path
import unittest

from bridge.agent_deck_bridge.protocol import (
    AckPayload,
    AckStatus,
    ActionCode,
    ActionIntentPayload,
    ActionResultPayload,
    ActionResultStatus,
    AdapterCode,
    BatteryDisplayMode,
    BatteryLevelPayload,
    DeviceStatusPayload,
    EncoderClickPayload,
    EncoderDeltaPayload,
    Envelope,
    EnvelopeError,
    EnvelopeFlag,
    EventEdge,
    GestureClass,
    HeartbeatPayload,
    HelloAckPayload,
    HelloPayload,
    ImplementationId,
    JoystickDirection,
    JoystickEventPayload,
    KeyEventPayload,
    MessageType,
    ModeCode,
    NormalizedState,
    PayloadError,
    SequenceError,
    SequenceTracker,
    SetAgentStatePayload,
    SetBatteryDisplayModePayload,
    SetBrightnessPayload,
    SetLedPayload,
    SetModePayload,
    SetSelectedAgentPayload,
    StateSnapshotPayload,
    TouchEventPayload,
    TouchGesture,
    TransportCode,
    decode_payload,
)


FIXTURE = Path(__file__).parent / "fixtures" / "protocol_v1_golden.json"


class ProtocolGoldenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.golden = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def samples(self):
        return {
            "hello": (
                MessageType.HELLO,
                0x1234,
                0,
                EnvelopeFlag.NONE,
                HelloPayload(
                    ImplementationId.BRIDGE, 0, 56, 0x01020304, 0x11223344
                ),
            ),
            "hello_ack": (
                MessageType.HELLO_ACK,
                0x1235,
                0,
                EnvelopeFlag.NONE,
                HelloAckPayload(AckStatus.OK, 0, 56, 0x01000001, 0x55667788),
            ),
            "heartbeat": (
                MessageType.HEARTBEAT,
                0x1234,
                0,
                EnvelopeFlag.NONE,
                HeartbeatPayload(0x01020304),
            ),
            "ack": (
                MessageType.ACK,
                0x1237,
                0,
                EnvelopeFlag.NONE,
                AckPayload(MessageType.ACTION_INTENT, AckStatus.STALE, 4),
            ),
            "state_snapshot": (
                MessageType.STATE_SNAPSHOT,
                0x1238,
                0,
                EnvelopeFlag.NONE,
                StateSnapshotPayload(
                    0x11223344,
                    7,
                    9,
                    20,
                    ModeCode.DEFAULT,
                    BatteryDisplayMode.ON_CHANGE,
                    ((0x20, 0x20, 0x20), (0x2D, 0x7F, 0xF9)),
                ),
            ),
            "set_agent_state": (
                MessageType.SET_AGENT_STATE,
                0x1239,
                0,
                EnvelopeFlag.NONE,
                SetAgentStatePayload(7, 9, NormalizedState.RUNNING),
            ),
            "set_selected_agent": (
                MessageType.SET_SELECTED_AGENT,
                0x123A,
                0,
                EnvelopeFlag.NONE,
                SetSelectedAgentPayload(7, 9),
            ),
            "set_led": (
                MessageType.SET_LED,
                0x123B,
                0,
                EnvelopeFlag.NONE,
                SetLedPayload(3, 0x11, 0x22, 0x33, 1500),
            ),
            "set_brightness": (
                MessageType.SET_BRIGHTNESS,
                0x123C,
                0,
                EnvelopeFlag.NONE,
                SetBrightnessPayload(20, 300),
            ),
            "set_mode": (
                MessageType.SET_MODE,
                0x123D,
                0,
                EnvelopeFlag.NONE,
                SetModePayload(ModeCode.SESSION_SELECT),
            ),
            "action_result": (
                MessageType.ACTION_RESULT,
                0x123E,
                0x2468,
                EnvelopeFlag.NONE,
                ActionResultPayload(
                    ActionCode.APPROVE, ActionResultStatus.SUCCEEDED, 0
                ),
            ),
            "set_battery_display_mode": (
                MessageType.SET_BATTERY_DISPLAY_MODE,
                0x123F,
                0,
                EnvelopeFlag.NONE,
                SetBatteryDisplayModePayload(BatteryDisplayMode.ON_CHANGE),
            ),
            "key_event": (
                MessageType.KEY_EVENT,
                0x1240,
                0,
                EnvelopeFlag.NONE,
                KeyEventPayload(11, EventEdge.PRESS, 1000, 1),
            ),
            "encoder_delta": (
                MessageType.ENCODER_DELTA,
                0x1241,
                0,
                EnvelopeFlag.NONE,
                EncoderDeltaPayload(-3, 2),
            ),
            "encoder_click": (
                MessageType.ENCODER_CLICK,
                0x1242,
                0,
                EnvelopeFlag.NONE,
                EncoderClickPayload(EventEdge.RELEASE, 250),
            ),
            "joystick_event": (
                MessageType.JOYSTICK_EVENT,
                0x1243,
                0,
                EnvelopeFlag.NONE,
                JoystickEventPayload(
                    JoystickDirection.LEFT, EventEdge.PRESS, 75
                ),
            ),
            "touch_event": (
                MessageType.TOUCH_EVENT,
                0x1244,
                0,
                EnvelopeFlag.NONE,
                TouchEventPayload(TouchGesture.DOUBLE_TAP, 320),
            ),
            "device_status": (
                MessageType.DEVICE_STATUS,
                0x1245,
                0,
                EnvelopeFlag.NONE,
                DeviceStatusPayload(
                    1,
                    2,
                    AdapterCode.NRF52840,
                    TransportCode.BLE_GATT,
                    0x01020304,
                ),
            ),
            "battery_level": (
                MessageType.BATTERY_LEVEL,
                0x1246,
                0,
                EnvelopeFlag.NONE,
                BatteryLevelPayload(3890, 73, 3),
            ),
            "action_intent": (
                MessageType.ACTION_INTENT,
                0x1235,
                0x2468,
                EnvelopeFlag.ACK_REQUIRED,
                ActionIntentPayload(
                    0x11223344,
                    0x55667788,
                    9,
                    ActionCode.APPROVE,
                    GestureClass.LONG,
                    1000,
                ),
            ),
        }

    def test_every_message_type_has_a_byte_exact_golden_vector(self) -> None:
        samples = self.samples()
        self.assertEqual(set(samples), set(self.golden))
        self.assertEqual(
            {message_type for message_type, *_ in samples.values()},
            set(MessageType),
        )
        for name, (
            message_type,
            sequence,
            request_id,
            flags,
            payload,
        ) in samples.items():
            with self.subTest(name=name):
                envelope = Envelope.from_payload(
                    message_type,
                    sequence,
                    payload,
                    request_id=request_id,
                    flags=flags,
                )
                expected = bytes.fromhex(self.golden[name])
                self.assertEqual(envelope.encode(), expected)
                decoded = Envelope.decode(expected)
                self.assertEqual(decoded, envelope)
                self.assertEqual(decoded.decoded_payload(), payload)

    def test_firmware_cross_check_vectors_are_locked(self) -> None:
        self.assertEqual(
            self.golden["heartbeat"], "010300043412000004030201"
        )
        self.assertEqual(
            self.golden["action_intent"],
            "01270110351268244433221188776655090000000102e803",
        )

    def test_hid_report_padding_round_trips_and_must_be_zero(self) -> None:
        envelope = Envelope.from_payload(
            MessageType.HEARTBEAT, 1, HeartbeatPayload(9)
        )
        report = envelope.encode(hid_report=True)
        self.assertEqual(len(report), 64)
        self.assertEqual(Envelope.decode(report), envelope)
        corrupted = report[:-1] + b"\x01"
        with self.assertRaises(EnvelopeError):
            Envelope.decode(corrupted)

    def test_payload_boundary_and_malformed_envelopes(self) -> None:
        boundary = Envelope(MessageType.HEARTBEAT, 1, payload=bytes(56))
        self.assertEqual(len(boundary.encode()), 64)
        with self.assertRaises(EnvelopeError):
            Envelope(MessageType.HEARTBEAT, 1, payload=bytes(57)).encode()
        with self.assertRaises(EnvelopeError):
            Envelope.decode(b"\x01\x03")
        with self.assertRaises(EnvelopeError):
            Envelope.decode(bytes.fromhex("0203000000000000"))
        with self.assertRaises(EnvelopeError):
            Envelope.decode(bytes.fromhex("01ff000000000000"))
        with self.assertRaises(EnvelopeError):
            Envelope.decode(bytes.fromhex("0103800000000000"))
        with self.assertRaises(EnvelopeError):
            Envelope.decode(bytes.fromhex("010300040000000000"))

    def test_invalid_enum_and_length_are_rejected(self) -> None:
        with self.assertRaises(PayloadError):
            decode_payload(MessageType.SET_MODE, b"\xff")
        with self.assertRaises(PayloadError):
            decode_payload(MessageType.ACTION_INTENT, bytes(15))
        with self.assertRaises(PayloadError):
            decode_payload(
                MessageType.STATE_SNAPSHOT,
                bytes.fromhex("00000000000000000000000000000001"),
            )


class SequenceTrackerTests(unittest.TestCase):
    def test_duplicate_stale_wrap_and_epoch_reset(self) -> None:
        tracker = SequenceTracker()
        tracker.accept(1, 0xFFFE)
        tracker.accept(1, 0xFFFF)
        tracker.accept(1, 0)
        with self.assertRaises(SequenceError):
            tracker.accept(1, 0)
        with self.assertRaises(SequenceError):
            tracker.accept(1, 0xFFFF)
        tracker.accept(2, 7)


if __name__ == "__main__":
    unittest.main()
