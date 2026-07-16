from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from bridge.agent_deck_bridge.audit import (
    AuditRecord,
    JsonLineAuditSink,
    MemoryAuditSink,
)
from bridge.agent_deck_bridge.config import load_config
from bridge.agent_deck_bridge.core import (
    SessionObservation,
    SessionRegistry,
)
from bridge.agent_deck_bridge.integrations import ActionExecution
from bridge.agent_deck_bridge.policy import ActionIntent, PolicyEngine
from bridge.agent_deck_bridge.protocol import (
    ActionCode,
    ActionResultStatus,
    GestureClass,
)
from bridge.agent_deck_bridge.ptt import PTTController


class MutableClock:
    def __init__(self, value=0.0):
        self.value = value

    def __call__(self):
        return self.value


class AuditSinkTests(unittest.TestCase):
    def test_json_lines_are_structured_and_omit_null_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            sink = JsonLineAuditSink(path)
            sink.record(
                AuditRecord(
                    event="intent_result",
                    outcome="rejected",
                    request_id=7,
                    action="delete",
                    detail="second confirmation required",
                )
            )
            record = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(record["request_id"], 7)
            self.assertEqual(record["action"], "delete")
            self.assertIn("timestamp", record)
            self.assertNotIn("session_id", record)


def registry_with_session(state="waiting_approval", actions=None):
    actions = actions or {
        ActionCode.APPROVE,
        ActionCode.REJECT,
        ActionCode.INTERRUPT,
        ActionCode.PUSH,
        ActionCode.DEPLOY,
        ActionCode.DELETE,
        ActionCode.NEW_TASK,
        ActionCode.RUN_TESTS,
        ActionCode.OPEN_DIFF,
        ActionCode.SET_REASONING_LEVEL,
        ActionCode.PUSH_TO_TALK,
    }
    registry = SessionRegistry(epoch=1)
    registry.refresh(
        "fixture",
        [
            SessionObservation(
                "fixture", "alpha", "Alpha", state, frozenset(actions)
            )
        ],
    )
    session = registry.sessions[0]
    registry.select(session.session_id)
    return registry, session


class PolicyEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = MutableClock()
        self.registry, self.session = registry_with_session()
        self.audit = MemoryAuditSink()
        self.engine = PolicyEngine(
            self.registry,
            load_config().safety_rules,
            audit=self.audit,
            clock=self.clock,
        )
        self.engine.reset_connection(0x11223344)
        self.executions = 0

    def execute(self, session, action):
        self.executions += 1
        return ActionExecution(ActionResultStatus.SUCCEEDED, "ok", 9)

    def intent(self, **overrides):
        values = {
            "epoch": 0x11223344,
            "session_id": self.session.session_id,
            "state_version": self.session.state_version,
            "request_id": 10,
            "action": ActionCode.APPROVE,
            "gesture": GestureClass.LONG,
            "hold_ms": 1000,
        }
        values.update(overrides)
        return ActionIntent(**values)

    def test_valid_action_executes_once_and_duplicate_returns_cached_result(self) -> None:
        intent = self.intent()
        first = self.engine.handle(intent, self.execute)
        second = self.engine.handle(intent, self.execute)
        self.assertEqual(first, second)
        self.assertEqual(first.status, ActionResultStatus.SUCCEEDED)
        self.assertEqual(self.executions, 1)
        self.assertTrue(any(item.event == "intent_duplicate" for item in self.audit.records))

    def test_request_id_collision_stale_epoch_session_version_and_gesture_reject(self) -> None:
        original = self.intent()
        self.engine.handle(original, self.execute)
        cases = [
            self.intent(action=ActionCode.REJECT),
            self.intent(request_id=11, epoch=9),
            self.intent(request_id=12, session_id=999),
            self.intent(request_id=13, state_version=999),
            self.intent(request_id=14, gesture=GestureClass.SHORT),
            self.intent(request_id=15, hold_ms=1),
        ]
        for intent in cases:
            with self.subTest(intent=intent):
                result = self.engine.handle(intent, self.execute)
                self.assertEqual(result.status, ActionResultStatus.REJECTED)
        self.assertEqual(self.executions, 1)

    def test_state_requirement_and_supported_action_are_enforced(self) -> None:
        registry, session = registry_with_session(
            state="idle", actions={ActionCode.APPROVE}
        )
        engine = PolicyEngine(registry, load_config().safety_rules)
        engine.reset_connection(7)
        wrong_state = ActionIntent(
            7,
            session.session_id,
            session.state_version,
            1,
            ActionCode.APPROVE,
            GestureClass.LONG,
            1000,
        )
        self.assertEqual(
            engine.handle(wrong_state, self.execute).status,
            ActionResultStatus.REJECTED,
        )
        unsupported = ActionIntent(
            7,
            session.session_id,
            session.state_version,
            2,
            ActionCode.DELETE,
            GestureClass.CHORD,
            1000,
        )
        self.assertEqual(
            engine.handle(unsupported, self.execute).status,
            ActionResultStatus.UNSUPPORTED,
        )

    def test_reviewed_ordinary_action_rule_executes(self) -> None:
        result = self.engine.handle(
            self.intent(
                request_id=16,
                action=ActionCode.RUN_TESTS,
                gesture=GestureClass.SHORT,
                hold_ms=0,
            ),
            self.execute,
        )
        self.assertEqual(result.status, ActionResultStatus.SUCCEEDED)
        self.assertEqual(self.executions, 1)

    def test_second_confirmation_requires_a_distinct_request_before_timeout(self) -> None:
        first = self.intent(
            request_id=20,
            action=ActionCode.DELETE,
            gesture=GestureClass.CHORD,
        )
        pending = self.engine.handle(first, self.execute)
        duplicate = self.engine.handle(first, self.execute)
        self.assertEqual(
            pending.status, ActionResultStatus.CONFIRMATION_REQUIRED
        )
        self.assertEqual(duplicate, pending)
        second = self.intent(
            request_id=21,
            action=ActionCode.DELETE,
            gesture=GestureClass.CHORD,
        )
        accepted = self.engine.handle(second, self.execute)
        self.assertEqual(accepted.status, ActionResultStatus.SUCCEEDED)
        self.assertEqual(self.executions, 1)

        third = self.intent(
            request_id=22,
            action=ActionCode.PUSH,
            gesture=GestureClass.CHORD,
        )
        self.engine.handle(third, self.execute)
        self.clock.value = 6
        expired = self.engine.handle(
            self.intent(
                request_id=23,
                action=ActionCode.PUSH,
                gesture=GestureClass.CHORD,
            ),
            self.execute,
        )
        self.assertEqual(
            expired.status, ActionResultStatus.CONFIRMATION_REQUIRED
        )
        self.assertEqual(self.executions, 1)

    def test_selection_or_connection_reset_cancels_confirmation(self) -> None:
        self.engine.handle(
            self.intent(
                request_id=30,
                action=ActionCode.DEPLOY,
                gesture=GestureClass.CHORD,
            ),
            self.execute,
        )
        self.engine.cancel_pending("selection_changed")
        result = self.engine.handle(
            self.intent(
                request_id=31,
                action=ActionCode.DEPLOY,
                gesture=GestureClass.CHORD,
            ),
            self.execute,
        )
        self.assertEqual(
            result.status, ActionResultStatus.CONFIRMATION_REQUIRED
        )
        self.engine.reset_connection(99)
        stale = self.engine.handle(
            self.intent(request_id=32), self.execute
        )
        self.assertEqual(stale.status, ActionResultStatus.REJECTED)

    def test_adapter_exception_is_failed_and_cached(self) -> None:
        calls = 0

        def explode(session, action):
            nonlocal calls
            calls += 1
            raise RuntimeError("secret internal failure")

        first = self.engine.handle(self.intent(request_id=40), explode)
        second = self.engine.handle(self.intent(request_id=40), explode)
        self.assertEqual(first.status, ActionResultStatus.FAILED)
        self.assertEqual(second, first)
        self.assertEqual(calls, 1)
        self.assertNotIn("secret internal failure", first.detail)


class FakePTTBackend:
    def __init__(self):
        self.starts = []
        self.stops = []

    def start(self, session):
        self.starts.append(session.session_id)
        return ActionExecution(ActionResultStatus.SUCCEEDED, "capture started")

    def stop(self, session, reason):
        self.stops.append((session.session_id, reason))
        return ActionExecution(ActionResultStatus.SUCCEEDED, "capture stopped")


class PTTControllerTests(unittest.TestCase):
    def setUp(self):
        self.clock = MutableClock()
        self.backend = FakePTTBackend()
        self.registry, self.session = registry_with_session()
        self.ptt = PTTController(
            self.backend, max_hold_ms=1000, clock=self.clock
        )

    def test_press_release_timeout_and_disconnect_are_fail_closed(self) -> None:
        self.assertEqual(
            self.ptt.press(self.session).status, ActionResultStatus.SUCCEEDED
        )
        self.ptt.press(self.session)
        self.assertEqual(self.backend.starts, [self.session.session_id])
        self.ptt.release()
        self.assertIsNone(self.ptt.active)
        self.assertEqual(self.backend.stops[-1][1], "release")

        self.ptt.press(self.session)
        self.clock.value = 1.1
        self.ptt.tick()
        self.assertIsNone(self.ptt.active)
        self.assertEqual(self.backend.stops[-1][1], "max_hold_timeout")

        self.ptt.press(self.session)
        self.ptt.disconnect()
        self.assertIsNone(self.ptt.active)
        self.assertEqual(self.backend.stops[-1][1], "transport_disconnect")

    def test_stop_failure_still_clears_active_state(self) -> None:
        class BrokenStop(FakePTTBackend):
            def stop(self, session, reason):
                raise RuntimeError("broken")

        controller = PTTController(BrokenStop(), max_hold_ms=1000)
        controller.press(self.session)
        result = controller.disconnect()
        self.assertIsNone(controller.active)
        self.assertEqual(result.status, ActionResultStatus.FAILED)


if __name__ == "__main__":
    unittest.main()
