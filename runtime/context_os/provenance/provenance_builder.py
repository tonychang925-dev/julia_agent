from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from runtime.evidence import EvidenceChunk, RankedEvidence

from .provenance_chain import ContextProvenanceChain
from .provenance_record import ContextProvenanceRecord
from .provenance_type import ContextSourceType


@dataclass(frozen=True)
class ProvenanceBuilder:
    """Builds provenance records without changing source authority."""

    def current_user(self, *, text: str, block_id: str = "current_user_input", cognitive_scope: str | None = None) -> ContextProvenanceRecord:
        return ContextProvenanceRecord.create(
            context_block_id=block_id,
            source_type=ContextSourceType.CURRENT_USER.value,
            source_id="current_turn:user",
            speaker="Tony",
            authority=1.0,
            confidence=1.0,
            retrieval_reason=("direct_current_user_statement",),
            injection_reason="current_user_input",
            injected_by="conversation_runtime",
            current_task_relevance=1.0,
            cognitive_scope=cognitive_scope,
        )

    def from_ranked_evidence(
        self,
        item: RankedEvidence,
        *,
        block_id: str | None = None,
        injected_by: str = "semantic_evidence_projection",
        cognitive_scope: str | None = None,
    ) -> ContextProvenanceRecord:
        chunk = item.chunk
        return ContextProvenanceRecord.create(
            context_block_id=block_id or chunk.id,
            source_type=self._source_type(chunk),
            source_id=chunk.id,
            source_version=self._source_version(chunk),
            speaker=chunk.speaker,
            authority=item.authority,
            confidence=item.final_score,
            retrieval_reason=tuple(item.reason),
            injection_reason=self._injection_reason(chunk),
            injected_by=injected_by,
            current_task_relevance=item.semantic_similarity,
            cognitive_scope=cognitive_scope,
            inferred=False,
        )

    def exclusion(
        self,
        *,
        source_id: str,
        source_type: str,
        reason: str,
        current_scope: str,
        blocked_domains: tuple[str, ...],
        authority: float = 0.0,
        speaker: str | None = None,
    ) -> ContextProvenanceRecord:
        return ContextProvenanceRecord.create(
            context_block_id=source_id,
            source_type=source_type,
            source_id=source_id,
            speaker=speaker,
            authority=authority,
            confidence=0.0,
            retrieval_reason=(reason,),
            injection_reason="excluded_from_context",
            injected_by="memory_scope_policy",
            current_task_relevance=0.0,
            cognitive_scope=current_scope,
            decision="excluded",
            exclusion_reason=reason,
            excluded_domains=blocked_domains,
        )

    def runtime_inference(
        self,
        *,
        block_id: str,
        source_id: str,
        reason: str,
        confidence: float,
        injected_by: str,
        cognitive_scope: str | None = None,
    ) -> ContextProvenanceRecord:
        return ContextProvenanceRecord.create(
            context_block_id=block_id,
            source_type=ContextSourceType.RUNTIME_INFERENCE.value,
            source_id=source_id,
            speaker="runtime",
            authority=0.1,
            confidence=confidence,
            retrieval_reason=(reason,),
            injection_reason=reason,
            injected_by=injected_by,
            current_task_relevance=confidence,
            cognitive_scope=cognitive_scope,
            inferred=True,
        )

    def chain(self, records: list[ContextProvenanceRecord], *, chain_id: str | None = None) -> ContextProvenanceChain:
        return ContextProvenanceChain(chain_id=chain_id or f"prov_chain_{uuid4().hex}", records=tuple(records))

    @staticmethod
    def _source_type(chunk: EvidenceChunk) -> str:
        if chunk.source_type == "archive":
            return ContextSourceType.CONVERSATION_ARCHIVE.value
        if chunk.source_type == "memory":
            return ContextSourceType.GOVERNED_MEMORY.value
        if chunk.source_type == "diary":
            return ContextSourceType.CLAUDE_DIARY.value
        return ContextSourceType.RUNTIME_INFERENCE.value

    @staticmethod
    def _source_version(chunk: EvidenceChunk) -> str | None:
        if isinstance(chunk.provenance, dict):
            if chunk.provenance.get("memory_type"):
                return str(chunk.provenance.get("memory_type"))
            if chunk.provenance.get("archive_role"):
                return str(chunk.provenance.get("archive_role"))
            if chunk.provenance.get("heading"):
                return str(chunk.provenance.get("heading"))
        return None

    @staticmethod
    def _injection_reason(chunk: EvidenceChunk) -> str:
        if chunk.source_type == "archive" and chunk.speaker == "Tony":
            return "direct_previous_user_statement"
        if chunk.source_type == "archive":
            return "archive_experience_evidence"
        if chunk.source_type == "memory":
            return "governed_memory_retrieval"
        if chunk.source_type == "diary":
            return "diary_background_projection"
        return "semantic_evidence_retrieval"
