from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


CompactLevel = Literal["light", "medium", "heavy", "emergency"]


@dataclass(frozen=True)
class CompactDecision:
    topic: str
    decision: str
    source_record_ids: list[str] = field(default_factory=list)
    reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CompactFailure:
    failure_type: str
    summary: str
    source_record_ids: list[str] = field(default_factory=list)
    resolved: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ExperienceCompactState:
    """Structured, source-grounded compact object.

    Compact is not a new fact source. It is a traceable cognitive state derived
    from ContextMessageRecord ranges.
    """

    compact_id: str
    title: str
    session_id: str
    period_start: str
    period_end: str
    session_goal: str
    current_task: str
    main_arc: str
    decisions: list[CompactDecision] = field(default_factory=list)
    known_failures: list[CompactFailure] = field(default_factory=list)
    open_loops: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    technical_progress: list[str] = field(default_factory=list)
    relationship_development: list[str] = field(default_factory=list)
    emotional_context: list[str] = field(default_factory=list)
    source_record_ids: list[str] = field(default_factory=list)
    source_evidence_ids: list[str] = field(default_factory=list)
    confidence: float = 0.0
    level: CompactLevel = "medium"
    created_at: str = field(default_factory=now_iso)
    schema_version: str = "experience_compact_state.v1"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.compact_id:
            raise ValueError("compact_id is required")
        if not self.session_id:
            raise ValueError("session_id is required")
        if self.confidence < 0 or self.confidence > 1:
            raise ValueError("confidence must be in [0, 1]")
        if not self.source_record_ids:
            raise ValueError("source_record_ids must not be empty")

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        period_start: str,
        period_end: str,
        source_record_ids: list[str],
        title: str = "Julia Context OS Compact",
        session_goal: str = "",
        current_task: str = "",
        main_arc: str = "",
        decisions: list[CompactDecision] | None = None,
        known_failures: list[CompactFailure] | None = None,
        open_loops: list[str] | None = None,
        next_actions: list[str] | None = None,
        technical_progress: list[str] | None = None,
        relationship_development: list[str] | None = None,
        emotional_context: list[str] | None = None,
        source_evidence_ids: list[str] | None = None,
        confidence: float = 0.75,
        level: CompactLevel = "medium",
        metadata: dict[str, Any] | None = None,
    ) -> "ExperienceCompactState":
        return cls(
            compact_id=f"ctx_compact_{uuid4().hex}",
            title=title,
            session_id=session_id,
            period_start=period_start,
            period_end=period_end,
            session_goal=session_goal,
            current_task=current_task,
            main_arc=main_arc,
            decisions=list(decisions or []),
            known_failures=list(known_failures or []),
            open_loops=list(open_loops or []),
            next_actions=list(next_actions or []),
            technical_progress=list(technical_progress or []),
            relationship_development=list(relationship_development or []),
            emotional_context=list(emotional_context or []),
            source_record_ids=list(source_record_ids),
            source_evidence_ids=list(source_evidence_ids or []),
            confidence=confidence,
            level=level,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["decisions"] = [d.to_dict() for d in self.decisions]
        data["known_failures"] = [f.to_dict() for f in self.known_failures]
        return data

    def to_context_block_text(self) -> str:
        parts = [
            f"Compact: {self.title}",
            f"Main arc: {self.main_arc}",
            f"Current task: {self.current_task}",
        ]
        if self.decisions:
            parts.append("Decisions:\n" + "\n".join(f"- {d.topic}: {d.decision}" for d in self.decisions))
        if self.open_loops:
            parts.append("Open loops:\n" + "\n".join(f"- {x}" for x in self.open_loops))
        if self.next_actions:
            parts.append("Next actions:\n" + "\n".join(f"- {x}" for x in self.next_actions))
        parts.append("Sources: " + ", ".join(self.source_record_ids))
        return "\n\n".join(p for p in parts if p.strip())
