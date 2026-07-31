from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from runtime.capability import (
    CapabilityContext,
    CapabilityPermissionGuard,
    CapabilityRequest,
    CapabilityRouter,
    PermissionDecision,
    ToolReflection,
    ToolReflectionBuilder,
    ToolResult,
)

from .action_decision import ActionDecision
from .action_governance import GovernedActionDecision
from .action_intent import ActionIntent


@dataclass(frozen=True)
class CapabilityExecutionTrace:
    """Auditable Phase 3.7.3 runtime trace for capability invocation.

    The trace records lifecycle boundaries without embedding provider/model
    identity. It is runtime evidence, not persona memory.
    """

    governance_decision: str
    capability: str | None
    validation_allowed: bool | None
    execution_status: str
    reflection_created: bool
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "governance_decision": self.governance_decision,
            "capability": self.capability,
            "validation_allowed": self.validation_allowed,
            "execution_status": self.execution_status,
            "reflection_created": self.reflection_created,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class ActionExecutionResult:
    """Lifecycle result for governed capability invocation.

    This is not a cognitive state object. It is runtime execution evidence after
    ActionPolicy has authorized an ActionIntent.
    """

    status: str
    intent: ActionIntent | None
    decision: ActionDecision | None
    request: CapabilityRequest | None
    permission: PermissionDecision | None
    tool_result: ToolResult | None
    reflection: ToolReflection | None
    governance: GovernedActionDecision | None = None
    execution_trace: CapabilityExecutionTrace | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "intent": self.intent.__dict__ if self.intent else None,
            "decision": self.decision.to_dict() if self.decision else None,
            "request": self.request.to_dict() if self.request else None,
            "permission": self.permission.to_dict() if self.permission else None,
            "tool_result": self.tool_result.to_dict() if self.tool_result else None,
            "reflection": self.reflection.to_dict() if self.reflection else None,
            "governance": self.governance.to_dict() if self.governance else None,
            "execution_trace": self.execution_trace.to_dict() if self.execution_trace else None,
        }


@dataclass
class ActionExecutor:
    """Executes only Runtime-governed ActionDecision=allow paths.

    ActionExecutor does not ask an LLM for commands. It maps approved cognitive
    intent types to CapabilityRequest envelopes, runs the existing capability
    permission guard, then routes through CapabilityRouter.
    """

    router: CapabilityRouter
    permission_guard: CapabilityPermissionGuard = field(default_factory=CapabilityPermissionGuard)
    reflection_builder: ToolReflectionBuilder = field(default_factory=ToolReflectionBuilder)
    capability_map: dict[str, tuple[str, str]] = field(default_factory=lambda: {
        "code_inspection": ("claude_code_tool", "handoff"),
        "diagnostics": ("claude_code_tool", "handoff"),
        "read_context": ("claude_code_tool", "handoff"),
        "planning": ("planning_tool", "create_plan"),
    })

    def execute_governed(
        self,
        intent: ActionIntent | None,
        governance: GovernedActionDecision | None,
    ) -> ActionExecutionResult:
        """Invoke capabilities only from an explicit ActionGovernanceLayer result."""

        decision = governance.decision if governance else None
        if intent is None or decision is None or governance is None:
            return ActionExecutionResult(
                "blocked",
                intent,
                decision,
                None,
                None,
                None,
                None,
                governance,
                self._trace("missing_governance", None, None, "blocked", False, ["governance_required"]),
            )
        if decision.decision != "allow":
            status = "skipped" if decision.decision == "ask" else "blocked"
            return ActionExecutionResult(
                status,
                intent,
                decision,
                None,
                None,
                None,
                None,
                governance,
                self._trace(decision.decision, None, None, status, False, ["governance_not_allow"]),
            )

        return self._execute_allowed(intent, decision, governance=governance)

    def execute(self, intent: ActionIntent | None, decision: ActionDecision | None) -> ActionExecutionResult:
        """Legacy Phase 3.7.3 entry kept for compatibility.

        New runtime paths should call execute_governed() so CapabilityRequest is
        created from GovernedActionDecision evidence.
        """
        if intent is None or decision is None:
            return ActionExecutionResult(
                "blocked",
                intent,
                decision,
                None,
                None,
                None,
                None,
                None,
                self._trace("missing_decision", None, None, "blocked", False, ["decision_required"]),
            )
        if decision.decision != "allow":
            status = "skipped" if decision.decision == "ask" else "blocked"
            return ActionExecutionResult(
                status,
                intent,
                decision,
                None,
                None,
                None,
                None,
                None,
                self._trace(decision.decision, None, None, status, False, ["decision_not_allow"]),
            )

        return self._execute_allowed(intent, decision, governance=None)

    def _execute_allowed(
        self,
        intent: ActionIntent,
        decision: ActionDecision,
        *,
        governance: GovernedActionDecision | None,
    ) -> ActionExecutionResult:
        request = self._request_from_intent(intent, decision, governance=governance)
        permission = self.permission_guard.decide(request)
        if not permission.allowed:
            blocked = ToolResult(
                ok=False,
                tool=request.capability,
                error=permission.reason,
                metadata={"permission": permission.to_dict(), "action_decision": decision.to_dict()},
            )
            reflection = self.reflection_builder.build(request, blocked)
            return ActionExecutionResult(
                "blocked",
                intent,
                decision,
                request,
                permission,
                blocked,
                reflection,
                governance,
                self._trace(decision.decision, request.capability, False, "blocked", True, [permission.reason]),
            )

        result = self.router.invoke(request)
        reflection = self.reflection_builder.build(request, result)
        status = "executed" if result.ok else "failed"
        return ActionExecutionResult(
            status,
            intent,
            decision,
            request,
            permission,
            result,
            reflection,
            governance,
            self._trace(decision.decision, request.capability, True, status, True, [permission.reason]),
        )

    def _request_from_intent(
        self,
        intent: ActionIntent,
        decision: ActionDecision,
        *,
        governance: GovernedActionDecision | None = None,
    ) -> CapabilityRequest:
        mapped_capability, action = self.capability_map.get(
            intent.required_capability or "",
            (intent.required_capability or "unknown_capability", "invoke"),
        )
        capability_context = CapabilityContext(
            session_id=None,
            actor="julia_runtime",
            intent=intent.intent_type,
            risk_level=intent.risk_level,
            authorization="governed_action_decision_allow" if governance else "legacy_action_decision_allow",
            parent_turn_id=None,
            metadata={
                "action_reason": intent.reason,
                "governance_reason": decision.reason,
                "governance_trace": governance.trace.to_dict() if governance else None,
            },
        )
        return CapabilityRequest(
            capability=mapped_capability,
            action=action,
            input={
                "intent_type": intent.intent_type,
                "goal": intent.goal,
                "target": intent.target,
                "required_capability": intent.required_capability,
            },
            session_id=None,
            turn_id=None,
            correlation_id=f"action_{intent.intent_type}_{intent.required_capability or 'none'}",
            metadata={
                "risk_level": intent.risk_level,
                "confidence": intent.confidence,
                "governance": governance.to_dict() if governance else {"decision": decision.to_dict()},
            },
            context=capability_context,
        )


    @staticmethod
    def _trace(
        governance_decision: str,
        capability: str | None,
        validation_allowed: bool | None,
        execution_status: str,
        reflection_created: bool,
        evidence: list[str],
    ) -> CapabilityExecutionTrace:
        return CapabilityExecutionTrace(
            governance_decision=governance_decision,
            capability=capability,
            validation_allowed=validation_allowed,
            execution_status=execution_status,
            reflection_created=reflection_created,
            evidence=evidence,
        )
