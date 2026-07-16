"""Structured audit records for guarded bridge actions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
from typing import Any, Protocol


@dataclass(frozen=True)
class AuditRecord:
    event: str
    outcome: str
    epoch: int | None = None
    request_id: int | None = None
    session_id: int | None = None
    integration: str | None = None
    action: str | None = None
    state: str | None = None
    state_version: int | None = None
    gesture: str | None = None
    detail: str | None = None
    timestamp: str | None = None

    def with_timestamp(self) -> "AuditRecord":
        if self.timestamp is not None:
            return self
        return AuditRecord(
            **{
                **asdict(self),
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            key: value
            for key, value in asdict(self.with_timestamp()).items()
            if value is not None
        }


class AuditSink(Protocol):
    def record(self, record: AuditRecord) -> None: ...


class NullAuditSink:
    def record(self, record: AuditRecord) -> None:
        del record


class MemoryAuditSink:
    def __init__(self) -> None:
        self.records: list[AuditRecord] = []

    def record(self, record: AuditRecord) -> None:
        self.records.append(record.with_timestamp())


class JsonLineAuditSink:
    """Append one JSON object per line without storing credentials or payload blobs."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser()
        self._lock = threading.Lock()

    def record(self, record: AuditRecord) -> None:
        serialized = json.dumps(
            record.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as output:
                output.write(serialized)
                output.write("\n")
