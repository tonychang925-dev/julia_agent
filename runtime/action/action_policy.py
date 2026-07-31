from __future__ import annotations

from dataclasses import dataclass, field

from .action_decision import ActionDecision
from .action_intent import ActionIntent


@dataclass(frozen=True)
class ActionPolicy:
    """Authorizes ActionIntent without executing it.

    The first policy is intentionally conservative:
    - low risk + known capability can be allowed;
    - medium risk or unknown capability asks for confirmation;
    - high/critical/destructive or low-confidence intents are rejected.
    """

    confidence_threshold: float = 0.7
    known_capabilities: set[str] = field(default_factory=lambda: {
        "code_inspection",
        "planning",
        "diagnostics",
        "read_context",
    })
    ask_capabilities: set[str] = field(default_factory=lambda: {
        "code_modification",
        "file_write",
        "external_api",
    })
    prohibited_capabilities: set[str] = field(default_factory=lambda: {
        "destructive_operation",
        "credential_access",
        "external_send",
        "production_mutation",
    })

    def decide(self, intent: ActionIntent | None) -> ActionDecision:
        if intent is None:
            return ActionDecision(
                decision="reject",
                intent_type="none",
                risk_level="none",
                allowed_capability=None,
                reason="no_action_intent",
                confidence=1.0,
                evidence=["planner_returned_none"],
            )
        capability = intent.required_capability
        risk = intent.risk_level.lower().strip()
        evidence = [
            f"intent_type={intent.intent_type}",
            f"risk_level={risk}",
            f"confidence={intent.confidence:.2f}",
        ]
        if intent.confidence < self.confidence_threshold:
            return ActionDecision(
                decision="reject",
                intent_type=intent.intent_type,
                risk_level=risk,
                allowed_capability=None,
                reason="low_confidence_action_intent",
                confidence=max(0.0, min(1.0, intent.confidence)),
                evidence=[*evidence, "confidence_below_threshold"],
            )
        if risk in {"high", "critical"} or capability in self.prohibited_capabilities:
            return ActionDecision(
                decision="reject",
                intent_type=intent.intent_type,
                risk_level=risk,
                allowed_capability=None,
                reason="high_risk_or_prohibited_capability",
                confidence=0.95,
                evidence=[*evidence, "high_risk" if risk in {"high", "critical"} else "prohibited_capability"],
            )
        if risk == "medium" or capability in self.ask_capabilities:
            return ActionDecision(
                decision="ask",
                intent_type=intent.intent_type,
                risk_level=risk,
                allowed_capability=capability,
                reason="requires_confirmation_before_action",
                confidence=0.9,
                evidence=[*evidence, "medium_risk_or_write_capability"],
                required_confirmation=True,
            )
        if capability not in self.known_capabilities:
            return ActionDecision(
                decision="ask",
                intent_type=intent.intent_type,
                risk_level=risk,
                allowed_capability=capability,
                reason="unknown_capability_requires_confirmation",
                confidence=0.85,
                evidence=[*evidence, "unknown_capability"],
                required_confirmation=True,
            )
        return ActionDecision(
            decision="allow",
            intent_type=intent.intent_type,
            risk_level=risk,
            allowed_capability=capability,
            reason="low_risk_known_capability_allowed",
            confidence=0.92,
            evidence=[*evidence, "low_risk", "known_capability"],
        )
