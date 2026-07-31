from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class WorkerEvent:
    event_type: str
    source_turn_id: str
    created_at: str = field(default_factory=now_iso)
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_type:
            raise ValueError("event_type is required")
        if not self.source_turn_id:
            raise ValueError("source_turn_id is required")

    @classmethod
    def turn_completed(cls, *, source_turn_id: str, payload: dict[str, Any] | None = None) -> "WorkerEvent":
        return cls(event_type="turn_completed", source_turn_id=source_turn_id, payload=dict(payload or {}))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
