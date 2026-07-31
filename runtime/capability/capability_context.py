from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CapabilityContext:
    """Why and under what authority a capability is invoked."""

    session_id: str | None
    actor: str
    intent: str
    risk_level: str
    authorization: str
    parent_turn_id: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "actor": self.actor,
            "intent": self.intent,
            "risk_level": self.risk_level,
            "authorization": self.authorization,
            "parent_turn_id": self.parent_turn_id,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CapabilityRequest:
    """One tool/capability invocation requested by Julia Runtime."""

    capability: str
    action: str
    input: dict[str, Any]
    session_id: str | None = None
    turn_id: int | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    context: CapabilityContext | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "action": self.action,
            "input": self.input,
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
            "context": self.context.to_dict() if self.context else None,
        }
