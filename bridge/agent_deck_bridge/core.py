"""Session identity, state normalization, and selection."""

from __future__ import annotations

from dataclasses import dataclass, replace
import secrets
import time
from typing import Iterable

from .protocol import ActionCode, NormalizedState


_STATE_ALIASES: dict[str, NormalizedState] = {
    "idle": NormalizedState.IDLE,
    "ready": NormalizedState.IDLE,
    "stopped": NormalizedState.IDLE,
    "running": NormalizedState.RUNNING,
    "working": NormalizedState.RUNNING,
    "busy": NormalizedState.RUNNING,
    "waiting_approval": NormalizedState.WAITING_APPROVAL,
    "approval": NormalizedState.WAITING_APPROVAL,
    "confirm": NormalizedState.WAITING_APPROVAL,
    "waiting_input": NormalizedState.WAITING_INPUT,
    "input": NormalizedState.WAITING_INPUT,
    "prompt": NormalizedState.WAITING_INPUT,
    "completed": NormalizedState.COMPLETED,
    "complete": NormalizedState.COMPLETED,
    "done": NormalizedState.COMPLETED,
    "failed": NormalizedState.FAILED,
    "error": NormalizedState.FAILED,
    "crashed": NormalizedState.FAILED,
    "disconnected": NormalizedState.DISCONNECTED,
    "unknown": NormalizedState.DISCONNECTED,
    "offline": NormalizedState.DISCONNECTED,
}


def normalize_state(raw_state: str | NormalizedState | None) -> NormalizedState:
    if isinstance(raw_state, NormalizedState):
        return raw_state
    if raw_state is None:
        return NormalizedState.DISCONNECTED
    normalized = raw_state.strip().lower().replace("-", "_").replace(" ", "_")
    return _STATE_ALIASES.get(normalized, NormalizedState.DISCONNECTED)


@dataclass(frozen=True)
class SessionObservation:
    integration: str
    upstream_id: str
    label: str
    state: str | NormalizedState | None
    supported_actions: frozenset[ActionCode] = frozenset()
    metadata: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class Session:
    session_id: int
    integration: str
    upstream_id: str
    label: str
    state: NormalizedState
    state_version: int
    supported_actions: frozenset[ActionCode]
    last_observed_monotonic: float
    health: str = "ok"
    metadata: tuple[tuple[str, str], ...] = ()


class SessionRegistry:
    """Assign runtime-scoped IDs and preserve them across discovery refreshes."""

    def __init__(self, *, epoch: int | None = None) -> None:
        self.epoch = epoch if epoch is not None else _nonzero_u32()
        self._next_id = 1
        self._next_version = 1
        self._sessions: dict[int, Session] = {}
        self._by_upstream: dict[tuple[str, str], int] = {}
        self._selected_session_id: int | None = None

    @property
    def selected_session_id(self) -> int | None:
        return self._selected_session_id

    @property
    def sessions(self) -> tuple[Session, ...]:
        return tuple(sorted(self._sessions.values(), key=lambda item: item.session_id))

    def get(self, session_id: int) -> Session | None:
        return self._sessions.get(session_id)

    def selected(self) -> Session | None:
        if self._selected_session_id is None:
            return None
        return self._sessions.get(self._selected_session_id)

    def refresh(
        self,
        integration: str,
        observations: Iterable[SessionObservation],
        *,
        now: float | None = None,
    ) -> tuple[Session, ...]:
        timestamp = time.monotonic() if now is None else now
        observed_keys: set[tuple[str, str]] = set()
        for observation in observations:
            if observation.integration != integration:
                raise ValueError("observation integration does not match refresh owner")
            key = (integration, observation.upstream_id)
            if key in observed_keys:
                raise ValueError(f"duplicate upstream session {key!r}")
            observed_keys.add(key)
            state = normalize_state(observation.state)
            existing_id = self._by_upstream.get(key)
            if existing_id is None:
                session_id = self._allocate_id()
                session = Session(
                    session_id=session_id,
                    integration=integration,
                    upstream_id=observation.upstream_id,
                    label=observation.label,
                    state=state,
                    state_version=self._allocate_version(),
                    supported_actions=observation.supported_actions,
                    last_observed_monotonic=timestamp,
                    metadata=observation.metadata,
                )
                self._sessions[session_id] = session
                self._by_upstream[key] = session_id
                continue
            existing = self._sessions[existing_id]
            changed = (
                existing.label != observation.label
                or existing.state != state
                or existing.supported_actions != observation.supported_actions
                or existing.metadata != observation.metadata
                or existing.health != "ok"
            )
            self._sessions[existing_id] = replace(
                existing,
                label=observation.label,
                state=state,
                state_version=(
                    self._allocate_version() if changed else existing.state_version
                ),
                supported_actions=observation.supported_actions,
                last_observed_monotonic=timestamp,
                health="ok",
                metadata=observation.metadata,
            )

        stale_keys = [
            key
            for key in self._by_upstream
            if key[0] == integration and key not in observed_keys
        ]
        for key in stale_keys:
            stale_id = self._by_upstream.pop(key)
            self._sessions.pop(stale_id, None)
            if self._selected_session_id == stale_id:
                self._selected_session_id = None
        return self.sessions

    def mark_integration_failed(self, integration: str, *, now: float | None = None) -> None:
        timestamp = time.monotonic() if now is None else now
        for session_id, session in tuple(self._sessions.items()):
            if session.integration != integration or session.health == "failed":
                continue
            self._sessions[session_id] = replace(
                session,
                health="failed",
                state=NormalizedState.FAILED,
                state_version=self._allocate_version(),
                last_observed_monotonic=timestamp,
            )

    def select(self, session_id: int | None) -> Session | None:
        if session_id is None:
            self._selected_session_id = None
            return None
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"unknown session_id {session_id}")
        self._selected_session_id = session_id
        return session

    def select_first_if_needed(self) -> Session | None:
        selected = self.selected()
        if selected is not None:
            return selected
        if not self._sessions:
            return None
        first_id = min(self._sessions)
        return self.select(first_id)

    def _allocate_id(self) -> int:
        if self._next_id > 0xFFFFFFFF:
            raise OverflowError("runtime session ID space exhausted")
        value = self._next_id
        self._next_id += 1
        return value

    def _allocate_version(self) -> int:
        if self._next_version > 0xFFFFFFFF:
            raise OverflowError("state version space exhausted")
        value = self._next_version
        self._next_version += 1
        return value


def _nonzero_u32() -> int:
    value = 0
    while value == 0:
        value = secrets.randbits(32)
    return value
