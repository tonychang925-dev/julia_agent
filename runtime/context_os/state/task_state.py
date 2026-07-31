from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_unique(items: list[str], value: str) -> list[str]:
    value = value.strip()
    if not value or value in items:
        return list(items)
    return [*items, value]


@dataclass(frozen=True)
class JuliaTaskState:
    """Current task/work-item state for Julia Context OS.

    Task state is not the conversation transcript. It records what Julia and Tony
    are actively trying to complete, the status, verified decisions, blockers,
    and next actions.
    """

    task_id: str
    objective: str
    session_id: str | None = None
    status: str = "active"
    progress: float = 0.0
    decisions: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.task_id:
            raise ValueError("task_id is required")
        if not self.objective:
            raise ValueError("objective is required")
        if self.progress < 0 or self.progress > 1:
            raise ValueError("progress must be in [0, 1]")

    @classmethod
    def create(
        cls,
        *,
        objective: str,
        session_id: str | None = None,
        task_id: str | None = None,
        status: str = "active",
        progress: float = 0.0,
        next_actions: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "JuliaTaskState":
        return cls(
            task_id=task_id or f"task_{uuid4().hex}",
            session_id=session_id,
            objective=objective,
            status=status,
            progress=progress,
            next_actions=list(next_actions or []),
            metadata=dict(metadata or {}),
        )

    def with_status(self, status: str, *, progress: float | None = None) -> "JuliaTaskState":
        return replace(self, status=status, progress=self.progress if progress is None else progress, updated_at=now_iso())

    def add_decision(self, decision: str) -> "JuliaTaskState":
        return replace(self, decisions=_append_unique(self.decisions, decision), updated_at=now_iso())

    def add_blocker(self, blocker: str) -> "JuliaTaskState":
        return replace(self, blockers=_append_unique(self.blockers, blocker), updated_at=now_iso())

    def add_next_action(self, action: str) -> "JuliaTaskState":
        return replace(self, next_actions=_append_unique(self.next_actions, action), updated_at=now_iso())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JuliaTaskState":
        return cls(
            task_id=data["task_id"],
            objective=data["objective"],
            session_id=data.get("session_id"),
            status=data.get("status") or "active",
            progress=float(data.get("progress") or 0.0),
            decisions=list(data.get("decisions") or []),
            blockers=list(data.get("blockers") or []),
            next_actions=list(data.get("next_actions") or []),
            created_at=data.get("created_at") or now_iso(),
            updated_at=data.get("updated_at") or now_iso(),
            metadata=dict(data.get("metadata") or {}),
        )
