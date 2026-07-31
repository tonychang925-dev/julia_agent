from __future__ import annotations

from pathlib import Path

from runtime.context_os.memory_router import MemoryScopeClassifier, MemoryScopePolicy
from runtime.context_os.provenance import ProvenanceBuilder, ProvenanceValidator

from .evidence_store import CognitiveEvidenceStore
from .semantic_ranker import AuthorityAwareSemanticRanker, RankedEvidence


class SemanticContextRetriever:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.store = CognitiveEvidenceStore(self.project_root)
        self.ranker = AuthorityAwareSemanticRanker()
        self.provenance_builder = ProvenanceBuilder()
        self.provenance_validator = ProvenanceValidator()
        self.scope_classifier = MemoryScopeClassifier()
        self.scope_policy = MemoryScopePolicy()

    def retrieve(self, query: str, *, limit: int = 8) -> list[RankedEvidence]:
        return self.ranker.rank(query, self.store.load_all(), limit=limit)

    def prompt_section(self, query: str, *, limit: int = 8, cognitive_mode: str | None = None) -> tuple[str, dict[str, object]]:
        ranked = self.retrieve(query, limit=limit)
        scope = self.scope_classifier.classify(user_input=query, cognitive_mode=cognitive_mode)
        provenance_records = [
            self.provenance_builder.from_ranked_evidence(
                item,
                block_id=item.chunk.id,
                injected_by="semantic_evidence_projection",
                cognitive_scope=scope.scope,
            )
            for item in ranked
        ]
        route_decisions = []
        included_ranked = []
        included_records = []
        excluded_records = []
        for item, provenance in zip(ranked, provenance_records):
            memory_class = self._memory_class_from_chunk(item.chunk)
            route = self.scope_policy.decide(
                memory_id=item.chunk.id,
                memory_class=memory_class,
                scope=scope,
                provenance=provenance,
                semantic_score=item.semantic_similarity,
            )
            route_decisions.append(route)
            if route.action == "inject":
                included_ranked.append(item)
                included_records.append(provenance)
            else:
                excluded_records.append(self.provenance_builder.exclusion(
                    source_id=item.chunk.id,
                    source_type=provenance.source_type,
                    reason=route.reason,
                    current_scope=scope.scope,
                    blocked_domains=route.blocked_domains,
                    authority=provenance.authority,
                    speaker=provenance.speaker,
                ))
        provenance_chain = self.provenance_builder.chain([*included_records, *excluded_records], chain_id="semantic_evidence_projection_chain")
        metadata = {
            "queried": True,
            "hit_count": len(included_ranked),
            "scope_decision": scope.to_dict(),
            "route_decisions": [route.to_dict() for route in route_decisions],
            "sources": [
                {
                    "id": item.chunk.id,
                    "source_type": item.chunk.source_type,
                    "speaker": item.chunk.speaker,
                    "authority": item.authority,
                    "semantic_similarity": item.semantic_similarity,
                    "final_score": item.final_score,
                    "reason": item.reason,
                }
                for item in included_ranked
            ],
            "provenance_chain": provenance_chain.to_dict(),
            "provenance_validation": self.provenance_validator.validate_chain(provenance_chain).to_dict(),
        }
        if not included_ranked:
            return (
                "Semantic evidence: no matching evidence found. Do not invent unsupported facts.",
                metadata,
            )
        blocks = "\n\n".join(item.chunk.to_prompt_block() for item in included_ranked)
        return (
            "Semantic Cognitive Evidence (authority-ranked; answer from these source facts before model priors):\n"
            f"{blocks}",
            metadata,
        )


    @staticmethod
    def _memory_class_from_chunk(chunk) -> str:
        if chunk.source_type == "archive":
            return "normal_episode"
        if chunk.source_type == "diary":
            return "normal_episode"
        if chunk.source_type == "memory":
            provenance = chunk.provenance if isinstance(chunk.provenance, dict) else {}
            memory_type = str(provenance.get("memory_type") or "")
            source_id = str(chunk.id).lower()
            content = str(chunk.content).lower()
            if memory_type == "relationship" or "relationship" in source_id or "intimacy" in source_id or "l1_l4" in source_id:
                return "relationship_foundation"
            if any(term in content for term in ["phase 3", "julia runtime", "context", "architecture", "架构"]):
                return "project_milestone"
            return "normal_episode"
        return "normal_episode"
