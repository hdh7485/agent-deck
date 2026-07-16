"""Bridge orchestration without transport-specific side effects."""

from __future__ import annotations

import secrets
import time
from typing import Callable, Iterable

from .audit import AuditRecord, AuditSink, NullAuditSink
from .config import BridgeConfig
from .core import Session, SessionRegistry
from .integrations import (
    ActionExecution,
    IntegrationAdapter,
)
from .led import LedRenderer
from .policy import ActionIntent, PolicyEngine
from .protocol import (
    AckPayload,
    AckStatus,
    ActionCode,
    ActionIntentPayload,
    ActionResultPayload,
    ActionResultStatus,
    Envelope,
    EnvelopeFlag,
    EventEdge,
    HeartbeatPayload,
    HelloAckPayload,
    HelloPayload,
    ImplementationId,
    KeyEventPayload,
    MessageType,
    PayloadError,
    SequenceError,
    SequenceTracker,
    SetBrightnessPayload,
)
from .ptt import PTTBackend, PTTController, UnsupportedPTTBackend


BRIDGE_CAPABILITIES = 1 << 0 | 1 << 1 | 1 << 2


class BridgeRuntime:
    """Coordinate adapters, state, policy, PTT, and protocol responses."""

    def __init__(
        self,
        config: BridgeConfig,
        adapters: Iterable[IntegrationAdapter] = (),
        *,
        audit: AuditSink | None = None,
        ptt_backend: PTTBackend | None = None,
        registry: SessionRegistry | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.config = config
        self.audit = audit or NullAuditSink()
        self.registry = registry or SessionRegistry()
        self.adapters: dict[str, IntegrationAdapter] = {
            adapter.name: adapter for adapter in adapters
        }
        self.clock = clock
        self.policy = PolicyEngine(
            self.registry,
            config.safety_rules,
            audit=self.audit,
            clock=clock,
        )
        self.ptt = PTTController(
            ptt_backend or UnsupportedPTTBackend(),
            max_hold_ms=config.ptt_max_hold_ms,
            audit=self.audit,
            clock=clock,
        )
        self.led = LedRenderer(config.state_colors)
        self.connection_epoch: int | None = None
        self.connected = False
        self.last_heartbeat: float | None = None
        self._outgoing_sequence = 0
        self._incoming_sequences = SequenceTracker()

    def poll(self) -> tuple[Session, ...]:
        previous_selection = self.registry.selected_session_id
        for name, adapter in self.adapters.items():
            try:
                observations = adapter.discover()
                self.registry.refresh(name, observations, now=self.clock())
            except Exception as error:
                self.registry.mark_integration_failed(name, now=self.clock())
                self.audit.record(
                    AuditRecord(
                        event="integration_poll",
                        outcome="failed",
                        integration=name,
                        detail=f"adapter poll failed: {type(error).__name__}",
                    )
                )
        self.registry.select_first_if_needed()
        selected = self.registry.selected()
        selection_changed = previous_selection != self.registry.selected_session_id
        ptt_selection_invalid = self.ptt.active is not None and (
            selected is None
            or selected.session_id != self.ptt.active.session.session_id
            or selected.health != "ok"
            or ActionCode.PUSH_TO_TALK not in selected.supported_actions
        )
        if selection_changed:
            self.policy.cancel_pending("selection_changed")
            self.ptt.stop("selection_changed")
        elif ptt_selection_invalid:
            self.ptt.stop("ptt_capability_changed")
        return self.registry.sessions

    def connect(
        self, *, epoch: int | None = None
    ) -> tuple[Envelope, Envelope, Envelope]:
        self.ptt.disconnect("connection_reset")
        self.connection_epoch = epoch if epoch is not None else _nonzero_u32()
        self.connected = True
        self.last_heartbeat = self.clock()
        self._incoming_sequences.reset(self.connection_epoch)
        self.policy.reset_connection(self.connection_epoch)
        hello = Envelope.from_payload(
            MessageType.HELLO,
            self._next_sequence(),
            HelloPayload(
                implementation_id=ImplementationId.BRIDGE,
                minor=0,
                max_payload=56,
                capabilities=BRIDGE_CAPABILITIES,
                epoch=self.connection_epoch,
            ),
        )
        return hello, self.brightness_envelope(), self.snapshot_envelope()

    def brightness_envelope(self) -> Envelope:
        if self.connection_epoch is None:
            raise RuntimeError("transport is not connected")
        return Envelope.from_payload(
            MessageType.SET_BRIGHTNESS,
            self._next_sequence(),
            SetBrightnessPayload(
                self.config.brightness_percent,
                self.config.current_limit_ma,
            ),
        )

    def disconnect(self, reason: str = "transport_disconnect") -> None:
        self.connected = False
        self.last_heartbeat = None
        self.policy.cancel_pending(reason)
        self.ptt.disconnect(reason)

    def select(self, session_id: int) -> Session:
        old = self.registry.selected_session_id
        session = self.registry.select(session_id)
        assert session is not None
        if old != session_id:
            self.policy.cancel_pending("selection_changed")
            self.ptt.stop("selection_changed")
        return session

    def snapshot_envelope(self) -> Envelope:
        if self.connection_epoch is None:
            raise RuntimeError("transport is not connected")
        payload = self.led.snapshot(
            self.registry,
            connection_epoch=self.connection_epoch,
            brightness_percent=self.config.brightness_percent,
            battery_display_mode=self.config.battery_display_mode,
        )
        return Envelope.from_payload(
            MessageType.STATE_SNAPSHOT, self._next_sequence(), payload
        )

    def handle(self, envelope: Envelope) -> Envelope:
        if not self.connected or self.connection_epoch is None:
            raise RuntimeError("transport is not connected")
        try:
            self._incoming_sequences.accept(self.connection_epoch, envelope.sequence)
        except SequenceError:
            return self._ack(
                envelope,
                AckStatus.STALE,
                detail=4,
                error=True,
            )
        if envelope.message_type is MessageType.HELLO:
            try:
                hello = envelope.decoded_payload()
            except PayloadError:
                return self._ack(
                    envelope, AckStatus.MALFORMED, detail=2, error=True
                )
            assert isinstance(hello, HelloPayload)
            status = AckStatus.OK if hello.max_payload >= 16 else AckStatus.UNSUPPORTED
            return Envelope.from_payload(
                MessageType.HELLO_ACK,
                self._next_sequence(),
                HelloAckPayload(
                    status=status,
                    minor=min(hello.minor, 0),
                    max_payload=min(hello.max_payload, 56),
                    capabilities=hello.capabilities & BRIDGE_CAPABILITIES,
                    epoch=self.connection_epoch,
                ),
                request_id=envelope.request_id,
                flags=(
                    EnvelopeFlag.RESPONSE
                    | (EnvelopeFlag.ERROR if status is not AckStatus.OK else 0)
                ),
            )
        if envelope.message_type is MessageType.HEARTBEAT:
            try:
                heartbeat = envelope.decoded_payload()
            except PayloadError:
                return self._ack(
                    envelope, AckStatus.MALFORMED, detail=2, error=True
                )
            assert isinstance(heartbeat, HeartbeatPayload)
            self.last_heartbeat = self.clock()
            return self._ack(envelope, AckStatus.OK)
        if envelope.message_type is MessageType.ACTION_INTENT:
            try:
                payload = envelope.decoded_payload()
            except PayloadError:
                return self._ack(
                    envelope, AckStatus.MALFORMED, detail=2, error=True
                )
            assert isinstance(payload, ActionIntentPayload)
            result = self.policy.handle(
                ActionIntent(
                    epoch=payload.epoch,
                    session_id=payload.session_id,
                    state_version=payload.state_version,
                    request_id=envelope.request_id,
                    action=payload.action,
                    gesture=payload.gesture,
                    hold_ms=payload.hold_ms,
                ),
                self._execute,
            )
            flags = EnvelopeFlag.RESPONSE
            if result.status not in {
                ActionResultStatus.SUCCEEDED,
                ActionResultStatus.CONFIRMATION_REQUIRED,
            }:
                flags |= EnvelopeFlag.ERROR
            return Envelope.from_payload(
                MessageType.ACTION_RESULT,
                self._next_sequence(),
                ActionResultPayload(
                    result.action, result.status, result.detail_code
                ),
                request_id=envelope.request_id,
                flags=flags,
            )
        if envelope.message_type is MessageType.KEY_EVENT:
            try:
                payload = envelope.decoded_payload()
            except PayloadError:
                return self._ack(
                    envelope, AckStatus.MALFORMED, detail=2, error=True
                )
            assert isinstance(payload, KeyEventPayload)
            if payload.key_id != self.config.ptt_key_id:
                return self._ack(envelope, AckStatus.UNSUPPORTED, detail=3, error=True)
            if payload.edge is EventEdge.RELEASE:
                result = self.ptt.release()
            else:
                selected = self.registry.selected()
                if (
                    selected is None
                    or selected.health != "ok"
                    or ActionCode.PUSH_TO_TALK not in selected.supported_actions
                ):
                    result = ActionExecution(
                        ActionResultStatus.UNSUPPORTED,
                        "selected session does not support push-to-talk",
                        3,
                    )
                else:
                    result = self.ptt.press(selected)
            return Envelope.from_payload(
                MessageType.ACTION_RESULT,
                self._next_sequence(),
                ActionResultPayload(
                    ActionCode.PUSH_TO_TALK, result.status, result.detail_code
                ),
                request_id=envelope.request_id,
                flags=(
                    EnvelopeFlag.RESPONSE
                    | (
                        EnvelopeFlag.ERROR
                        if result.status is not ActionResultStatus.SUCCEEDED
                        else 0
                    )
                ),
            )
        return self._ack(envelope, AckStatus.UNSUPPORTED, detail=3, error=True)

    def tick(self) -> None:
        self.ptt.tick()
        if (
            self.connected
            and self.last_heartbeat is not None
            and (self.clock() - self.last_heartbeat) * 1000
            >= self.config.heartbeat_timeout_ms
        ):
            self.disconnect("heartbeat_expired")

    def _execute(self, session: Session, action: ActionCode) -> ActionExecution:
        adapter = self.adapters.get(session.integration)
        if adapter is None:
            return ActionExecution(
                ActionResultStatus.UNSUPPORTED, "integration adapter unavailable", 3
            )
        return adapter.execute(session, action)

    def _ack(
        self,
        incoming: Envelope,
        status: AckStatus,
        *,
        detail: int = 0,
        error: bool = False,
    ) -> Envelope:
        return Envelope.from_payload(
            MessageType.ACK,
            self._next_sequence(),
            AckPayload(incoming.message_type, status, detail),
            request_id=incoming.request_id,
            flags=EnvelopeFlag.RESPONSE | (EnvelopeFlag.ERROR if error else 0),
        )

    def _next_sequence(self) -> int:
        sequence = self._outgoing_sequence
        self._outgoing_sequence = (self._outgoing_sequence + 1) & 0xFFFF
        return sequence


def _nonzero_u32() -> int:
    value = 0
    while value == 0:
        value = secrets.randbits(32)
    return value
