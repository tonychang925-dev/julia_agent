from __future__ import annotations

from dataclasses import dataclass, field

from .resurrection_snapshot import JuliaContext, ResurrectionSnapshot


@dataclass(frozen=True)
class ResurrectionValidationResult:
    restored: bool
    sources: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "restored": self.restored,
            "sources": list(self.sources),
            "missing": list(self.missing),
            "confidence": self.confidence,
            "warnings": list(self.warnings),
        }


@dataclass
class ResurrectionValidator:
    min_confidence: float = 0.5

    def validate(self, snapshot: ResurrectionSnapshot, context: JuliaContext) -> ResurrectionValidationResult:
        missing = list(snapshot.missing)
        warnings: list[str] = []
        if not context.current_task:
            warnings.append("current_task_missing")
        if not context.open_loops and not context.next_actions:
            warnings.append("continuity_actions_missing")
        if not context.evidence_refs:
            warnings.append("evidence_refs_missing")
        restored = bool(context.session_id) and context.confidence >= self.min_confidence and "session_state" not in missing
        return ResurrectionValidationResult(
            restored=restored,
            sources=list(context.sources),
            missing=missing,
            confidence=context.confidence,
            warnings=warnings,
        )
