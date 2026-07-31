from __future__ import annotations

from dataclasses import dataclass

from runtime.context_os.transcript import ProvenanceType

from .resurrection_snapshot import ResurrectionSnapshot


@dataclass
class EvidenceRestorer:
    """Restores evidence references without loading all memory."""

    filter_assistant_generated: bool = True

    def restore(self, snapshot: ResurrectionSnapshot) -> list[str]:
        refs = list(snapshot.evidence_refs)
        if self.filter_assistant_generated:
            assistant_ids = {
                r.message_id for r in snapshot.recent_tail
                if r.provenance_type == ProvenanceType.ASSISTANT_RESPONSE
            }
            refs = [ref for ref in refs if ref not in assistant_ids]
        return _dedupe(refs)


def _dedupe(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = str(value).strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            out.append(normalized)
    return out
