"""Isolated, non-shell integration adapters."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any, Callable, Protocol, Sequence

from .core import Session, SessionObservation
from .protocol import ActionCode, ActionResultStatus


class IntegrationError(RuntimeError):
    """An integration failed without terminating the bridge runtime."""


@dataclass(frozen=True)
class ActionExecution:
    status: ActionResultStatus
    detail: str = ""
    detail_code: int = 0


class IntegrationAdapter(Protocol):
    name: str

    def discover(self) -> list[SessionObservation]: ...

    def execute(self, session: Session, action: ActionCode) -> ActionExecution: ...


Runner = Callable[[Sequence[str], float], subprocess.CompletedProcess[str]]


def safe_run(argv: Sequence[str], timeout: float) -> subprocess.CompletedProcess[str]:
    """Run a fixed argv vector without a shell."""

    if not argv or any(
        not isinstance(item, str) or not item or "\x00" in item for item in argv
    ):
        raise ValueError("argv must contain non-empty NUL-free strings")
    return subprocess.run(
        list(argv),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=False,
    )


class FixtureAdapter:
    """File-backed integration for repeatable state and policy tests."""

    name = "fixture"

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.execute_count = 0
        self._action_results: dict[tuple[str, ActionCode], ActionExecution] = {}

    def discover(self) -> list[SessionObservation]:
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise IntegrationError(f"unable to load fixture: {error}") from error
        if not isinstance(document, dict):
            raise IntegrationError("fixture root must be an object")
        sessions_raw = document.get("sessions", [])
        if not isinstance(sessions_raw, list):
            raise IntegrationError("fixture sessions must be a list")
        observations: list[SessionObservation] = []
        for index, raw_session in enumerate(sessions_raw):
            if not isinstance(raw_session, dict):
                raise IntegrationError(f"fixture session {index} must be an object")
            upstream_id = raw_session.get("id")
            label = raw_session.get("label", upstream_id)
            if not isinstance(upstream_id, str) or not upstream_id:
                raise IntegrationError(f"fixture session {index} needs a string id")
            if not isinstance(label, str):
                raise IntegrationError(f"fixture session {index} label must be a string")
            actions = _parse_actions(raw_session.get("actions", []))
            metadata_raw = raw_session.get("metadata", {})
            if not isinstance(metadata_raw, dict) or not all(
                isinstance(key, str) and isinstance(value, (str, int, float, bool))
                for key, value in metadata_raw.items()
            ):
                raise IntegrationError(
                    f"fixture session {index} metadata must contain scalar values"
                )
            observations.append(
                SessionObservation(
                    integration=self.name,
                    upstream_id=upstream_id,
                    label=label,
                    state=raw_session.get("state"),
                    supported_actions=actions,
                    metadata=tuple(
                        sorted((key, str(value)) for key, value in metadata_raw.items())
                    ),
                )
            )
        self._action_results = self._parse_action_results(
            document.get("action_results", {})
        )
        return observations

    def execute(self, session: Session, action: ActionCode) -> ActionExecution:
        self.execute_count += 1
        if session.integration != self.name:
            return ActionExecution(
                ActionResultStatus.REJECTED, "session belongs to another integration"
            )
        if action not in session.supported_actions:
            return ActionExecution(ActionResultStatus.UNSUPPORTED, "action unsupported")
        return self._action_results.get(
            (session.upstream_id, action),
            ActionExecution(ActionResultStatus.SUCCEEDED, "fixture action completed"),
        )

    def _parse_action_results(self, raw: Any) -> dict[tuple[str, ActionCode], ActionExecution]:
        if not isinstance(raw, dict):
            raise IntegrationError("fixture action_results must be an object")
        results: dict[tuple[str, ActionCode], ActionExecution] = {}
        for key, value in raw.items():
            if not isinstance(key, str) or "/" not in key:
                raise IntegrationError("action result keys must be <session>/<action>")
            session_id, action_name = key.rsplit("/", 1)
            try:
                action = ActionCode[action_name.upper()]
            except KeyError as error:
                raise IntegrationError(f"unknown fixture action {action_name!r}") from error
            if isinstance(value, str):
                status_name = value
                detail = ""
                detail_code = 0
            elif isinstance(value, dict):
                status_name = value.get("status")
                detail = value.get("detail", "")
                detail_code = value.get("detail_code", 0)
            else:
                raise IntegrationError(f"invalid action result for {key}")
            if not isinstance(status_name, str):
                raise IntegrationError(f"action result {key} needs a status")
            try:
                status = ActionResultStatus[status_name.upper()]
            except KeyError as error:
                raise IntegrationError(
                    f"unknown action result status {status_name!r}"
                ) from error
            if not isinstance(detail, str) or not isinstance(detail_code, int):
                raise IntegrationError(f"invalid action result detail for {key}")
            results[(session_id, action)] = ActionExecution(
                status, detail, detail_code
            )
        return results


class TmuxAdapter:
    """Read-only tmux pane discovery.

    No device-originated value is interpolated into an executable command, and
    this adapter intentionally does not call ``tmux send-keys``.
    """

    name = "tmux"
    _FORMAT = (
        "#{pane_id}\t#{session_name}\t#{window_index}.#{pane_index}\t"
        "#{pane_current_command}\t#{pane_title}\t#{pane_dead}"
    )

    def __init__(
        self,
        *,
        executable: str = "tmux",
        runner: Runner = safe_run,
        timeout: float = 2.0,
    ) -> None:
        self.executable = executable
        self.runner = runner
        self.timeout = timeout

    def discover(self) -> list[SessionObservation]:
        argv = [self.executable, "list-panes", "-a", "-F", self._FORMAT]
        try:
            result = self.runner(argv, self.timeout)
        except (OSError, subprocess.SubprocessError) as error:
            raise IntegrationError(f"tmux discovery failed: {error}") from error
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            if "no server running" in stderr.lower():
                return []
            raise IntegrationError(
                f"tmux list-panes exited {result.returncode}: {stderr[:200]}"
            )
        observations: list[SessionObservation] = []
        for line_number, line in enumerate(result.stdout.splitlines(), start=1):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) != 6:
                raise IntegrationError(f"tmux output line {line_number} is malformed")
            pane_id, session_name, pane_index, command, title, dead = parts
            if not pane_id.startswith("%"):
                raise IntegrationError(f"tmux output line {line_number} has invalid pane id")
            state = _tmux_state(command, title, dead)
            observations.append(
                SessionObservation(
                    integration=self.name,
                    upstream_id=pane_id,
                    label=f"{session_name}:{pane_index} {title or command}".strip(),
                    state=state,
                    supported_actions=frozenset(),
                    metadata=(
                        ("command", command),
                        ("pane", pane_index),
                        ("session", session_name),
                    ),
                )
            )
        return observations

    def execute(self, session: Session, action: ActionCode) -> ActionExecution:
        del session, action
        return ActionExecution(
            ActionResultStatus.UNSUPPORTED,
            "tmux adapter is discovery-only; send-keys is intentionally disabled",
        )


@dataclass(frozen=True)
class CodexCapabilities:
    available: bool
    executable: str | None
    version: str | None
    capabilities: frozenset[str]
    error: str | None = None


class CodexAdapter:
    """Read-only Codex CLI capability detection.

    It calls only ``--version`` and ``--help``. Semantic action execution stays
    unsupported until a reviewed Codex API or explicit backend is supplied.
    """

    name = "codex"

    def __init__(
        self,
        *,
        executable: str | None = None,
        runner: Runner = safe_run,
        timeout: float = 3.0,
        which: Callable[[str], str | None] = shutil.which,
    ) -> None:
        self._configured_executable = executable
        self.runner = runner
        self.timeout = timeout
        self.which = which
        self.last_capabilities: CodexCapabilities | None = None

    def detect_capabilities(self) -> CodexCapabilities:
        executable = self._configured_executable or self.which("codex")
        if executable is None:
            capabilities = CodexCapabilities(False, None, None, frozenset())
            self.last_capabilities = capabilities
            return capabilities
        try:
            version_result = self.runner([executable, "--version"], self.timeout)
            help_result = self.runner([executable, "--help"], self.timeout)
        except (OSError, subprocess.SubprocessError) as error:
            capabilities = CodexCapabilities(
                False, executable, None, frozenset(), str(error)
            )
            self.last_capabilities = capabilities
            return capabilities
        if version_result.returncode != 0:
            capabilities = CodexCapabilities(
                False,
                executable,
                None,
                frozenset(),
                (version_result.stderr or "").strip()[:200],
            )
            self.last_capabilities = capabilities
            return capabilities
        help_text = help_result.stdout if help_result.returncode == 0 else ""
        detected: set[str] = {"version_detection"}
        lowered = help_text.lower()
        for needle, capability in (
            ("resume", "resume"),
            ("exec", "noninteractive_exec"),
            ("approval", "approval_configuration"),
            ("sandbox", "sandbox_configuration"),
            ("json", "json_output"),
            ("voice", "voice_input"),
        ):
            if needle in lowered:
                detected.add(capability)
        capabilities = CodexCapabilities(
            True,
            executable,
            (version_result.stdout or "").strip()[:200],
            frozenset(detected),
            None if help_result.returncode == 0 else "help unavailable",
        )
        self.last_capabilities = capabilities
        return capabilities

    def discover(self) -> list[SessionObservation]:
        self.detect_capabilities()
        return []

    def execute(self, session: Session, action: ActionCode) -> ActionExecution:
        del session, action
        return ActionExecution(
            ActionResultStatus.UNSUPPORTED,
            "Codex adapter is capability-detection-only in V1 prototype",
        )


def _parse_actions(raw: Any) -> frozenset[ActionCode]:
    if not isinstance(raw, list):
        raise IntegrationError("session actions must be a list")
    actions: set[ActionCode] = set()
    for item in raw:
        if not isinstance(item, str):
            raise IntegrationError("session action names must be strings")
        try:
            actions.add(ActionCode[item.upper()])
        except KeyError as error:
            raise IntegrationError(f"unknown session action {item!r}") from error
    return frozenset(actions)


def _tmux_state(command: str, title: str, dead: str) -> str:
    if dead not in {"0", ""}:
        return "failed"
    combined = f"{command} {title}".lower()
    if any(token in combined for token in ("approval", "approve", "confirm")):
        return "waiting_approval"
    if any(token in combined for token in ("waiting input", "question", "prompt")):
        return "waiting_input"
    if any(token in combined for token in ("failed", "error", "crash")):
        return "failed"
    if any(token in combined for token in ("completed", "complete", "done")):
        return "completed"
    if command.lower() in {"bash", "zsh", "fish", "sh"}:
        return "idle"
    return "running"
