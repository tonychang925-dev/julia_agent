from __future__ import annotations

from dataclasses import dataclass, field

from .context_plan import ContextPlan
from .planner_policy import PlannerPolicy


@dataclass
class ContextPlanner:
    policy: PlannerPolicy = field(default_factory=PlannerPolicy)

    def plan(self, query: str, cognitive_mode: str = "conversation") -> ContextPlan:
        decision = self.policy.decide(query=query, cognitive_mode=cognitive_mode)
        return ContextPlan(
            query=query,
            cognitive_mode=cognitive_mode,
            intent_type=decision.intent_type,
            required_blocks=decision.required_blocks,
            optional_blocks=decision.optional_blocks,
            evidence_intents=decision.evidence_intents,
            excluded_blocks=decision.excluded_blocks,
            target_budget_tokens=decision.target_budget_tokens,
            reason=decision.reason,
            planner_confidence=decision.confidence,
        )
