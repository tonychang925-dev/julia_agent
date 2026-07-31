from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4

from runtime.context_os.compact import ExperienceCompactState
from runtime.context_os.state import JuliaSessionState, JuliaTaskState
from runtime.context_os.transcript import ContextMessageRecord


@dataclass(frozen=True)
class JuliaContext:
    """Provider-independent reconstructed model-facing cognitive context."""

    context_id: str
    user_id: str
    session_id: str
    project: str = ""
    phase: str = ""
    current_task: str = ""
    active_goals: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    open_loops: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    recent_tail: list[ContextMessageRecord] = field(default_factory=list)
    compact_ids: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["recent_tail"] = [r.to_dict() for r in self.recent_tail]
        return data

    def to_context_text(self) -> str:
        parts = [
            f"JuliaContext: {self.context_id}",
            f"Project: {self.project}",
            f"Phase: {self.phase}",
            f"Current task: {self.current_task}",
        ]
        if self.active_goals:
            parts.append("Active goals:\n" + "\n".join(f"- {x}" for x in self.active_goals))
        if self.decisions:
            parts.append("Decisions:\n" + "\n".join(f"- {x}" for x in self.decisions))
        if self.open_loops:
            parts.append("Open loops:\n" + "\n".join(f"- {x}" for x in self.open_loops))
        if self.next_actions:
            parts.append("Next actions:\n" + "\n".join(f"- {x}" for x in self.next_actions))
        if self.evidence_refs:
            parts.append("Evidence refs: " + ", ".join(self.evidence_refs))
        if self.recent_tail:
            tail = "\n".join(f"[{r.speaker.value}] {r.content}" for r in self.recent_tail)
            parts.append("Recent preserved tail:\n" + tail)
        return "\n\n".join(p for p in parts if p.strip())


@dataclass(frozen=True)
class ResurrectionSnapshot:
    """Restoration target: cognitive state inputs, not raw transcript reload."""

    snapshot_id: str
    user_id: str
    session_id: str
    session_state: JuliaSessionState | None = None
    task_state: JuliaTaskState | None = None
    compact_state: ExperienceCompactState | None = None
    recent_tail: list[ContextMessageRecord] = field(default_factory=list)
    active_open_loops: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    restoration_confidence: float = 0.0
    sources: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        session_id: str,
        session_state: JuliaSessionState | None = None,
        task_state: JuliaTaskState | None = None,
        compact_state: ExperienceCompactState | None = None,
        recent_tail: list[ContextMessageRecord] | None = None,
        active_open_loops: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        restoration_confidence: float = 0.0,
        sources: list[str] | None = None,
        missing: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "ResurrectionSnapshot":
        return cls(
            snapshot_id=f"resurrection_snapshot_{uuid4().hex}",
            user_id=user_id,
            session_id=session_id,
            session_state=session_state,
            task_state=task_state,
            compact_state=compact_state,
            recent_tail=list(recent_tail or []),
            active_open_loops=list(active_open_loops or []),
            evidence_refs=list(evidence_refs or []),
            restoration_confidence=restoration_confidence,
            sources=list(sources or []),
            missing=list(missing or []),
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "session_state": self.session_state.to_dict() if self.session_state else None,
            "task_state": self.task_state.to_dict() if self.task_state else None,
            "compact_state": self.compact_state.to_dict() if self.compact_state else None,
            "recent_tail": [r.to_dict() for r in self.recent_tail],
            "active_open_loops": list(self.active_open_loops),
            "evidence_refs": list(self.evidence_refs),
            "restoration_confidence": self.restoration_confidence,
            "sources": list(self.sources),
            "missing": list(self.missing),
            "metadata": dict(self.metadata),
        }
