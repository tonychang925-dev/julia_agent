from __future__ import annotations

from dataclasses import dataclass

from .provenance_chain import ContextProvenanceChain
from .provenance_validator import ProvenanceValidator


@dataclass(frozen=True)
class ProvenanceAuditReport:
    chain: ContextProvenanceChain
    validation: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {"chain": self.chain.to_dict(), "validation": self.validation}


@dataclass(frozen=True)
class ProvenanceAuditor:
    validator: ProvenanceValidator = ProvenanceValidator()

    def audit(self, chain: ContextProvenanceChain) -> ProvenanceAuditReport:
        return ProvenanceAuditReport(chain=chain, validation=self.validator.validate_chain(chain).to_dict())
