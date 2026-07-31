from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from runtime.context_os.execution.context_mutation import ContextMutation, MutationType


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProposalType(str, Enum):
    MEMORY_CANDIDATE = "memory_candidate"
    SESSION_STATE_UPDATE = "session_state_update"
    TASK_STATE_UPDATE = "task_state_update"
    COMPACT_CANDIDATE = "compact_candidate"
    EVIDENCE_GAP = "evidence_gap"


@dataclass(frozen=True)
class StateProposal:
    """Worker-produced state change proposal.

    Async workers are analysts only: they emit proposals with source evidence.
    Governance/policy must validate proposals before any mutation runtime applies
    them to SessionState, TaskState, or governed memory.
    """

    proposal_id: str
    proposal_type: ProposalType
    source_turn_id: str
    summary: str
    target: str
    payload: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    evidence_refs: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.proposal_id:
            raise ValueError("proposal_id is required")
        if not self.source_turn_id:
            raise ValueError("source_turn_id is required")
        if not self.summary:
            raise ValueError("summary is required")
        if not self.target:
            raise ValueError("target is required")
        if self.confidence < 0 or self.confidence > 1:
            raise ValueError("confidence must be in [0, 1]")

    @classmethod
    def create(
        cls,
        proposal_type: ProposalType | str,
        *,
        source_turn_id: str,
        summary: str,
        target: str,
        payload: dict[str, Any] | None = None,
        confidence: float = 0.0,
        evidence_refs: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "StateProposal":
        return cls(
            proposal_id=f"ctx_prop_{uuid4().hex}",
            proposal_type=ProposalType(proposal_type),
            source_turn_id=source_turn_id,
            summary=summary,
            target=target,
            payload=dict(payload or {}),
            confidence=confidence,
            evidence_refs=list(evidence_refs or []),
            metadata=dict(metadata or {}),
        )

    def to_mutation(self) -> ContextMutation:
        """Convert only proposal types that map to working-state mutations."""
        if self.proposal_type == ProposalType.TASK_STATE_UPDATE:
            mutation_type = MutationType.TASK_PROGRESS_UPDATE
        elif self.proposal_type == ProposalType.EVIDENCE_GAP:
            mutation_type = MutationType.EVIDENCE_GAP_FOUND
        elif self.proposal_type == ProposalType.SESSION_STATE_UPDATE:
            mutation_type = MutationType.OPEN_LOOP_CREATED
        else:
            raise ValueError(f"proposal cannot become direct state mutation: {self.proposal_type.value}")
        value = self.payload.get("value") or self.payload.get("next_action") or self.payload.get("goal")
        return ContextMutation.create(
            mutation_type,
            self.summary,
            target=self.target,
            value=str(value) if value is not None else None,
            authority_score=self.confidence,
            source_turn_id=self.source_turn_id,
            evidence_refs=self.evidence_refs,
            metadata={"proposal_id": self.proposal_id, "proposal_type": self.proposal_type.value, **self.metadata},
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["proposal_type"] = self.proposal_type.value
        return data
