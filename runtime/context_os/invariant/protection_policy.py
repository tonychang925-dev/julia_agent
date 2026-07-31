from __future__ import annotations

from dataclasses import dataclass, field

from .invariant_definition import ContextInvariant, ProtectionLevel
from .invariant_rule import InvariantRule
from .invariant_type import InvariantType
from .invariant_violation import InvariantViolation, ViolationSeverity


@dataclass(frozen=True)
class InvariantDecision:
    allowed: bool
    violations: list[InvariantViolation] = field(default_factory=list)
    audited: bool = True

    @property
    def blocked(self) -> bool:
        return not self.allowed

    def to_dict(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "blocked": self.blocked,
            "audited": self.audited,
            "violations": [v.to_dict() for v in self.violations],
        }


@dataclass(frozen=True)
class ProtectionPolicy:
    invariants: list[ContextInvariant] = field(default_factory=list)
    block_on: set[ViolationSeverity] = field(default_factory=lambda: {ViolationSeverity.HIGH, ViolationSeverity.CRITICAL})

    @classmethod
    def default(cls) -> "ProtectionPolicy":
        return cls(invariants=[
            ContextInvariant("identity_julia", InvariantType.IDENTITY, "Julia identity cannot be modified by provider response", ProtectionLevel.CRITICAL, "no_provider_identity_mutation"),
            ContextInvariant("persona_julia", InvariantType.PERSONA, "PersonaContext cannot be rewritten by unvalidated output", ProtectionLevel.CRITICAL, "no_direct_persona_mutation"),
            ContextInvariant("relationship_tony", InvariantType.RELATIONSHIP, "Julia/Tony relationship continuity requires evidence", ProtectionLevel.CRITICAL, "relationship_requires_evidence"),
            ContextInvariant("cognitive_ownership", InvariantType.COGNITIVE_OWNERSHIP, "LLM is not Julia and cannot directly own state", ProtectionLevel.CRITICAL, "provider_output_must_be_candidate"),
            ContextInvariant("governed_memory", InvariantType.GOVERNED_MEMORY, "Governed memory and core identity evidence cannot be deleted by compact/worker/provider", ProtectionLevel.CRITICAL, "protect_governed_memory"),
            ContextInvariant("project_continuity", InvariantType.PROJECT_CONTINUITY, "Julia Runtime project continuity cannot drift to unrelated Julia programming language runtime", ProtectionLevel.STRICT, "protect_project_semantics"),
            ContextInvariant("provider_independence", InvariantType.PROVIDER_INDEPENDENCE, "Provider migration cannot change identity hash", ProtectionLevel.CRITICAL, "provider_independent_identity"),
        ])

    def evaluate(self, subject: object, *, source: str) -> InvariantDecision:
        violations: list[InvariantViolation] = []
        for invariant in self.invariants:
            violations.extend(InvariantRule(invariant).evaluate(subject, source=source))
        allowed = not any(v.severity in self.block_on for v in violations)
        return InvariantDecision(allowed=allowed, violations=violations)
