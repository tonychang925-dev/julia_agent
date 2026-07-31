from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.context_os.budget.context_block import ContextBlock
from runtime.context_os.planner.context_plan import ContextPlan
from runtime.evidence.semantic_retriever import SemanticContextRetriever


@dataclass
class SemanticEvidenceIntegration:
    """Build Context OS evidence blocks from semantic retrieval results.

    This adapter keeps retrieval as a Context OS tool: the planner declares
    abstract evidence intents, this layer retrieves source-grounded evidence,
    filters low-authority assistant-generated claims when requested, and returns
    a model-facing ContextBlock with traceable evidence ids and source refs.
    """

    retriever: Any | None = None
    project_root: str | None = None
    default_limit: int = 8

    def __post_init__(self) -> None:
        if self.retriever is None:
            if self.project_root is None:
                raise ValueError("project_root or retriever is required")
            self.retriever = SemanticContextRetriever(self.project_root)
        if self.default_limit <= 0:
            raise ValueError("default_limit must be positive")

    def build_blocks(self, plan: ContextPlan, *, limit: int | None = None) -> list[ContextBlock]:
        if not plan.evidence_intents:
            return []

        ranked = list(self.retriever.retrieve(plan.query, limit=limit or self.default_limit))
        filter_assistant = "assistant_generated_claims" in set(plan.excluded_blocks)
        if filter_assistant:
            ranked = [item for item in ranked if not self._is_assistant_generated(item)]

        if not ranked:
            return [self._empty_block(plan, filter_assistant=filter_assistant)]

        content = self._format_prompt_block(ranked)
        evidence_ids = [item.chunk.id for item in ranked]
        source_refs = [self._source_ref(item) for item in ranked]
        authority_score = max(float(item.authority) for item in ranked)
        priority = self._priority(plan, authority_score)
        metadata = {
            "queried": True,
            "hit_count": len(ranked),
            "query": plan.query,
            "intent_type": plan.intent_type.value,
            "evidence_intents": [intent.value for intent in plan.evidence_intents],
            "excluded_blocks": list(plan.excluded_blocks),
            "assistant_generated_filtered": filter_assistant,
            "sources": [self._source_metadata(item) for item in ranked],
        }
        return [ContextBlock(
            block_id=f"semantic_evidence_{plan.plan_id}",
            block_type="semantic_evidence",
            priority=priority,
            content=content,
            required="semantic_evidence" in plan.required_blocks,
            source_refs=source_refs,
            evidence_ids=evidence_ids,
            authority_score=round(authority_score, 4),
            metadata=metadata,
        )]

    @staticmethod
    def _format_prompt_block(ranked: list[Any]) -> str:
        blocks = "\n\n".join(item.chunk.to_prompt_block() for item in ranked)
        return (
            "Semantic Cognitive Evidence "
            "(authority-ranked; answer from these source facts before model priors):\n"
            f"{blocks}"
        )

    @staticmethod
    def _source_ref(item: Any) -> str:
        chunk = item.chunk
        location = chunk.source_path or chunk.session_id or chunk.id
        if chunk.turn_id is not None:
            location = f"{location}:turn-{chunk.turn_id}"
        return f"{chunk.source_type}:{location}"

    @staticmethod
    def _source_metadata(item: Any) -> dict[str, object]:
        chunk = item.chunk
        return {
            "id": chunk.id,
            "source_type": chunk.source_type,
            "source_path": chunk.source_path,
            "session_id": chunk.session_id,
            "turn_id": chunk.turn_id,
            "timestamp": chunk.timestamp,
            "speaker": chunk.speaker,
            "authority": float(item.authority),
            "semantic_similarity": float(item.semantic_similarity),
            "memory_importance": float(item.memory_importance),
            "recency": float(item.recency),
            "final_score": float(item.final_score),
            "reason": list(item.reason),
            "provenance": dict(chunk.provenance),
        }

    @staticmethod
    def _is_assistant_generated(item: Any) -> bool:
        chunk = item.chunk
        speaker = (chunk.speaker or "").strip().lower()
        if speaker in {"assistant", "julia", "ai", "model"}:
            return True
        provenance = chunk.provenance if isinstance(chunk.provenance, dict) else {}
        markers = {
            str(provenance.get("origin", "")).lower(),
            str(provenance.get("provenance_type", "")).lower(),
            str(provenance.get("source", "")).lower(),
        }
        return bool(markers & {"assistant_response", "llm_reflection", "model_inference", "assistant_generated"})

    @staticmethod
    def _priority(plan: ContextPlan, authority_score: float) -> int:
        base = 78 if plan.evidence_intents else 55
        if "semantic_evidence" in plan.required_blocks:
            base += 10
        if authority_score >= 0.9:
            base += 5
        return min(100, base)

    @staticmethod
    def _empty_block(plan: ContextPlan, *, filter_assistant: bool) -> ContextBlock:
        return ContextBlock(
            block_id=f"semantic_evidence_empty_{plan.plan_id}",
            block_type="semantic_evidence",
            priority=70,
            content=(
                "Semantic evidence: no matching high-authority evidence found. "
                "Do not invent unsupported personal, relationship, or historical facts."
            ),
            required="semantic_evidence" in plan.required_blocks,
            authority_score=0.0,
            metadata={
                "queried": True,
                "hit_count": 0,
                "query": plan.query,
                "intent_type": plan.intent_type.value,
                "evidence_intents": [intent.value for intent in plan.evidence_intents],
                "excluded_blocks": list(plan.excluded_blocks),
                "assistant_generated_filtered": filter_assistant,
                "warning": "no_matching_high_authority_evidence",
            },
        )
