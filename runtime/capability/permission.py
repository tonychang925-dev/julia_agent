from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .capability_context import CapabilityRequest


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    confirm_required: bool
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "confirm_required": self.confirm_required,
            "reason": self.reason,
            "metadata": self.metadata,
        }


class CapabilityPermissionGuard:
    """Minimal permission gate for Phase 3.4.2."""

    DESTRUCTIVE_WORDS = {"delete", "remove", "rm", "unlink", "erase", "删除", "移除"}

    def decide(self, request: CapabilityRequest) -> PermissionDecision:
        action_text = f"{request.action} {request.input}".lower()
        risk = request.context.risk_level if request.context else request.metadata.get("risk_level", "low")
        if risk == "high" or any(word in action_text for word in self.DESTRUCTIVE_WORDS):
            return PermissionDecision(
                allowed=False,
                confirm_required=True,
                reason="destructive_or_high_risk_capability_requires_confirmation",
                metadata={"risk_level": risk},
            )
        return PermissionDecision(
            allowed=True,
            confirm_required=False,
            reason="allowed_low_risk_capability",
            metadata={"risk_level": risk},
        )
