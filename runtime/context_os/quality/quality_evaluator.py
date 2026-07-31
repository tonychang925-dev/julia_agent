from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from runtime.context_os.planner.context_intent import ContextIntentType
from runtime.context_os.planner.context_plan import ContextPlan
from .context_quality import ContextQuality
from .quality_policy import ContextQualityPolicy


def _get_block_attr(block: Any, name: str, default: Any = None) -> Any:
    if isinstance(block, dict):
        return block.get(name, default)
    return getattr(block, name, default)


@dataclass
class ContextQualityEvaluator:
    policy: ContextQualityPolicy = field(default_factory=ContextQualityPolicy)

    def evaluate(self, *, plan: ContextPlan, blocks: list[Any]) -> ContextQuality:
        included = [b for b in blocks if _get_block_attr(b, "included", True)]
        target = max(1, plan.target_budget_tokens)
        estimated = sum(int(_get_block_attr(b, "estimated_tokens", 0) or 0) for b in included)
        budget_utilization = min(1.0, estimated / target)

        block_types = {str(_get_block_attr(b, "block_type", "")) for b in included}
        identity_coverage = 1.0 if "core_identity" in block_types else 0.0
        relationship_coverage = 1.0 if "relationship_anchor" in block_types else 0.0
        task_coverage = 1.0 if "active_task" in block_types or "session_state" in block_types else 0.0

        evidence_blocks = [b for b in included if str(_get_block_attr(b, "block_type", "")) in {"semantic_evidence", "compact_state", "recent_turns"}]
        evidence_count = sum(len(_get_block_attr(b, "evidence_ids", []) or []) or (1 if str(_get_block_attr(b, "block_type", "")) == "semantic_evidence" else 0) for b in evidence_blocks)
        authorities = [float(_get_block_attr(b, "authority_score", 0.0) or 0.0) for b in evidence_blocks]
        highest_authority = max(authorities, default=0.0)
        low_authority_count = sum(1 for value in authorities if value <= self.policy.low_authority_threshold)
        assistant_count = sum(
            1
            for b in evidence_blocks
            if "assistant" in str(_get_block_attr(b, "provenance_type", "")).lower()
            or "assistant" in str(_get_block_attr(b, "source", "")).lower()
        )
        assistant_ratio = assistant_count / len(evidence_blocks) if evidence_blocks else 0.0

        evidence_confidence = highest_authority
        if evidence_count == 0:
            evidence_confidence = 0.0
        elif assistant_ratio > self.policy.high_assistant_ratio:
            evidence_confidence = min(evidence_confidence, 0.35)

        conflict_count = self._estimate_conflicts(evidence_blocks)
        hallucination_risk = self._estimate_hallucination_risk(
            intent_type=plan.intent_type,
            evidence_count=evidence_count,
            highest_authority=highest_authority,
            assistant_ratio=assistant_ratio,
            conflict_count=conflict_count,
        )

        draft = ContextQuality(
            plan_id=plan.plan_id,
            identity_coverage=identity_coverage,
            relationship_coverage=relationship_coverage,
            task_coverage=task_coverage,
            evidence_confidence=evidence_confidence,
            budget_utilization=budget_utilization,
            hallucination_risk=hallucination_risk,
            highest_authority=highest_authority,
            evidence_count=evidence_count,
            low_authority_evidence_count=low_authority_count,
            assistant_generated_ratio=assistant_ratio,
            conflict_count=conflict_count,
            pass_gate=True,
            warnings=[],
        )
        return self.policy.apply_gate(intent_type=plan.intent_type, draft=draft)

    @staticmethod
    def _estimate_conflicts(evidence_blocks: list[Any]) -> int:
        topics: dict[str, set[str]] = {}
        for block in evidence_blocks:
            for topic in _get_block_attr(block, "conflict_topics", []) or []:
                topics.setdefault(str(topic), set()).add(str(_get_block_attr(block, "content", "")))
        return sum(1 for values in topics.values() if len(values) > 1)

    @staticmethod
    def _estimate_hallucination_risk(
        *,
        intent_type: ContextIntentType,
        evidence_count: int,
        highest_authority: float,
        assistant_ratio: float,
        conflict_count: int,
    ) -> float:
        risk = 0.2
        if intent_type == ContextIntentType.PERSONAL_HISTORY_RECALL:
            risk += 0.25
        if evidence_count == 0:
            risk += 0.45
        if highest_authority <= 0.3:
            risk += 0.35
        elif highest_authority >= 0.8:
            risk -= 0.2
        if assistant_ratio > 0.5:
            risk += 0.25
        if conflict_count > 0:
            risk += 0.2
        return max(0.0, min(1.0, risk))
