from __future__ import annotations

from dataclasses import dataclass, field, replace

from runtime.action.action_executor import ActionExecutor
from runtime.action.action_governance import ActionGovernanceLayer
from runtime.action.action_planner import ActionPlanner
from runtime.action.action_reflection import ActionReflectionEngine
from runtime.cognitive.context_compiler import ContextCompiler, ContextPolicy, RuntimeEnvelope
from runtime.memory.governance import MemoryGovernanceManager
from pathlib import Path

from .action_e2e_request import ActionE2ERequest
from .action_e2e_result import ActionE2EResult
from .action_e2e_trace import ActionE2ETrace, GovernanceAuthorization


@dataclass
class ActionE2ERuntime:
    project_root: Path
    executor: ActionExecutor
    planner: ActionPlanner = field(default_factory=ActionPlanner)
    governance: ActionGovernanceLayer = field(default_factory=ActionGovernanceLayer)
    reflection: ActionReflectionEngine = field(default_factory=ActionReflectionEngine)
    memory_governance: MemoryGovernanceManager = field(default_factory=MemoryGovernanceManager)
    context_compiler: ContextCompiler | None = None

    def __post_init__(self) -> None:
        if self.context_compiler is None:
            self.context_compiler = ContextCompiler(self.project_root, policy=ContextPolicy(memory_limit=5))

    def run(self, request: ActionE2ERequest) -> ActionE2EResult:
        if request.alpha_mode and request.allow_side_effects:
            raise ValueError("E2E Alpha side effects disabled")
        if request.max_action_steps != 1:
            raise ValueError("E2E Alpha supports exactly one action step")

        envelope = RuntimeEnvelope(
            session_id=request.session_id,
            turn_id=request.turn_id,
            provider="e2e_alpha",
            backend="local_fixture",
            timestamp="2026-07-29T00:00:00Z",
            latency_target_ms=1500,
        )
        cognitive_turn = self.context_compiler.compile(
            envelope,
            request.text,
            conversation_context={},
            user_intent={"mode": request.mode, "source": "e2e_alpha"},
        )
        context = cognitive_turn.julia_context
        trace = ActionE2ETrace(
            context_trace={
                "session_id": request.session_id,
                "turn_id": request.turn_id,
                "cognitive_mode": context.cognitive_mode.mode.name,
                "memory_count": len(context.memory_context),
                "alpha_mode": request.alpha_mode,
                "allow_side_effects": request.allow_side_effects,
                "max_action_steps": request.max_action_steps,
            }
        )

        intent = self.planner.plan(context)
        trace = replace(trace, intent_trace={"intent": intent.__dict__ if intent else None, "executable": False})
        governed = self.governance.govern(intent, context=context)
        trace = replace(trace, policy_trace=governed.to_dict())

        if intent is None:
            trace = replace(trace, final_status="no_action")
            return ActionE2EResult.blocked(context=context, intent=None, governance=governed, trace=trace, status="no_action")

        if governed.decision.decision != "allow":
            trace = replace(trace, final_status=governed.decision.decision)
            return ActionE2EResult.blocked(context=context, intent=intent, governance=governed, trace=trace, status=governed.decision.decision)

        authorization = GovernanceAuthorization.issue(intent=intent, governance=governed)
        auth_ok, auth_reason = authorization.validate(intent=intent, governance=governed)
        authorization = authorization.consume() if auth_ok else authorization
        trace = replace(trace, authorization_trace={"ok": auth_ok, "reason": auth_reason, "authorization": authorization.to_dict()})
        if not auth_ok:
            trace = replace(trace, final_status="authorization_blocked")
            return ActionE2EResult.blocked(context=context, intent=intent, governance=governed, trace=trace, status="authorization_blocked")

        execution = self.executor.execute_governed(intent, governed)
        reflection = self.reflection.reflect_with_governance(execution, governance_manager=self.memory_governance)
        final_status = "completed" if execution.status == "executed" else execution.status
        trace = replace(
            trace,
            execution_trace=execution.execution_trace.to_dict() if execution.execution_trace else {},
            reflection_trace={"evidence": reflection.evidence.to_dict(), "candidate": reflection.candidate.__dict__ if reflection.candidate else None, "persisted": reflection.persisted},
            memory_governance_trace=reflection.governance_decision.__dict__ if reflection.governance_decision else {},
            memory_candidate_created=reflection.candidate is not None,
            memory_governance_prechecked=reflection.governance_decision is not None,
            memory_persisted=reflection.persisted,
            final_status=final_status,
        )
        return ActionE2EResult(final_status, context, intent, governed, execution, reflection, trace)
