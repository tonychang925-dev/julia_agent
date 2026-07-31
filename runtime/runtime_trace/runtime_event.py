from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class RuntimeEvent:
    schema_version: str
    timestamp: str
    session_id: str
    turn_id: int
    backend: str | None = None
    audio: dict[str, Any] = field(default_factory=dict)
    latency: dict[str, Any] = field(default_factory=dict)
    state_trace: list[str] = field(default_factory=list)

    @classmethod
    def from_trace(cls, trace: Any) -> "RuntimeEvent":
        reasoning = trace.reasoning or {}
        return cls(
            schema_version="runtime_event.v1",
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=trace.session_id,
            turn_id=trace.turn_id,
            backend=reasoning.get("backend"),
            audio=trace.audio or {},
            latency=trace.latency or {},
            state_trace=trace.state_trace or [],
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
