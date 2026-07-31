from __future__ import annotations

from dataclasses import dataclass

from .loop_state import CognitiveLoopState
from .termination_reason import TerminationReason


@dataclass(frozen=True)
class ContinuationDecision:
    decision: str
    reason: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {"decision": self.decision, "reason": self.reason}


@dataclass(frozen=True)
class LoopContinuationPolicy:
    """Runtime-only continuation policy. Provider advice is never authoritative."""

    def decide(
        self,
        *,
        state: CognitiveLoopState,
        governance_decision: str,
        execution_status: str | None,
        reflection_status: str | None,
        intent_signature: str | None,
        risk_score: float,
        context_quality_ok: bool = True,
        invariant_violation: bool = False,
        goal_satisfied: bool = False,
    ) -> ContinuationDecision:
        if invariant_violation:
            return ContinuationDecision("ABORT", TerminationReason.INVARIANT_VIOLATION.value)
        if governance_decision == "reject":
            return ContinuationDecision("ABORT", TerminationReason.GOVERNANCE_REJECT.value)
        if governance_decision == "ask":
            return ContinuationDecision("ASK_USER", TerminationReason.ASK_USER.value)
        if not context_quality_ok:
            return ContinuationDecision("PAUSE", TerminationReason.CONTEXT_QUALITY.value)

        next_step = state.current_step + 1
        next_total_risk = state.total_risk_score + float(risk_score or 0.0)
        if next_total_risk > state.max_total_risk_score:
            return ContinuationDecision("PAUSE", TerminationReason.RISK_LIMIT.value)

        if intent_signature and intent_signature == state.last_intent_signature:
            next_same_count = state.consecutive_same_intent + 1
        elif intent_signature:
            next_same_count = 1
        else:
            next_same_count = 0
        if next_same_count > state.max_consecutive_same_intent:
            return ContinuationDecision("PAUSE", TerminationReason.DUPLICATE_INTENT.value)

        if execution_status in {"failed", "blocked"}:
            next_failures = len(state.failed_actions) + (1 if intent_signature else 0)
            if next_failures >= state.max_failures:
                return ContinuationDecision("PAUSE", TerminationReason.FAILURE_LIMIT.value)
            return ContinuationDecision("PAUSE", TerminationReason.CAPABILITY_FAILURE.value)

        if goal_satisfied or execution_status == "executed":
            return ContinuationDecision("COMPLETE", TerminationReason.GOAL_SATISFIED.value)

        if next_step >= state.max_steps:
            return ContinuationDecision("PAUSE", TerminationReason.STEP_LIMIT.value)

        return ContinuationDecision("CONTINUE", None)
