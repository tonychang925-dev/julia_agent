from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ActionDecision:
    """Runtime governance decision for an ActionIntent.

    This object authorizes only the next governance state. It never executes a
    capability and never contains provider/session/runtime metadata.
    """

    decision: str
    intent_type: str
    risk_level: str
    allowed_capability: str | None
    reason: str
    confidence: float
    evidence: list[str]
    required_confirmation: bool = False
    execution_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "intent_type": self.intent_type,
            "risk_level": self.risk_level,
            "allowed_capability": self.allowed_capability,
            "reason": self.reason,
            "confidence": self.confidence,
            "evidence": list(self.evidence),
            "required_confirmation": self.required_confirmation,
            "execution_id": self.execution_id,
        }
