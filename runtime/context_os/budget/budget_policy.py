from __future__ import annotations

from dataclasses import dataclass

from runtime.context_os.planner.context_intent import ContextIntentType
from runtime.context_os.planner.context_plan import ContextPlan


@dataclass(frozen=True)
class BudgetPolicy:
    safety_margin_ratio: float = 0.05
    target_utilization_ratio: float = 0.9
    max_required_overflow_ratio: float = 1.1

    def effective_budget(self, plan: ContextPlan) -> int:
        usable = int(plan.target_budget_tokens * (1 - self.safety_margin_ratio) * self.target_utilization_ratio)
        return max(1, usable)

    def priority_boosts(self, intent_type: ContextIntentType) -> dict[str, int]:
        if intent_type == ContextIntentType.CURRENT_TASK_QUESTION:
            return {"active_task": 30, "open_loops": 25, "recent_turns": 15, "semantic_evidence": 10}
        if intent_type == ContextIntentType.PERSONAL_HISTORY_RECALL:
            return {"semantic_evidence": 35, "relationship_anchor": 20, "compact_state": 15}
        if intent_type in {ContextIntentType.IDENTITY_QUESTION, ContextIntentType.RELATIONSHIP_QUESTION}:
            return {"core_identity": 40, "relationship_anchor": 35, "semantic_evidence": 15}
        if intent_type == ContextIntentType.TECHNICAL_DEBUG:
            return {"active_task": 25, "known_failures": 25, "recent_turns": 20, "semantic_evidence": 15}
        if intent_type == ContextIntentType.EMOTIONAL_SUPPORT:
            return {"relationship_anchor": 35, "emotional_context": 25, "recent_turns": 15}
        return {}
