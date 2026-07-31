from __future__ import annotations

from dataclasses import dataclass

from runtime.context_os.execution.context_mutation import MutationType

from .context_state import ContextWorkingState
from .mutation_decision import MutationDecision
from .mutation_event import ContextMutationEvent


@dataclass
class MutationPolicy:
    min_confidence: float = 0.45

    def decide(self, *, state: ContextWorkingState, event: ContextMutationEvent) -> MutationDecision:
        if event.confidence < self.min_confidence:
            return MutationDecision(event=event, accepted=False, reason="confidence_below_threshold")
        if event.target in state.protected_fields:
            return MutationDecision(event=event, accepted=False, reason="protected_field_runtime_authority_required")
        if event.mutation_type in {
            MutationType.CURRENT_ARC_UPDATE,
            MutationType.OPEN_LOOP_CREATED,
            MutationType.OPEN_LOOP_RESOLVED,
            MutationType.COGNITIVE_MODE_CHANGED,
            MutationType.TASK_PROGRESS_UPDATE,
            MutationType.EVIDENCE_GAP_FOUND,
            MutationType.QUALITY_WARNING,
        }:
            return MutationDecision(event=event, accepted=True, reason="accepted_by_context_mutation_policy")
        return MutationDecision(event=event, accepted=False, reason="unsupported_mutation_type")
