from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.cognitive.context_compiler import JuliaContext
from runtime.reflection.memory_candidate import MemoryCandidate

from .action_decision import ActionDecision
from .action_executor import ActionExecutionResult, ActionExecutor
from .action_intent import ActionIntent
from .action_planner import ActionPlanner
from .action_policy import ActionPolicy
from .action_reflection import ActionReflectionEngine


@dataclass(frozen=True)
class AutonomousCognitiveLoopResult:
    """One bounded autonomous cognition cycle.

    This is orchestration evidence, not model memory and not a command stream.
    """

    status: str
    intent: ActionIntent | None
    decision: ActionDecision
    execution: ActionExecutionResult | None
    memory_candidate: MemoryCandidate | None

    def to_dict(self) -> dict[str, Any]:
        """Return a cognitive-safe loop summary.

        Raw CapabilityRequest / ToolReflection payloads may contain runtime envelope
        field names. The autonomous loop exposes only decision and outcome evidence
        needed by the cognitive layer.
        """
        return {
            "status": self.status,
            "intent": self.intent.__dict__ if self.intent else None,
            "decision": self.decision.to_dict(),
            "execution": self._execution_summary(),
            "memory_candidate": self.memory_candidate.__dict__ if self.memory_candidate else None,
        }

    def _execution_summary(self) -> dict[str, Any] | None:
        if self.execution is None:
            return None
        tool_result = self.execution.tool_result
        permission = self.execution.permission
        return {
            "status": self.execution.status,
            "capability": self.intent.required_capability if self.intent else None,
            "permission_allowed": permission.allowed if permission else None,
            "tool_ok": tool_result.ok if tool_result else None,
            "tool_error": tool_result.error if tool_result else None,
            "reflected": self.memory_candidate is not None,
        }


@dataclass
class AutonomousCognitiveLoop:
    """Minimal Phase 3.7.5 loop: plan -> decide -> execute -> reflect.

    The loop is intentionally single-cycle and bounded. It does not recursively
    call itself, does not let an LLM execute commands, and does not persist memory
    directly. Runtime components retain authority at each boundary.
    """

    planner: ActionPlanner
    policy: ActionPolicy
    executor: ActionExecutor
    reflector: ActionReflectionEngine

    def run_once(self, context: JuliaContext) -> AutonomousCognitiveLoopResult:
        intent = self.planner.plan(context)
        decision = self.policy.decide(intent)
        if intent is None:
            return AutonomousCognitiveLoopResult(
                status="no_action",
                intent=None,
                decision=decision,
                execution=None,
                memory_candidate=None,
            )
        execution = self.executor.execute(intent, decision)
        memory_candidate = self.reflector.reflect(execution)
        return AutonomousCognitiveLoopResult(
            status=self._status(decision, execution, memory_candidate),
            intent=intent,
            decision=decision,
            execution=execution,
            memory_candidate=memory_candidate,
        )

    @staticmethod
    def _status(
        decision: ActionDecision,
        execution: ActionExecutionResult,
        memory_candidate: MemoryCandidate | None,
    ) -> str:
        if decision.decision == "ask":
            return "awaiting_confirmation"
        if decision.decision == "reject":
            return "rejected"
        if execution.status == "executed":
            return "completed_with_reflection" if memory_candidate else "completed"
        if execution.status == "failed":
            return "failed_with_reflection" if memory_candidate else "failed"
        if execution.status == "blocked":
            return "blocked_with_reflection" if memory_candidate else "blocked"
        return execution.status
