from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from bridge.agent_deck_bridge.cli import main
from bridge.agent_deck_bridge.config import load_config
from bridge.agent_deck_bridge.core import SessionObservation
from bridge.agent_deck_bridge.integrations import ActionExecution, FixtureAdapter
from bridge.agent_deck_bridge.protocol import (
    AckPayload,
    AckStatus,
    ActionCode,
    ActionIntentPayload,
    ActionResultPayload,
    ActionResultStatus,
    Envelope,
    EnvelopeFlag,
    EventEdge,
    GestureClass,
    HeartbeatPayload,
    HelloPayload,
    ImplementationId,
    KeyEventPayload,
    MessageType,
    StateSnapshotPayload,
)
from bridge.agent_deck_bridge.runtime import BridgeRuntime


class MutableClock:
    def __init__(self, value=0.0):
        self.value = value

    def __call__(self):
        return self.value


class RecordingPTTBackend:
    def __init__(self):
        self.starts = []
        self.stops = []

    def start(self, session):
        self.starts.append(session.session_id)
        return ActionExecution(ActionResultStatus.SUCCEEDED, "started")

    def stop(self, session, reason):
        self.stops.append((session.session_id, reason))
        return ActionExecution(ActionResultStatus.SUCCEEDED, "stopped")


class StaticAdapter:
    def __init__(self, name, observations=None, error=None):
        self.name = name
        self.observations = observations or []
        self.error = error

    def discover(self):
        if self.error:
            raise self.error
        return self.observations

    def execute(self, session, action):
        return ActionExecution(ActionResultStatus.SUCCEEDED, "ok", 7)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.clock = MutableClock()
        self.ptt = RecordingPTTBackend()
        self.adapter = StaticAdapter(
            "fixture",
            [
                SessionObservation(
                    "fixture",
                    "alpha",
                    "Alpha",
                    "waiting_approval",
                    frozenset(
                        {
                            ActionCode.APPROVE,
                            ActionCode.PUSH_TO_TALK,
                        }
                    ),
                )
            ],
        )
        self.runtime = BridgeRuntime(
            load_config(),
            [self.adapter],
            ptt_backend=self.ptt,
            clock=self.clock,
        )
        self.runtime.poll()
        self.hello, self.brightness, self.snapshot = self.runtime.connect(
            epoch=0x11223344
        )

    def test_connect_emits_hello_and_complete_twelve_led_snapshot(self):
        hello = self.hello.decoded_payload()
        self.assertIsInstance(hello, HelloPayload)
        self.assertEqual(hello.implementation_id, ImplementationId.BRIDGE)
        snapshot = self.snapshot.decoded_payload()
        self.assertIsInstance(snapshot, StateSnapshotPayload)
        self.assertEqual(snapshot.epoch, 0x11223344)
        self.assertEqual(len(snapshot.leds), 12)
        self.assertEqual(
            snapshot.selected_session_id,
            self.runtime.registry.selected_session_id,
        )
        brightness = self.brightness.decoded_payload()
        self.assertEqual(brightness.brightness_percent, 20)
        self.assertEqual(brightness.current_limit_ma, 300)

    def test_hello_heartbeat_and_malformed_payload_are_acknowledged_safely(self):
        hello = Envelope.from_payload(
            MessageType.HELLO,
            1,
            HelloPayload(ImplementationId.NRF52840, 0, 56, 7, 99),
            request_id=1,
        )
        response = self.runtime.handle(hello)
        self.assertEqual(response.message_type, MessageType.HELLO_ACK)
        heartbeat = Envelope.from_payload(
            MessageType.HEARTBEAT,
            2,
            HeartbeatPayload(100),
            request_id=2,
        )
        ack = self.runtime.handle(heartbeat)
        self.assertEqual(ack.decoded_payload().status, AckStatus.OK)
        malformed = Envelope(
            MessageType.ACTION_INTENT, 3, request_id=3, payload=b"\x00"
        )
        rejected = self.runtime.handle(malformed)
        self.assertEqual(rejected.message_type, MessageType.ACK)
        self.assertEqual(rejected.decoded_payload().status, AckStatus.MALFORMED)

    def test_action_intent_is_state_checked_and_request_id_idempotent(self):
        session = self.runtime.registry.selected()
        payload = ActionIntentPayload(
            0x11223344,
            session.session_id,
            session.state_version,
            ActionCode.APPROVE,
            GestureClass.LONG,
            1000,
        )
        first = self.runtime.handle(
            Envelope.from_payload(
                MessageType.ACTION_INTENT,
                1,
                payload,
                request_id=0x2468,
                flags=EnvelopeFlag.ACK_REQUIRED,
            )
        )
        second = self.runtime.handle(
            Envelope.from_payload(
                MessageType.ACTION_INTENT,
                2,
                payload,
                request_id=0x2468,
                flags=EnvelopeFlag.ACK_REQUIRED,
            )
        )
        self.assertEqual(
            first.decoded_payload().status, ActionResultStatus.SUCCEEDED
        )
        self.assertEqual(first.decoded_payload(), second.decoded_payload())

    def test_duplicate_sequence_is_rejected_before_dispatch(self):
        heartbeat = Envelope.from_payload(
            MessageType.HEARTBEAT, 8, HeartbeatPayload(1)
        )
        self.runtime.handle(heartbeat)
        duplicate = self.runtime.handle(heartbeat)
        self.assertEqual(duplicate.message_type, MessageType.ACK)
        self.assertEqual(duplicate.decoded_payload().status, AckStatus.STALE)

    def test_ptt_release_timeout_and_heartbeat_loss_stop_capture(self):
        press = Envelope.from_payload(
            MessageType.KEY_EVENT,
            1,
            KeyEventPayload(11, EventEdge.PRESS, 0),
            request_id=1,
        )
        release = Envelope.from_payload(
            MessageType.KEY_EVENT,
            2,
            KeyEventPayload(11, EventEdge.RELEASE, 250),
            request_id=2,
        )
        self.runtime.handle(press)
        self.runtime.handle(release)
        self.assertEqual(self.ptt.stops[-1][1], "release")

        self.runtime.handle(
            Envelope.from_payload(
                MessageType.KEY_EVENT,
                3,
                KeyEventPayload(11, EventEdge.PRESS, 0),
                request_id=3,
            )
        )
        self.clock.value = 61
        self.runtime.tick()
        self.assertFalse(self.runtime.connected)
        self.assertIn(
            self.ptt.stops[-1][1],
            {"max_hold_timeout", "heartbeat_expired"},
        )

    def test_poll_stops_ptt_when_selected_session_disappears(self):
        self.runtime.handle(
            Envelope.from_payload(
                MessageType.KEY_EVENT,
                1,
                KeyEventPayload(11, EventEdge.PRESS, 0),
                request_id=1,
            )
        )
        self.assertIsNotNone(self.runtime.ptt.active)

        self.adapter.observations = []
        self.runtime.poll()

        self.assertIsNone(self.runtime.registry.selected())
        self.assertIsNone(self.runtime.ptt.active)
        self.assertEqual(self.ptt.stops[-1][1], "selection_changed")

    def test_ptt_release_is_honored_after_capability_is_removed(self):
        self.runtime.handle(
            Envelope.from_payload(
                MessageType.KEY_EVENT,
                1,
                KeyEventPayload(11, EventEdge.PRESS, 0),
                request_id=1,
            )
        )
        self.runtime.registry.refresh(
            "fixture",
            [
                SessionObservation(
                    "fixture",
                    "alpha",
                    "Alpha",
                    "waiting_approval",
                    frozenset({ActionCode.APPROVE}),
                )
            ],
            now=self.clock(),
        )

        response = self.runtime.handle(
            Envelope.from_payload(
                MessageType.KEY_EVENT,
                2,
                KeyEventPayload(11, EventEdge.RELEASE, 250),
                request_id=2,
            )
        )

        self.assertEqual(
            response.decoded_payload().status, ActionResultStatus.SUCCEEDED
        )
        self.assertIsNone(self.runtime.ptt.active)
        self.assertEqual(self.ptt.stops[-1][1], "release")

    def test_poll_stops_ptt_when_capability_is_removed(self):
        self.runtime.handle(
            Envelope.from_payload(
                MessageType.KEY_EVENT,
                1,
                KeyEventPayload(11, EventEdge.PRESS, 0),
                request_id=1,
            )
        )
        self.adapter.observations = [
            SessionObservation(
                "fixture",
                "alpha",
                "Alpha",
                "waiting_approval",
                frozenset({ActionCode.APPROVE}),
            )
        ]

        self.runtime.poll()

        self.assertIsNone(self.runtime.ptt.active)
        self.assertEqual(self.ptt.stops[-1][1], "ptt_capability_changed")

    def test_adapter_failure_does_not_crash_other_adapters(self):
        good = StaticAdapter(
            "good",
            [SessionObservation("good", "ok", "Good", "running")],
        )
        bad = StaticAdapter("bad", error=RuntimeError("parse failed"))
        runtime = BridgeRuntime(load_config(), [bad, good], clock=self.clock)
        sessions = runtime.poll()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0].integration, "good")


class CliTests(unittest.TestCase):
    def test_config_check_decode_discover_and_snapshot(self):
        config = Path(__file__).parents[1] / "config.example.yaml"
        output = io.StringIO()
        with redirect_stdout(output):
            result = main(["--config", str(config), "config-check"])
        self.assertEqual(result, 0)
        self.assertTrue(json.loads(output.getvalue())["valid"])

        heartbeat_hex = "010300043412000004030201"
        output = io.StringIO()
        with redirect_stdout(output):
            result = main(["decode", heartbeat_hex])
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output.getvalue())["type"], "heartbeat")

        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "sessions.json"
            fixture.write_text(
                json.dumps(
                    {
                        "sessions": [
                            {
                                "id": "alpha",
                                "label": "Alpha",
                                "state": "running",
                                "actions": ["interrupt"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            output = io.StringIO()
            with redirect_stdout(output):
                result = main(
                    [
                        "--config",
                        str(config),
                        "discover",
                        "--fixture",
                        str(fixture),
                    ]
                )
            self.assertEqual(result, 0)
            self.assertEqual(json.loads(output.getvalue())[0]["state"], "running")

            output = io.StringIO()
            with redirect_stdout(output):
                result = main(
                    [
                        "--config",
                        str(config),
                        "snapshot",
                        "--fixture",
                        str(fixture),
                    ]
                )
            self.assertEqual(result, 0)
            envelope = Envelope.decode(bytes.fromhex(output.getvalue().strip()))
            self.assertEqual(envelope.message_type, MessageType.STATE_SNAPSHOT)

    def test_decode_error_returns_nonzero_without_traceback(self):
        error = io.StringIO()
        with redirect_stderr(error):
            result = main(["decode", "not-hex"])
        self.assertEqual(result, 2)
        self.assertIn("decode error", error.getvalue())


if __name__ == "__main__":
    unittest.main()
