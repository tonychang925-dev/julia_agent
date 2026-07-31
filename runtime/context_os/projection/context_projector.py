from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from runtime.context_os.budget import ContextBlock
from runtime.context_os.compact import ExperienceCompactState
from runtime.context_os.evidence import SemanticEvidenceIntegration
from runtime.context_os.planner.context_plan import ContextPlan
from runtime.context_os.session import SessionResurrectionEngine, SessionSnapshot
from runtime.context_os.state import JuliaSessionState, JuliaTaskState, SessionTaskStateProjection
from runtime.context_os.transcript.message_record import ContextMessageRecord

from .compact_projection import CompactProjection
from .evidence_projection import EvidenceProjection
from .identity_projection import IdentityProjection
from .recent_tail_projection import RecentTailProjection
from .relationship_projection import RelationshipProjection
from .session_projection import SessionProjection
from .task_projection import TaskProjection


@dataclass(frozen=True)
class ContextProjectionInputs:
    identity: str | None = None
    relationship: str | None = None
    current_task: str | None = None
    session_state: JuliaSessionState | None = None
    task_state: JuliaTaskState | None = None
    session_snapshot: SessionSnapshot | None = None
    compacts: list[ExperienceCompactState] = field(default_factory=list)
    preserved_records: list[ContextMessageRecord] = field(default_factory=list)
    recent_records: list[ContextMessageRecord] = field(default_factory=list)
    semantic_evidence: SemanticEvidenceIntegration | None = None
    extra_blocks: list[ContextBlock] = field(default_factory=list)


@dataclass(frozen=True)
class ContextProjectionResult:
    blocks: list[ContextBlock]
    trace: dict[str, Any]


@dataclass
class ContextProjector:
    resurrection: SessionResurrectionEngine = field(default_factory=SessionResurrectionEngine)
    recent_tail_max_records: int = 8

    def project(self, *, plan: ContextPlan, inputs: ContextProjectionInputs) -> ContextProjectionResult:
        blocks: list[ContextBlock] = []
        blocks.extend(b.to_context_block() for b in IdentityProjection().project(inputs.identity))
        blocks.extend(b.to_context_block() for b in RelationshipProjection().project(plan, inputs.relationship))
        blocks.extend(b.to_context_block() for b in TaskProjection().project(inputs.current_task))
        blocks.extend(SessionTaskStateProjection().project(session_state=inputs.session_state, task_state=inputs.task_state))
        blocks.extend(b.to_context_block() for b in CompactProjection().project(inputs.compacts))
        blocks.extend(SessionProjection(self.resurrection).project(
            snapshot=inputs.session_snapshot,
            compacts=inputs.compacts,
            preserved_records=inputs.preserved_records,
        ))
        blocks.extend(b.to_context_block() for b in RecentTailProjection(self.recent_tail_max_records).project(inputs.recent_records))
        blocks.extend(EvidenceProjection(inputs.semantic_evidence).project(plan))
        blocks.extend(inputs.extra_blocks)
        return ContextProjectionResult(
            blocks=blocks,
            trace={
                "included": [str(b.block_type) for b in blocks],
                "block_ids": [b.block_id for b in blocks],
                "source_refs": [ref for b in blocks for ref in b.source_refs],
                "evidence_refs": [eid for b in blocks for eid in b.evidence_ids],
                "reason": "authority_aware_cognitive_world_projection",
            },
        )
