"""State-aware semantic intent authorization and idempotency."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable, Mapping

from .audit import AuditRecord, AuditSink, NullAuditSink
from .config import SafetyRuleConfig
from .core import Session, SessionRegistry
from .integrations import ActionExecution
from .protocol import (
    ActionCode,
    ActionResultStatus,
    GestureClass,
)


@dataclass(frozen=True)
class ActionIntent:
    epoch: int
    session_id: int
    state_version: int
    request_id: int
    action: ActionCode
    gesture: GestureClass
    hold_ms: int

    def fingerprint(self) -> tuple[int, ...]:
        return (
            self.epoch,
            self.session_id,
            self.state_version,
            self.request_id,
            int(self.action),
            int(self.gesture),
            self.hold_ms,
        )


@dataclass(frozen=True)
class PolicyResult:
    action: ActionCode
    status: ActionResultStatus
    detail: str
    detail_code: int = 0


@dataclass(frozen=True)
class _CachedResult:
    fingerprint: tuple[int, ...]
    result: PolicyResult


@dataclass(frozen=True)
class _PendingConfirmation:
    epoch: int
    session_id: int
    state_version: int
    action: ActionCode
    expires_at: float


Executor = Callable[[Session, ActionCode], ActionExecution]


class PolicyEngine:
    def __init__(
        self,
        registry: SessionRegistry,
        rules: Mapping[ActionCode, SafetyRuleConfig],
        *,
        audit: AuditSink | None = None,
        confirmation_timeout_ms: int = 5000,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.registry = registry
        self.rules = dict(rules)
        self.audit = audit or NullAuditSink()
        self.confirmation_timeout_ms = confirmation_timeout_ms
        self.clock = clock
        self.connection_epoch: int | None = None
        self._processed: dict[tuple[int, int], _CachedResult] = {}
        self._pending: dict[
            tuple[int, int, ActionCode], _PendingConfirmation
        ] = {}

    def reset_connection(self, epoch: int) -> None:
        self.connection_epoch = epoch
        self._processed.clear()
        self._pending.clear()

    def cancel_pending(self, reason: str) -> None:
        for pending in tuple(self._pending.values()):
            self.audit.record(
                AuditRecord(
                    event="confirmation_cancelled",
                    outcome="cancelled",
                    epoch=pending.epoch,
                    session_id=pending.session_id,
                    action=pending.action.name.lower(),
                    state_version=pending.state_version,
                    detail=reason,
                )
            )
        self._pending.clear()

    def handle(self, intent: ActionIntent, executor: Executor) -> PolicyResult:
        cache_key = (intent.epoch, intent.request_id)
        cached = self._processed.get(cache_key)
        if cached is not None:
            if cached.fingerprint != intent.fingerprint():
                return self._record_and_cache(
                    intent,
                    PolicyResult(
                        intent.action,
                        ActionResultStatus.REJECTED,
                        "request_id reused with different intent",
                        5,
                    ),
                    cache=False,
                )
            self.audit.record(
                self._audit_record(intent, cached.result, event="intent_duplicate")
            )
            return cached.result

        rejection = self._precheck(intent)
        if rejection is not None:
            return self._record_and_cache(intent, rejection)

        session = self.registry.get(intent.session_id)
        assert session is not None
        rule = self.rules[intent.action]
        if rule.require_second_confirmation:
            confirmation_key = (intent.epoch, intent.session_id, intent.action)
            pending = self._pending.get(confirmation_key)
            now = self.clock()
            if (
                pending is None
                or pending.expires_at < now
                or pending.state_version != intent.state_version
            ):
                self._pending[confirmation_key] = _PendingConfirmation(
                    intent.epoch,
                    intent.session_id,
                    intent.state_version,
                    intent.action,
                    now + self.confirmation_timeout_ms / 1000,
                )
                return self._record_and_cache(
                    intent,
                    PolicyResult(
                        intent.action,
                        ActionResultStatus.CONFIRMATION_REQUIRED,
                        "repeat confirmed gesture before timeout",
                        1,
                    ),
                )
            self._pending.pop(confirmation_key, None)

        self.audit.record(
            AuditRecord(
                event="intent_execute",
                outcome="attempt",
                epoch=intent.epoch,
                request_id=intent.request_id,
                session_id=session.session_id,
                integration=session.integration,
                action=intent.action.name.lower(),
                state=session.state.name.lower(),
                state_version=session.state_version,
                gesture=intent.gesture.name.lower(),
            )
        )
        try:
            execution = executor(session, intent.action)
        except Exception as error:  # adapter isolation boundary
            result = PolicyResult(
                intent.action,
                ActionResultStatus.FAILED,
                f"integration execution failed: {type(error).__name__}",
                5,
            )
        else:
            result = PolicyResult(
                intent.action,
                execution.status,
                execution.detail,
                execution.detail_code,
            )
        return self._record_and_cache(intent, result)

    def _precheck(self, intent: ActionIntent) -> PolicyResult | None:
        if intent.request_id == 0:
            return self._reject(intent, "sensitive action requires request_id", 1)
        if self.connection_epoch is None or intent.epoch != self.connection_epoch:
            return self._reject(intent, "stale connection epoch", 4)
        selected = self.registry.selected()
        if selected is None or selected.session_id != intent.session_id:
            return self._reject(intent, "stale or unselected session", 4)
        session = self.registry.get(intent.session_id)
        if session is None:
            return self._reject(intent, "unknown session", 4)
        if session.state_version != intent.state_version:
            return self._reject(intent, "stale state_version", 4)
        if intent.action not in session.supported_actions:
            return PolicyResult(
                intent.action,
                ActionResultStatus.UNSUPPORTED,
                "action not supported by selected session",
                3,
            )
        rule = self.rules.get(intent.action)
        if rule is None:
            return self._reject(intent, "no reviewed safety rule for action", 1)
        if rule.required_state is not None and session.state != rule.required_state:
            return self._reject(
                intent,
                f"action requires {rule.required_state.name.lower()} state",
                1,
            )
        if intent.gesture != rule.gesture:
            return self._reject(
                intent,
                f"action requires {rule.gesture.name.lower()} gesture",
                1,
            )
        if intent.hold_ms < rule.minimum_hold_ms:
            return self._reject(
                intent,
                f"hold duration must be at least {rule.minimum_hold_ms} ms",
                1,
            )
        return None

    @staticmethod
    def _reject(intent: ActionIntent, detail: str, detail_code: int) -> PolicyResult:
        return PolicyResult(
            intent.action, ActionResultStatus.REJECTED, detail, detail_code
        )

    def _record_and_cache(
        self,
        intent: ActionIntent,
        result: PolicyResult,
        *,
        cache: bool = True,
    ) -> PolicyResult:
        if cache:
            self._processed[(intent.epoch, intent.request_id)] = _CachedResult(
                intent.fingerprint(), result
            )
        self.audit.record(self._audit_record(intent, result))
        return result

    def _audit_record(
        self,
        intent: ActionIntent,
        result: PolicyResult,
        *,
        event: str = "intent_result",
    ) -> AuditRecord:
        session = self.registry.get(intent.session_id)
        return AuditRecord(
            event=event,
            outcome=result.status.name.lower(),
            epoch=intent.epoch,
            request_id=intent.request_id,
            session_id=intent.session_id,
            integration=session.integration if session else None,
            action=intent.action.name.lower(),
            state=session.state.name.lower() if session else None,
            state_version=intent.state_version,
            gesture=intent.gesture.name.lower(),
            detail=result.detail,
        )
