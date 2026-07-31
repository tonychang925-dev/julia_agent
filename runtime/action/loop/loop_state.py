from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class CognitiveLoopState:
    loop_id: str
    status: str = "running"
    current_step: int = 0
    max_steps: int = 5
    completed_actions: list[str] = field(default_factory=list)
    failed_actions: list[str] = field(default_factory=list)
    pending_confirmation: bool = False
    termination_reason: str | None = None
    max_failures: int = 2
    max_consecutive_same_intent: int = 2
    max_total_risk_score: float = 2.0
    total_risk_score: float = 0.0
    last_intent_signature: str | None = None
    consecutive_same_intent: int = 0

    def advance(
        self,
        *,
        status: str,
        intent_signature: str | None,
        completed: bool,
        failed: bool,
        pending_confirmation: bool,
        termination_reason: str | None,
        risk_score: float = 0.0,
    ) -> "CognitiveLoopState":
        same_count = self.consecutive_same_intent
        if intent_signature is None:
            same_count = 0
        elif intent_signature == self.last_intent_signature:
            same_count += 1
        else:
            same_count = 1

        completed_actions = list(self.completed_actions)
        failed_actions = list(self.failed_actions)
        if completed and intent_signature:
            completed_actions.append(intent_signature)
        if failed and intent_signature:
            failed_actions.append(intent_signature)

        return replace(
            self,
            status=status,
            current_step=self.current_step + 1,
            completed_actions=completed_actions,
            failed_actions=failed_actions,
            pending_confirmation=pending_confirmation,
            termination_reason=termination_reason,
            total_risk_score=round(self.total_risk_score + float(risk_score or 0.0), 4),
            last_intent_signature=intent_signature,
            consecutive_same_intent=same_count,
        )
