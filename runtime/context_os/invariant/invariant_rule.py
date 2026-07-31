from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .invariant_definition import ContextInvariant, ProtectionLevel
from .invariant_type import InvariantType
from .invariant_violation import InvariantViolation, ViolationSeverity

PROTECTED_TARGET_KEYWORDS = {
    InvariantType.IDENTITY: ["identity", "identityruntime", "julia_identity"],
    InvariantType.PERSONA: ["persona", "personacontext", "persona_name"],
    InvariantType.RELATIONSHIP: ["relationship", "relationshipruntime", "relationship_context", "tony"],
    InvariantType.COGNITIVE_OWNERSHIP: ["direct_state_write", "provider_state_write", "llm_mutation", "worker_direct_mutation"],
    InvariantType.GOVERNED_MEMORY: ["governed_memory", "memoryobject", "memory_runtime", "core_identity_evidence"],
    InvariantType.PROJECT_CONTINUITY: ["project", "phase", "julia runtime", "context os"],
    InvariantType.PROVIDER_INDEPENDENCE: ["provider_identity", "identity_hash", "provider"],
}

ALLOWED_MUTATION_TARGETS = {"current_task", "open_loop", "open_loops", "progress", "task_state", "session_goal", "next_action"}


@dataclass(frozen=True)
class InvariantRule:
    invariant: ContextInvariant

    def evaluate(self, subject: Any, *, source: str) -> list[InvariantViolation]:
        target = _extract_target(subject)
        payload = _extract_payload(subject)
        evidence = _extract_evidence(subject)
        text = f"{target}\n{payload}".lower()
        violations: list[InvariantViolation] = []

        if self.invariant.invariant_type in {InvariantType.IDENTITY, InvariantType.PERSONA}:
            if _matches_any(text, PROTECTED_TARGET_KEYWORDS[self.invariant.invariant_type]):
                violations.append(self._violation(source, target, "protected_identity_or_persona_change"))

        elif self.invariant.invariant_type == InvariantType.RELATIONSHIP:
            if _matches_any(text, PROTECTED_TARGET_KEYWORDS[InvariantType.RELATIONSHIP]) and not evidence:
                violations.append(self._violation(source, target, "relationship_change_requires_evidence"))
            if "new user" in text or "第一次认识" in text or "first met" in text:
                violations.append(self._violation(source, target, "relationship_continuity_contradiction"))

        elif self.invariant.invariant_type == InvariantType.COGNITIVE_OWNERSHIP:
            if source in {"provider", "llm", "llm_mutation", "worker"} and _is_direct_state_write(target, payload):
                violations.append(self._violation(source, target, "provider_or_worker_cannot_directly_modify_julia_state"))

        elif self.invariant.invariant_type == InvariantType.GOVERNED_MEMORY:
            if any(term in text for term in ["delete core identity", "remove core identity", "core_identity_evidence", "memoryruntime.load_all"]):
                violations.append(self._violation(source, target, "governed_memory_or_core_identity_evidence_protected"))

        elif self.invariant.invariant_type == InvariantType.PROJECT_CONTINUITY:
            if "julia programming language runtime" in text and "cognitive" not in text and "context os" not in text:
                violations.append(self._violation(source, target, "project_continuity_drift_detected"))

        elif self.invariant.invariant_type == InvariantType.PROVIDER_INDEPENDENCE:
            if "identity_hash" in text and source in {"provider", "llm", "migration"}:
                violations.append(self._violation(source, target, "provider_cannot_change_identity_hash"))

        return violations

    def _violation(self, source: str, attempted_change: str, reason: str) -> InvariantViolation:
        severity = ViolationSeverity.CRITICAL if self.invariant.protection_level == ProtectionLevel.CRITICAL else ViolationSeverity.HIGH
        return InvariantViolation(
            invariant_id=self.invariant.invariant_id,
            source=source,
            attempted_change=attempted_change or self.invariant.validation_rule,
            severity=severity,
            reason=reason,
        )


def _extract_target(subject: Any) -> str:
    if isinstance(subject, dict):
        return str(subject.get("target") or subject.get("field") or subject.get("action") or "")
    return str(getattr(subject, "target", "") or getattr(subject, "block_type", "") or getattr(subject, "invariant_target", ""))


def _extract_payload(subject: Any) -> str:
    if isinstance(subject, dict):
        return str(subject.get("payload") or subject.get("value") or subject.get("content") or subject)
    if hasattr(subject, "payload"):
        return str(getattr(subject, "payload"))
    if hasattr(subject, "value"):
        return str(getattr(subject, "value"))
    if hasattr(subject, "content"):
        return str(getattr(subject, "content"))
    if hasattr(subject, "to_dict"):
        return str(subject.to_dict())
    return str(subject)


def _extract_evidence(subject: Any) -> list[str]:
    if isinstance(subject, dict):
        return list(subject.get("evidence_refs") or subject.get("evidence_ids") or subject.get("sources") or [])
    return list(getattr(subject, "evidence_refs", []) or getattr(subject, "evidence_ids", []) or getattr(subject, "source_refs", []) or [])


def _matches_any(text: str, needles: list[str]) -> bool:
    return any(needle.lower() in text for needle in needles)


def _is_direct_state_write(target: str, payload: str) -> bool:
    text = f"{target}\n{payload}".lower()
    if any(allowed in target.lower() for allowed in ALLOWED_MUTATION_TARGETS):
        return False
    protected = ["identity", "persona", "relationship", "memoryobject", "julia_state", "sessionstate", "taskstate"]
    return any(item in text for item in protected)
