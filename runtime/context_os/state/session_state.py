from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_unique(items: list[str], value: str) -> list[str]:
    value = value.strip()
    if not value or value in items:
        return list(items)
    return [*items, value]


@dataclass(frozen=True)
class JuliaSessionState:
    """Persistent project/session workspace state for Julia Context OS.

    Session state is not raw memory and not a transcript. It records the stable
    working environment that should survive provider changes and session restarts:
    project context, architecture decisions, constraints, and active goals.
    """

    session_id: str
    project_context: dict[str, Any] = field(default_factory=dict)
    architecture_decisions: list[str] = field(default_factory=list)
    persistent_constraints: list[str] = field(default_factory=list)
    active_goals: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.session_id:
            raise ValueError("session_id is required")

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        project: str = "",
        phase: str = "",
        architecture: str = "",
        design_principles: list[str] | None = None,
        persistent_constraints: list[str] | None = None,
        active_goals: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "JuliaSessionState":
        context: dict[str, Any] = {}
        if project:
            context["project"] = project
        if phase:
            context["phase"] = phase
        if architecture:
            context["architecture"] = architecture
        if design_principles:
            context["design_principles"] = list(design_principles)
        return cls(
            session_id=session_id,
            project_context=context,
            persistent_constraints=list(persistent_constraints or []),
            active_goals=list(active_goals or []),
            metadata=dict(metadata or {}),
        )

    def with_project_context(self, **updates: Any) -> "JuliaSessionState":
        return replace(self, project_context={**self.project_context, **updates}, updated_at=now_iso())

    def add_decision(self, decision: str) -> "JuliaSessionState":
        return replace(self, architecture_decisions=_append_unique(self.architecture_decisions, decision), updated_at=now_iso())

    def add_constraint(self, constraint: str) -> "JuliaSessionState":
        return replace(self, persistent_constraints=_append_unique(self.persistent_constraints, constraint), updated_at=now_iso())

    def add_goal(self, goal: str) -> "JuliaSessionState":
        return replace(self, active_goals=_append_unique(self.active_goals, goal), updated_at=now_iso())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JuliaSessionState":
        return cls(
            session_id=data["session_id"],
            project_context=dict(data.get("project_context") or {}),
            architecture_decisions=list(data.get("architecture_decisions") or []),
            persistent_constraints=list(data.get("persistent_constraints") or []),
            active_goals=list(data.get("active_goals") or []),
            created_at=data.get("created_at") or now_iso(),
            updated_at=data.get("updated_at") or now_iso(),
            version=int(data.get("version") or 1),
            metadata=dict(data.get("metadata") or {}),
        )
