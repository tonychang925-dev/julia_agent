from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LoopStepTrace:
    step: int
    intent_id: str | None
    governance_decision: str
    capability: str | None
    execution_status: str
    reflection_status: str
    continuation_decision: str
    termination_reason: str | None = None
    intent_trace: dict[str, Any] | None = None
    governance_trace: dict[str, Any] | None = None
    execution_trace: dict[str, Any] | None = None
    reflection_trace: dict[str, Any] | None = None
    continuation_trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "intent_id": self.intent_id,
            "governance_decision": self.governance_decision,
            "capability": self.capability,
            "execution_status": self.execution_status,
            "reflection_status": self.reflection_status,
            "continuation_decision": self.continuation_decision,
            "termination_reason": self.termination_reason,
            "intent_trace": self.intent_trace,
            "governance_trace": self.governance_trace,
            "execution_trace": self.execution_trace,
            "reflection_trace": self.reflection_trace,
            "continuation_trace": dict(self.continuation_trace),
        }


@dataclass(frozen=True)
class CognitiveLoopTrace:
    loop_id: str
    steps: list[LoopStepTrace] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"loop_id": self.loop_id, "steps": [step.to_dict() for step in self.steps]}
