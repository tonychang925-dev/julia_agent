from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class AgentEvent:
    event_type: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: f"evt_{uuid4().hex[:12]}")
    parent_id: str | None = None
    correlation_id: str | None = None
    timestamp: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
