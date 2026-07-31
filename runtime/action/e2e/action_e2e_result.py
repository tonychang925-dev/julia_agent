from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.action.action_executor import ActionExecutionResult
from runtime.action.action_governance import GovernedActionDecision
from runtime.action.action_intent import ActionIntent
from runtime.action.action_reflection import ActionReflectionReview
from runtime.cognitive.context_compiler import JuliaContext

from .action_e2e_trace import ActionE2ETrace


@dataclass(frozen=True)
class ActionE2EResult:
    final_status: str
    context: JuliaContext
    intent: ActionIntent | None
    governance: GovernedActionDecision | None
    execution: ActionExecutionResult | None
    reflection: ActionReflectionReview | None
    trace: ActionE2ETrace

    @classmethod
    def blocked(
        cls,
        *,
        context: JuliaContext,
        intent: ActionIntent | None,
        governance: GovernedActionDecision | None,
        trace: ActionE2ETrace,
        status: str,
    ) -> "ActionE2EResult":
        return cls(status, context, intent, governance, None, None, trace)

    def to_dict(self) -> dict[str, Any]:
        return {
            "final_status": self.final_status,
            "intent": self.intent.__dict__ if self.intent else None,
            "governance": self.governance.to_dict() if self.governance else None,
            "execution": self.execution.to_dict() if self.execution else None,
            "reflection": self.reflection.to_dict() if self.reflection else None,
            "trace": self.trace.to_dict(),
        }
