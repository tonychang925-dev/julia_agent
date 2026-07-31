from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .invariant_checker import InvariantChecker
from .protection_policy import InvariantDecision


@dataclass
class InvariantGuard:
    checker: InvariantChecker = field(default_factory=InvariantChecker)
    audit_log: list[dict[str, Any]] = field(default_factory=list)

    def pre_turn(self, projection: object, *, source: str = "projection") -> InvariantDecision:
        return self._check_and_audit(projection, source=source, stage="pre_turn")

    def post_turn(self, mutation_proposal: object, *, source: str = "llm_mutation") -> InvariantDecision:
        return self._check_and_audit(mutation_proposal, source=source, stage="post_turn")

    def check_compact(self, compact_candidate_or_request: object, *, source: str = "compact") -> InvariantDecision:
        return self._check_and_audit(compact_candidate_or_request, source=source, stage="compact")

    def check_resurrection(self, snapshot_or_context: object, *, source: str = "resurrection") -> InvariantDecision:
        return self._check_and_audit(snapshot_or_context, source=source, stage="resurrection")

    def _check_and_audit(self, subject: object, *, source: str, stage: str) -> InvariantDecision:
        decision = self.checker.check(subject, source=source)
        self.audit_log.append({"stage": stage, "source": source, **decision.to_dict()})
        return decision
