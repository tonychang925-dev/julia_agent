from __future__ import annotations

from dataclasses import dataclass, field

from .provenance_record import ContextProvenanceRecord


@dataclass(frozen=True)
class ContextProvenanceChain:
    chain_id: str
    records: tuple[ContextProvenanceRecord, ...] = field(default_factory=tuple)

    def included(self) -> list[ContextProvenanceRecord]:
        return [record for record in self.records if record.decision == "included"]

    def excluded(self) -> list[ContextProvenanceRecord]:
        return [record for record in self.records if record.decision == "excluded"]

    def by_block(self, block_id: str) -> list[ContextProvenanceRecord]:
        return [record for record in self.records if record.context_block_id == block_id]

    def to_dict(self) -> dict[str, object]:
        return {"chain_id": self.chain_id, "records": [record.to_dict() for record in self.records]}
