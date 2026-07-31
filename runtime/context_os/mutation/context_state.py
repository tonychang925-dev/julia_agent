from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any


@dataclass(frozen=True)
class OpenLoopState:
    loop_id: str
    title: str
    status: str = "open"
    source_turn_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ContextWorkingState:
    session_id: str
    current_arc: str = ""
    current_task: str = ""
    cognitive_mode: str = "conversation"
    open_loops: list[OpenLoopState] = field(default_factory=list)
    mode_transition_history: list[str] = field(default_factory=list)
    evidence_gaps: list[dict[str, Any]] = field(default_factory=list)
    quality_warnings: list[str] = field(default_factory=list)
    protected_fields: set[str] = field(default_factory=lambda: {"identity", "relationship", "persona"})

    def __post_init__(self) -> None:
        if not self.session_id:
            raise ValueError("session_id is required")

    def with_updates(self, **updates: Any) -> "ContextWorkingState":
        return replace(self, **updates)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["protected_fields"] = sorted(self.protected_fields)
        data["open_loops"] = [loop.to_dict() for loop in self.open_loops]
        return data
