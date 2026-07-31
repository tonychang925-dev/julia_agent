from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class MutationType(str, Enum):
    CURRENT_ARC_UPDATE = "current_arc_update"
    OPEN_LOOP_CREATED = "open_loop_created"
    OPEN_LOOP_RESOLVED = "open_loop_resolved"
    COGNITIVE_MODE_CHANGED = "cognitive_mode_changed"
    TASK_PROGRESS_UPDATE = "task_progress_update"
    EVIDENCE_GAP_FOUND = "evidence_gap_found"
    QUALITY_WARNING = "quality_warning"


@dataclass(frozen=True)
class ContextMutation:
    mutation_id: str
    mutation_type: MutationType
    summary: str
    target: str | None = None
    value: str | None = None
    authority_score: float = 0.6
    source_turn_id: str | None = None
    evidence_refs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.mutation_id:
            raise ValueError("mutation_id is required")
        if not self.summary:
            raise ValueError("summary is required")
        if self.authority_score < 0 or self.authority_score > 1:
            raise ValueError("authority_score must be in [0, 1]")

    @classmethod
    def create(
        cls,
        mutation_type: MutationType | str,
        summary: str,
        *,
        target: str | None = None,
        value: str | None = None,
        authority_score: float = 0.6,
        source_turn_id: str | None = None,
        evidence_refs: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "ContextMutation":
        return cls(
            mutation_id=f"ctx_mut_{uuid4().hex}",
            mutation_type=MutationType(mutation_type),
            summary=summary,
            target=target,
            value=value,
            authority_score=authority_score,
            source_turn_id=source_turn_id,
            evidence_refs=list(evidence_refs or []),
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["mutation_type"] = self.mutation_type.value
        return data
