from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.memory.governance import MemoryGovernanceDecision, MemoryGovernanceManager
from runtime.reflection.memory_candidate import MemoryCandidate

from .action_executor import ActionExecutionResult


@dataclass(frozen=True)
class ActionReflectionEvidence:
    """Sanitized evidence extracted from a capability execution result.

    Evidence is intentionally narrow: it records lifecycle facts needed for
    learning/governance without copying provider/session/model metadata or raw
    tool output into memory candidates.
    """

    status: str
    intent_type: str | None
    target: str | None
    capability: str | None
    tool_ok: bool | None
    error_kind: str | None
    permission_allowed: bool | None
    trace_status: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "intent_type": self.intent_type,
            "target": self.target,
            "capability": self.capability,
            "tool_ok": self.tool_ok,
            "error_kind": self.error_kind,
            "permission_allowed": self.permission_allowed,
            "trace_status": self.trace_status,
        }


@dataclass(frozen=True)
class ActionReflectionReview:
    """Candidate plus Memory Governance precheck; never persistence."""

    evidence: ActionReflectionEvidence
    candidate: MemoryCandidate | None
    governance_decision: MemoryGovernanceDecision | None
    persisted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence": self.evidence.to_dict(),
            "candidate": self.candidate.__dict__ if self.candidate else None,
            "governance_decision": self.governance_decision.__dict__ if self.governance_decision else None,
            "persisted": self.persisted,
        }


@dataclass(frozen=True)
class ActionReflectionEngine:
    """Converts governed action outcomes into memory candidates.

    Phase 3.7.4 keeps reflection as a candidate-only boundary: action results may
    become MemoryCandidate objects, but this layer never persists MemoryObject and
    never mutates Persona or Relationship state directly.
    """

    source: str = "action_reflection"

    def extract_evidence(self, result: ActionExecutionResult) -> ActionReflectionEvidence:
        intent = result.intent
        tool_result = result.tool_result
        permission = result.permission
        trace = result.execution_trace
        return ActionReflectionEvidence(
            status=result.status,
            intent_type=intent.intent_type if intent else None,
            target=intent.target if intent else None,
            capability=intent.required_capability if intent else None,
            tool_ok=tool_result.ok if tool_result else None,
            error_kind=self._error_kind(tool_result.error if tool_result else None),
            permission_allowed=permission.allowed if permission else None,
            trace_status=trace.execution_status if trace else None,
        )

    def reflect_with_governance(
        self,
        result: ActionExecutionResult,
        *,
        governance_manager: MemoryGovernanceManager | None = None,
    ) -> ActionReflectionReview:
        evidence = self.extract_evidence(result)
        candidate = self.reflect(result)
        governance_decision = None
        if candidate is not None:
            transient_memory = candidate.to_memory_object(index=0)
            governance_decision = (governance_manager or MemoryGovernanceManager()).decide(transient_memory)
        return ActionReflectionReview(
            evidence=evidence,
            candidate=candidate,
            governance_decision=governance_decision,
            persisted=False,
        )

    def reflect(self, result: ActionExecutionResult) -> MemoryCandidate | None:
        if result.intent is None or result.decision is None:
            return None
        if result.status == "skipped":
            return None

        if result.status == "executed" and result.tool_result and result.tool_result.ok:
            return self._executed_candidate(result)
        if result.status == "failed":
            return self._failed_candidate(result)
        if result.status == "blocked" and result.permission and not result.permission.allowed:
            return self._blocked_candidate(result)
        return None

    def _executed_candidate(self, result: ActionExecutionResult) -> MemoryCandidate:
        intent = result.intent
        capability = intent.required_capability or "capability"
        target = intent.target or "current project"
        return MemoryCandidate(
            memory_type="episodic",
            summary=(
                f"Julia completed a governed action through the capability lifecycle: "
                f"{intent.intent_type} on {target} using {capability}."
            ),
            reason="governed_action_executed; useful for future project continuity and action learning",
            importance={"emotional": 0.2, "relationship": 0.45, "technical": 0.82, "recurrence": 0.72},
            confidence=min(0.95, max(0.7, float(intent.confidence or 0.0))),
            topics=self._topics(result, extra=["Action Reflection", "Capability Lifecycle"]),
            source=self.source,
        )

    def _failed_candidate(self, result: ActionExecutionResult) -> MemoryCandidate:
        intent = result.intent
        error = (result.tool_result.error if result.tool_result else None) or "unknown action failure"
        reason_tag = "capability_gap" if "not registered" in error else "action_execution_failed"
        return MemoryCandidate(
            memory_type="episodic",
            summary=(
                f"Julia action did not complete: {intent.intent_type} for "
                f"{intent.target or 'current project'} encountered {reason_tag}."
            ),
            reason=f"{reason_tag}; failure should inform future capability planning and routing decisions",
            importance={"emotional": 0.15, "relationship": 0.35, "technical": 0.78, "recurrence": 0.75},
            confidence=0.78,
            topics=self._topics(result, extra=["Action Reflection", "Capability Gap"]),
            source=self.source,
        )

    def _blocked_candidate(self, result: ActionExecutionResult) -> MemoryCandidate:
        intent = result.intent
        return MemoryCandidate(
            memory_type="episodic",
            summary=(
                f"Julia blocked a proposed action through governance before execution: "
                f"{intent.intent_type} for {intent.target or 'current project'}."
            ),
            reason="permission_guard_blocked; preserves runtime control boundaries for future action decisions",
            importance={"emotional": 0.2, "relationship": 0.4, "technical": 0.72, "recurrence": 0.82},
            confidence=0.84,
            topics=self._topics(result, extra=["Action Reflection", "Action Governance"]),
            source=self.source,
        )

    def _topics(self, result: ActionExecutionResult, *, extra: list[str]) -> list[str]:
        intent = result.intent
        topics: list[str] = []
        text = " ".join(
            part for part in [intent.goal, intent.target or "", intent.required_capability or "", intent.reason] if part
        )
        if "Julia Runtime" in text or "julia" in text.lower():
            topics.append("Julia Runtime")
        if "Persona" in text or "identity" in text.lower() or "身份" in text:
            topics.append("Identity Continuity")
        if "memory" in text.lower() or "记忆" in text:
            topics.append("Memory Runtime")
        for topic in extra:
            if topic not in topics:
                topics.append(topic)
        return topics


    @staticmethod
    def _error_kind(error: str | None) -> str | None:
        if not error:
            return None
        lowered = error.lower()
        if "not registered" in lowered:
            return "capability_gap"
        if "timeout" in lowered:
            return "timeout"
        if "permission" in lowered or "confirmation" in lowered or "risk" in lowered:
            return "permission_block"
        return "execution_failed"
