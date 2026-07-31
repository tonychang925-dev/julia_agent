from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True)
class ContextProvenanceRecord:
    provenance_id: str
    context_block_id: str
    source_type: str
    source_id: str
    source_version: str | None
    speaker: str | None
    authority: float
    confidence: float
    retrieval_reason: tuple[str, ...]
    injection_reason: str
    injected_by: str
    current_task_relevance: float
    cognitive_scope: str | None
    created_at: str
    decision: str = "included"
    exclusion_reason: str | None = None
    excluded_domains: tuple[str, ...] = field(default_factory=tuple)
    inferred: bool = False

    @classmethod
    def create(
        cls,
        *,
        context_block_id: str,
        source_type: str,
        source_id: str,
        source_version: str | None = None,
        speaker: str | None = None,
        authority: float = 0.0,
        confidence: float = 0.0,
        retrieval_reason: tuple[str, ...] = (),
        injection_reason: str = "",
        injected_by: str = "unknown_projection",
        current_task_relevance: float = 0.0,
        cognitive_scope: str | None = None,
        decision: str = "included",
        exclusion_reason: str | None = None,
        excluded_domains: tuple[str, ...] = (),
        inferred: bool = False,
    ) -> "ContextProvenanceRecord":
        return cls(
            provenance_id=f"prov_{uuid4().hex}",
            context_block_id=context_block_id,
            source_type=source_type,
            source_id=source_id,
            source_version=source_version,
            speaker=speaker,
            authority=round(float(authority or 0.0), 4),
            confidence=round(float(confidence or 0.0), 4),
            retrieval_reason=tuple(retrieval_reason),
            injection_reason=injection_reason,
            injected_by=injected_by,
            current_task_relevance=round(float(current_task_relevance or 0.0), 4),
            cognitive_scope=cognitive_scope,
            created_at=datetime.now(timezone.utc).isoformat(),
            decision=decision,
            exclusion_reason=exclusion_reason,
            excluded_domains=tuple(excluded_domains),
            inferred=inferred,
        )

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["retrieval_reason"] = list(self.retrieval_reason)
        data["excluded_domains"] = list(self.excluded_domains)
        return data
