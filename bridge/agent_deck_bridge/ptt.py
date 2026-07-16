"""Fail-closed push-to-talk lifecycle management."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable, Protocol

from .audit import AuditRecord, AuditSink, NullAuditSink
from .core import Session
from .integrations import ActionExecution
from .protocol import ActionResultStatus


class PTTBackend(Protocol):
    def start(self, session: Session) -> ActionExecution: ...

    def stop(self, session: Session, reason: str) -> ActionExecution: ...


class UnsupportedPTTBackend:
    def start(self, session: Session) -> ActionExecution:
        del session
        return ActionExecution(
            ActionResultStatus.UNSUPPORTED,
            "no reviewed host voice-input backend is configured",
        )

    def stop(self, session: Session, reason: str) -> ActionExecution:
        del session, reason
        return ActionExecution(ActionResultStatus.SUCCEEDED, "capture was not active")


@dataclass(frozen=True)
class PTTState:
    session: Session
    started_at: float
    deadline: float


class PTTController:
    def __init__(
        self,
        backend: PTTBackend,
        *,
        max_hold_ms: int,
        audit: AuditSink | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_hold_ms <= 0:
            raise ValueError("max_hold_ms must be positive")
        self.backend = backend
        self.max_hold_ms = max_hold_ms
        self.audit = audit or NullAuditSink()
        self.clock = clock
        self.active: PTTState | None = None

    def press(self, session: Session) -> ActionExecution:
        if self.active is not None:
            if self.active.session.session_id == session.session_id:
                return ActionExecution(
                    ActionResultStatus.SUCCEEDED, "push-to-talk already active"
                )
            self.stop("session_changed")
        result = self.backend.start(session)
        self.audit.record(
            AuditRecord(
                event="ptt_start",
                outcome=result.status.name.lower(),
                session_id=session.session_id,
                integration=session.integration,
                action="push_to_talk",
                state=session.state.name.lower(),
                state_version=session.state_version,
                detail=result.detail,
            )
        )
        if result.status is ActionResultStatus.SUCCEEDED:
            now = self.clock()
            self.active = PTTState(
                session,
                now,
                now + self.max_hold_ms / 1000,
            )
        return result

    def release(self) -> ActionExecution:
        return self.stop("release")

    def stop(self, reason: str) -> ActionExecution:
        active = self.active
        if active is None:
            return ActionExecution(
                ActionResultStatus.SUCCEEDED, "push-to-talk already stopped"
            )
        self.active = None
        try:
            result = self.backend.stop(active.session, reason)
        except Exception as error:
            result = ActionExecution(
                ActionResultStatus.FAILED,
                f"voice backend stop failed: {type(error).__name__}",
            )
        self.audit.record(
            AuditRecord(
                event="ptt_stop",
                outcome=result.status.name.lower(),
                session_id=active.session.session_id,
                integration=active.session.integration,
                action="push_to_talk",
                state=active.session.state.name.lower(),
                state_version=active.session.state_version,
                detail=f"{reason}: {result.detail}",
            )
        )
        return result

    def tick(self) -> ActionExecution | None:
        if self.active is None or self.clock() < self.active.deadline:
            return None
        return self.stop("max_hold_timeout")

    def disconnect(self, reason: str = "transport_disconnect") -> ActionExecution:
        return self.stop(reason)
