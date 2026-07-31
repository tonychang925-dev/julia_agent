from __future__ import annotations

from dataclasses import dataclass

from runtime.context_os.planner.context_intent import ContextIntentType
from .context_quality import ContextQuality


@dataclass(frozen=True)
class ContextQualityPolicy:
    identity_min_for_identity_questions: float = 0.8
    evidence_min_for_historical_fact: float = 0.6
    low_authority_threshold: float = 0.3
    max_budget_utilization: float = 0.92
    high_assistant_ratio: float = 0.5

    def apply_gate(self, *, intent_type: ContextIntentType, draft: ContextQuality) -> ContextQuality:
        warnings = list(draft.warnings)
        pass_gate = draft.pass_gate

        if intent_type in {ContextIntentType.IDENTITY_QUESTION, ContextIntentType.RELATIONSHIP_QUESTION}:
            if draft.identity_coverage < self.identity_min_for_identity_questions:
                warnings.append("identity_coverage_below_required_threshold")
                pass_gate = False
            if draft.relationship_coverage < self.identity_min_for_identity_questions:
                warnings.append("relationship_coverage_below_required_threshold")
                pass_gate = False

        if intent_type == ContextIntentType.PERSONAL_HISTORY_RECALL:
            if draft.evidence_confidence < self.evidence_min_for_historical_fact:
                warnings.append("historical_fact_evidence_confidence_low")
            if draft.highest_authority <= self.low_authority_threshold:
                warnings.append("highest_authority_is_low_assistant_or_inference_only")
                pass_gate = False

        if draft.budget_utilization > self.max_budget_utilization:
            warnings.append("budget_utilization_too_high")

        if draft.assistant_generated_ratio > self.high_assistant_ratio:
            warnings.append("assistant_generated_evidence_dominates")

        if draft.conflict_count > 0:
            warnings.append("context_conflict_detected")

        hallucination_risk = draft.hallucination_risk
        if draft.highest_authority <= self.low_authority_threshold and draft.evidence_count > 0:
            hallucination_risk = max(hallucination_risk, 0.85)
        if draft.evidence_count == 0 and intent_type == ContextIntentType.PERSONAL_HISTORY_RECALL:
            hallucination_risk = max(hallucination_risk, 0.9)
            warnings.append("historical_query_has_no_evidence")
            pass_gate = False

        return ContextQuality(
            plan_id=draft.plan_id,
            identity_coverage=draft.identity_coverage,
            relationship_coverage=draft.relationship_coverage,
            task_coverage=draft.task_coverage,
            evidence_confidence=draft.evidence_confidence,
            budget_utilization=draft.budget_utilization,
            hallucination_risk=min(1.0, hallucination_risk),
            highest_authority=draft.highest_authority,
            evidence_count=draft.evidence_count,
            low_authority_evidence_count=draft.low_authority_evidence_count,
            assistant_generated_ratio=draft.assistant_generated_ratio,
            conflict_count=draft.conflict_count,
            pass_gate=pass_gate,
            warnings=warnings,
        )
