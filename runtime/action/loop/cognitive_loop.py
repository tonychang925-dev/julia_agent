from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from runtime.action.action_executor import ActionExecutor
from runtime.action.action_governance import ActionGovernanceLayer, GovernedActionDecision
from runtime.action.action_intent import ActionIntent
from runtime.action.action_planner import ActionPlanner
from runtime.action.action_reflection import ActionReflectionEngine, ActionReflectionReview
from runtime.cognitive.context_compiler import JuliaContext
from runtime.memory.governance import MemoryGovernanceManager

from .continuation_policy import LoopContinuationPolicy
from .loop_context import ContextMutationAdapter, IdentityContextMutationAdapter
from .loop_state import CognitiveLoopState
from .loop_trace import CognitiveLoopTrace, LoopStepTrace
from .termination_reason import TerminationReason


@dataclass(frozen=True)
class CognitiveLoopResult:
    state: CognitiveLoopState
    trace: CognitiveLoopTrace
    final_context: JuliaContext
    last_intent: ActionIntent | None = None
    last_governance: GovernedActionDecision | None = None
    last_reflection: ActionReflectionReview | None = None

    @property
    def status(self) -> str:
        return self.state.status

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": {
                "loop_id": self.state.loop_id,
                "status": self.state.status,
                "current_step": self.state.current_step,
                "max_steps": self.state.max_steps,
                "completed_actions": list(self.state.completed_actions),
                "failed_actions": list(self.state.failed_actions),
                "pending_confirmation": self.state.pending_confirmation,
                "termination_reason": self.state.termination_reason,
                "total_risk_score": self.state.total_risk_score,
                "consecutive_same_intent": self.state.consecutive_same_intent,
            },
            "trace": self.trace.to_dict(),
            "last_intent": self.last_intent.__dict__ if self.last_intent else None,
            "last_governance": self.last_governance.to_dict() if self.last_governance else None,
            "last_reflection": self.last_reflection.to_dict() if self.last_reflection else None,
        }


@dataclass
class CognitiveLoopRuntime:
    """Bounded, auditable Cognitive Loop Runtime for Phase 3.7.5.

    This runtime performs one governed action per step. Provider/model output can
    influence planning only through ActionPlanner; continuation is decided solely
    by LoopContinuationPolicy.
    """

    planner: ActionPlanner
    governance: ActionGovernanceLayer
    executor: ActionExecutor
    reflector: ActionReflectionEngine
    continuation_policy: LoopContinuationPolicy = field(default_factory=LoopContinuationPolicy)
    memory_governance: MemoryGovernanceManager = field(default_factory=MemoryGovernanceManager)
    context_mutation_adapter: ContextMutationAdapter = field(default_factory=IdentityContextMutationAdapter)
    max_steps: int = 5
    max_failures: int = 2
    max_consecutive_same_intent: int = 2
    max_total_risk_score: float = 2.0

    def run(self, context: JuliaContext, *, loop_id: str | None = None) -> CognitiveLoopResult:
        state = CognitiveLoopState(
            loop_id=loop_id or f"loop_{uuid4().hex[:12]}",
            max_steps=self.max_steps,
            max_failures=self.max_failures,
            max_consecutive_same_intent=self.max_consecutive_same_intent,
            max_total_risk_score=self.max_total_risk_score,
        )
        trace = CognitiveLoopTrace(loop_id=state.loop_id)
        current_context = context
        last_intent: ActionIntent | None = None
        last_governance: GovernedActionDecision | None = None
        last_reflection: ActionReflectionReview | None = None

        while state.status == "running":
            if state.current_step >= state.max_steps:
                state = self._stop_state(state, "paused", TerminationReason.STEP_LIMIT.value)
                break

            intent = self.planner.plan(current_context)
            last_intent = intent
            if intent is None:
                step_trace = self._no_action_trace(state.current_step + 1)
                trace = CognitiveLoopTrace(loop_id=trace.loop_id, steps=[*trace.steps, step_trace])
                state = state.advance(
                    status="complete",
                    intent_signature=None,
                    completed=False,
                    failed=False,
                    pending_confirmation=False,
                    termination_reason=TerminationReason.NO_ACTION.value,
                    risk_score=0.0,
                )
                break

            intent_signature = self._intent_signature(intent)
            governed = self.governance.govern(intent, context=current_context)
            last_governance = governed

            execution = self.executor.execute_governed(intent, governed)
            reflection = self.reflector.reflect_with_governance(execution, governance_manager=self.memory_governance)
            last_reflection = reflection

            invariant_violation = bool(governed.trace.invariant_allowed is False)
            continuation = self.continuation_policy.decide(
                state=state,
                governance_decision=governed.decision.decision,
                execution_status=execution.status,
                reflection_status="candidate" if reflection.candidate else "none",
                intent_signature=intent_signature,
                risk_score=governed.risk.risk_score,
                invariant_violation=invariant_violation,
                goal_satisfied=self._goal_satisfied(governed.decision.decision, execution.status),
            )

            step_trace = LoopStepTrace(
                step=state.current_step + 1,
                intent_id=intent_signature,
                governance_decision=governed.decision.decision,
                capability=intent.required_capability,
                execution_status=execution.status,
                reflection_status="candidate" if reflection.candidate else "none",
                continuation_decision=continuation.decision,
                termination_reason=continuation.reason,
                intent_trace={
                    "intent_type": intent.intent_type,
                    "risk_level": intent.risk_level,
                    "required_capability": intent.required_capability,
                    "confidence": intent.confidence,
                },
                governance_trace=governed.trace.to_dict(),
                execution_trace=execution.execution_trace.to_dict() if execution.execution_trace else None,
                reflection_trace={
                    "evidence": reflection.evidence.to_dict(),
                    "candidate": reflection.candidate.__dict__ if reflection.candidate else None,
                    "governance_decision": reflection.governance_decision.__dict__ if reflection.governance_decision else None,
                    "persisted": reflection.persisted,
                },
                continuation_trace=continuation.to_dict(),
            )
            trace = CognitiveLoopTrace(loop_id=trace.loop_id, steps=[*trace.steps, step_trace])

            next_status = self._state_status(continuation.decision)
            state = state.advance(
                status=next_status,
                intent_signature=intent_signature,
                completed=execution.status == "executed",
                failed=execution.status in {"failed", "blocked"},
                pending_confirmation=continuation.decision == "ASK_USER",
                termination_reason=continuation.reason,
                risk_score=governed.risk.risk_score,
            )

            current_context = self.context_mutation_adapter.mutate_after_step(current_context, step_trace)
            if continuation.decision != "CONTINUE":
                break

        return CognitiveLoopResult(
            state=state,
            trace=trace,
            final_context=current_context,
            last_intent=last_intent,
            last_governance=last_governance,
            last_reflection=last_reflection,
        )

    @staticmethod
    def _intent_signature(intent: ActionIntent) -> str:
        return "|".join(
            str(part or "") for part in [intent.intent_type, intent.target, intent.required_capability, intent.goal]
        )

    @staticmethod
    def _goal_satisfied(governance_decision: str, execution_status: str) -> bool:
        return governance_decision == "allow" and execution_status == "executed"

    @staticmethod
    def _state_status(decision: str) -> str:
        return {
            "CONTINUE": "running",
            "COMPLETE": "complete",
            "ASK_USER": "ask_user",
            "PAUSE": "paused",
            "ABORT": "aborted",
        }.get(decision, "paused")

    @staticmethod
    def _stop_state(state: CognitiveLoopState, status: str, reason: str) -> CognitiveLoopState:
        return state.advance(
            status=status,
            intent_signature=None,
            completed=False,
            failed=False,
            pending_confirmation=False,
            termination_reason=reason,
            risk_score=0.0,
        )

    @staticmethod
    def _no_action_trace(step: int) -> LoopStepTrace:
        return LoopStepTrace(
            step=step,
            intent_id=None,
            governance_decision="none",
            capability=None,
            execution_status="not_started",
            reflection_status="none",
            continuation_decision="COMPLETE",
            termination_reason=TerminationReason.NO_ACTION.value,
            intent_trace=None,
            governance_trace=None,
            execution_trace=None,
            reflection_trace=None,
            continuation_trace={"decision": "COMPLETE", "reason": TerminationReason.NO_ACTION.value},
        )
