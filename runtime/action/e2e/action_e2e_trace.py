from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from runtime.action.action_intent import ActionIntent
from runtime.action.action_governance import GovernedActionDecision


def _intent_id(intent: ActionIntent | None) -> str | None:
    if intent is None:
        return None
    return "|".join(str(part or "") for part in [intent.intent_type, intent.target, intent.required_capability, intent.goal])


@dataclass(frozen=True)
class GovernanceAuthorization:
    decision_id: str
    intent_id: str
    capability: str | None
    expires_at: str
    policy_version: str = "e2e-alpha-v1"
    consumed: bool = False

    @classmethod
    def issue(cls, *, intent: ActionIntent, governance: GovernedActionDecision, ttl_seconds: int = 60) -> "GovernanceAuthorization":
        return cls(
            decision_id=f"govauth_{uuid4().hex}",
            intent_id=_intent_id(intent) or "none",
            capability=intent.required_capability,
            expires_at=(datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat(),
            policy_version="e2e-alpha-v1",
            consumed=False,
        )

    def validate(self, *, intent: ActionIntent, governance: GovernedActionDecision) -> tuple[bool, str]:
        if self.consumed:
            return False, "authorization_already_consumed"
        if datetime.fromisoformat(self.expires_at) < datetime.now(timezone.utc):
            return False, "authorization_expired"
        if governance.decision.decision != "allow":
            return False, "governance_not_allow"
        if self.intent_id != _intent_id(intent):
            return False, "intent_id_mismatch"
        if self.capability != intent.required_capability:
            return False, "capability_mismatch"
        return True, "authorization_valid"

    def consume(self) -> "GovernanceAuthorization":
        return replace(self, consumed=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "intent_id": self.intent_id,
            "capability": self.capability,
            "expires_at": self.expires_at,
            "policy_version": self.policy_version,
            "consumed": self.consumed,
        }


@dataclass(frozen=True)
class ActionE2ETrace:
    context_trace: dict[str, Any] = field(default_factory=dict)
    intent_trace: dict[str, Any] = field(default_factory=dict)
    policy_trace: dict[str, Any] = field(default_factory=dict)
    authorization_trace: dict[str, Any] = field(default_factory=dict)
    execution_trace: dict[str, Any] = field(default_factory=dict)
    reflection_trace: dict[str, Any] = field(default_factory=dict)
    memory_governance_trace: dict[str, Any] = field(default_factory=dict)
    memory_candidate_created: bool = False
    memory_governance_prechecked: bool = False
    memory_persisted: bool = False
    final_status: str = "not_started"

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_trace": dict(self.context_trace),
            "intent_trace": dict(self.intent_trace),
            "policy_trace": dict(self.policy_trace),
            "authorization_trace": dict(self.authorization_trace),
            "execution_trace": dict(self.execution_trace),
            "reflection_trace": dict(self.reflection_trace),
            "memory_governance_trace": dict(self.memory_governance_trace),
            "memory_candidate_created": self.memory_candidate_created,
            "memory_governance_prechecked": self.memory_governance_prechecked,
            "memory_persisted": self.memory_persisted,
            "final_status": self.final_status,
        }
