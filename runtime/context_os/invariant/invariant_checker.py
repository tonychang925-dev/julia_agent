from __future__ import annotations

from dataclasses import dataclass, field

from .protection_policy import InvariantDecision, ProtectionPolicy


@dataclass
class InvariantChecker:
    policy: ProtectionPolicy = field(default_factory=ProtectionPolicy.default)

    def check(self, subject: object, *, source: str) -> InvariantDecision:
        return self.policy.evaluate(subject, source=source)
