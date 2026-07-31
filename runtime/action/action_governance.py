from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from runtime.context_os.invariant import InvariantGuard

from .action_decision import ActionDecision
from .action_intent import ActionIntent
from .action_policy import ActionPolicy


@dataclass(frozen=True)
class ActionRiskEvaluation:
    risk_level: str
    risk_score: float
    reasons: list[str] = field(default_factory=list)
    protected_context: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "reasons": list(self.reasons),
            "protected_context": self.protected_context,
        }


@dataclass(frozen=True)
class ActionPolicyTrace:
    intent_type: str
    requested_capability: str | None
    risk: ActionRiskEvaluation
    invariant_allowed: bool
    decision: str
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "intent_type": self.intent_type,
            "requested_capability": self.requested_capability,
            "risk": self.risk.to_dict(),
            "invariant_allowed": self.invariant_allowed,
            "decision": self.decision,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class GovernedActionDecision:
    decision: ActionDecision
    risk: ActionRiskEvaluation
    trace: ActionPolicyTrace
    executable: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "decision": self.decision.to_dict(),
            "risk": self.risk.to_dict(),
            "trace": self.trace.to_dict(),
            "executable": self.executable,
        }


@dataclass
class ActionRiskEvaluator:
    """Evaluates action risk before capability runtime."""

    destructive_terms: set[str] = field(default_factory=lambda: {"delete", "remove", "rm", "unlink", "erase", "删除", "移除", "覆盖", "overwrite"})
    protected_terms: set[str] = field(default_factory=lambda: {"identity", "persona", "relationship", "production", "credential", "token", "secret"})

    def evaluate(self, intent: ActionIntent | None, *, context: Any | None = None) -> ActionRiskEvaluation:
        if intent is None:
            return ActionRiskEvaluation("none", 1.0, ["no_intent"], protected_context=False)
        text = f"{intent.intent_type} {intent.goal} {intent.target} {intent.required_capability} {intent.reason}".lower()
        reasons = [f"intent_risk={intent.risk_level}"]
        score = {"low": 0.2, "medium": 0.55, "high": 0.9, "critical": 1.0}.get(intent.risk_level.lower(), 0.6)
        if intent.required_capability in {"code_modification", "file_write", "external_api"}:
            score = max(score, 0.6)
            reasons.append("write_or_external_capability")
        if intent.required_capability in {"destructive_operation", "credential_access", "external_send", "production_mutation"}:
            score = max(score, 0.95)
            reasons.append("prohibited_capability")
        if any(term in text for term in self.destructive_terms):
            score = max(score, 0.95)
            reasons.append("destructive_language")
        protected = any(term in text for term in self.protected_terms)
        if protected:
            score = max(score, 0.8)
            reasons.append("protected_context")
        if intent.confidence < 0.7:
            score = max(score, 0.75)
            reasons.append("low_intent_confidence")
        risk_level = "low"
        if score >= 0.9:
            risk_level = "high"
        elif score >= 0.5:
            risk_level = "medium"
        return ActionRiskEvaluation(risk_level=risk_level, risk_score=round(score, 4), reasons=reasons, protected_context=protected)


@dataclass
class ActionGovernanceLayer:
    """ActionIntent -> governed allow/ask/reject decision. No execution authority."""

    policy: ActionPolicy = field(default_factory=ActionPolicy)
    risk_evaluator: ActionRiskEvaluator = field(default_factory=ActionRiskEvaluator)
    invariant_guard: InvariantGuard = field(default_factory=InvariantGuard)

    def govern(self, intent: ActionIntent | None, *, context: Any | None = None) -> GovernedActionDecision:
        risk = self.risk_evaluator.evaluate(intent, context=context)
        invariant_subject = self._invariant_subject(intent)
        invariant_decision = self.invariant_guard.post_turn(invariant_subject, source="action_governance")

        if intent is None:
            decision = self.policy.decide(None)
        elif invariant_decision.blocked:
            decision = ActionDecision(
                decision="reject",
                intent_type=intent.intent_type,
                risk_level=risk.risk_level,
                allowed_capability=None,
                reason="invariant_guard_blocked_action_intent",
                confidence=0.95,
                evidence=["invariant_guard_blocked", *[v.reason for v in invariant_decision.violations]],
            )
        elif risk.risk_level == "high":
            decision = ActionDecision(
                decision="reject",
                intent_type=intent.intent_type,
                risk_level=risk.risk_level,
                allowed_capability=None,
                reason="action_risk_evaluation_rejected_high_risk",
                confidence=0.95,
                evidence=[*risk.reasons, "risk_score>=0.9"],
            )
        elif risk.risk_level == "medium":
            decision = ActionDecision(
                decision="ask",
                intent_type=intent.intent_type,
                risk_level=risk.risk_level,
                allowed_capability=intent.required_capability,
                reason="action_risk_requires_confirmation",
                confidence=0.9,
                evidence=[*risk.reasons, "medium_risk_requires_confirmation"],
                required_confirmation=True,
            )
        else:
            decision = self.policy.decide(intent)

        trace = ActionPolicyTrace(
            intent_type=decision.intent_type,
            requested_capability=intent.required_capability if intent else None,
            risk=risk,
            invariant_allowed=invariant_decision.allowed,
            decision=decision.decision,
            evidence=list(decision.evidence),
        )
        return GovernedActionDecision(decision=decision, risk=risk, trace=trace, executable=False)

    @staticmethod
    def _invariant_subject(intent: ActionIntent | None) -> dict[str, object]:
        if intent is None:
            return {"target": "none", "payload": {}}
        protected_targets = {"identity", "persona", "relationship", "relationship_context", "identity_hash", "memoryobject"}
        target = intent.target if (intent.target or "").lower() in protected_targets else intent.intent_type
        return {
            "target": target,
            "payload": {
                "intent_type": intent.intent_type,
                "goal": intent.goal,
                "required_capability": intent.required_capability,
                "reason": intent.reason,
            },
            "evidence_refs": ["action_intent_governance"],
        }
