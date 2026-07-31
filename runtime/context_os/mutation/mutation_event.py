from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4

from runtime.context_os.execution.context_mutation import MutationType


@dataclass(frozen=True)
class ContextMutationEvent:
    event_id: str
    mutation_type: MutationType
    source_turn_id: str
    evidence_refs: list[str]
    confidence: float
    reason: str
    target: str | None = None
    value: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValueError("event_id is required")
        if not self.source_turn_id:
            raise ValueError("source_turn_id is required")
        if not self.reason:
            raise ValueError("reason is required")
        if self.confidence < 0 or self.confidence > 1:
            raise ValueError("confidence must be in [0, 1]")

    @classmethod
    def create(
        cls,
        mutation_type: MutationType | str,
        *,
        source_turn_id: str,
        reason: str,
        evidence_refs: list[str] | None = None,
        confidence: float = 0.7,
        target: str | None = None,
        value: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "ContextMutationEvent":
        return cls(
            event_id=f"ctx_mut_event_{uuid4().hex}",
            mutation_type=MutationType(mutation_type),
            source_turn_id=source_turn_id,
            evidence_refs=list(evidence_refs or []),
            confidence=confidence,
            reason=reason,
            target=target,
            value=value,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["mutation_type"] = self.mutation_type.value
        return data
