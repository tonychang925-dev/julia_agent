from __future__ import annotations

from dataclasses import dataclass, field

from .context_reconstructor import ContextReconstructor
from .resurrection_loader import ResurrectionLoader
from .resurrection_request import ResurrectionRequest
from .resurrection_snapshot import JuliaContext, ResurrectionSnapshot
from .resurrection_validator import ResurrectionValidationResult, ResurrectionValidator


@dataclass(frozen=True)
class ResurrectionResult:
    restored: bool
    snapshot: ResurrectionSnapshot
    context: JuliaContext
    validation: ResurrectionValidationResult

    def to_dict(self) -> dict[str, object]:
        return {
            "restored": self.restored,
            "snapshot": self.snapshot.to_dict(),
            "context": self.context.to_dict(),
            "validation": self.validation.to_dict(),
            "sources": list(self.validation.sources),
            "missing": list(self.validation.missing),
            "confidence": self.validation.confidence,
        }


@dataclass
class SessionResurrectionRuntime:
    loader: ResurrectionLoader
    reconstructor: ContextReconstructor = field(default_factory=ContextReconstructor)
    validator: ResurrectionValidator = field(default_factory=ResurrectionValidator)

    def resurrect(self, request: ResurrectionRequest) -> ResurrectionResult:
        snapshot = self.loader.load(request)
        context = self.reconstructor.reconstruct(snapshot)
        validation = self.validator.validate(snapshot, context)
        return ResurrectionResult(
            restored=validation.restored,
            snapshot=snapshot,
            context=context,
            validation=validation,
        )
