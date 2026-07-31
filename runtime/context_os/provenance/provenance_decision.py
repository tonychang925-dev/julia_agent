from __future__ import annotations

from dataclasses import dataclass, field

from .provenance_record import ContextProvenanceRecord


@dataclass(frozen=True)
class ProvenanceValidationDecision:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    records_checked: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "records_checked": self.records_checked,
        }


@dataclass(frozen=True)
class ContextProvenanceDecision:
    record: ContextProvenanceRecord
    decision: str
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {"record": self.record.to_dict(), "decision": self.decision, "reason": self.reason}
