from __future__ import annotations

from dataclasses import dataclass

from runtime.context_os.planner.context_intent import ContextIntentType
from runtime.context_os.planner.context_plan import ContextPlan

from .projection_block import ContextProjectionBlock


@dataclass
class RelationshipProjection:
    def project(self, plan: ContextPlan, content: str | None) -> list[ContextProjectionBlock]:
        if not content:
            return []
        required = plan.intent_type in {
            ContextIntentType.IDENTITY_QUESTION,
            ContextIntentType.RELATIONSHIP_QUESTION,
            ContextIntentType.PERSONAL_HISTORY_RECALL,
            ContextIntentType.EMOTIONAL_SUPPORT,
            ContextIntentType.PRIVATE_VOICE_CONTINUITY,
        }
        return [ContextProjectionBlock(
            block_id="projection_relationship_anchor",
            block_type="relationship_anchor",
            source_refs=["relationship_anchor"],
            content=content,
            priority=96,
            authority=0.95,
            required=required,
            metadata={"projection": "relationship", "reason": "relationship_anchor_for_intent"},
        )]
