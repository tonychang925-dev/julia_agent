from __future__ import annotations

from dataclasses import dataclass

from runtime.context_os.provenance import ContextProvenanceRecord, ContextSourceType
from runtime.memory.governance import MemoryGovernanceDecision

from .memory_route_decision import MemoryRouteDecision
from .memory_scope_classifier import MemoryScopeDecision


@dataclass(frozen=True)
class MemoryScopePolicy:
    """Final injection policy: retrieval is not injection."""

    def decide(
        self,
        *,
        memory_id: str,
        memory_class: str,
        scope: MemoryScopeDecision,
        provenance: ContextProvenanceRecord | None,
        semantic_score: float = 0.0,
        governance: MemoryGovernanceDecision | None = None,
    ) -> MemoryRouteDecision:
        if provenance is None:
            return MemoryRouteDecision(
                memory_id=memory_id,
                action="suppress",
                scope=scope.scope,
                reason="missing_provenance",
                provenance_required=True,
                confidence=0.96,
                memory_class=memory_class,
                allowed_domains=scope.allowed_memory,
                blocked_domains=scope.blocked_memory,
            )
        if provenance.source_type not in {ContextSourceType.GOVERNED_MEMORY.value, ContextSourceType.CONVERSATION_ARCHIVE.value, ContextSourceType.CLAUDE_DIARY.value}:
            return MemoryRouteDecision(
                memory_id=memory_id,
                action="suppress",
                scope=scope.scope,
                reason="unsupported_provenance_source_type",
                provenance_required=True,
                confidence=0.9,
                memory_class=memory_class,
                allowed_domains=scope.allowed_memory,
                blocked_domains=scope.blocked_memory,
                provenance_id=provenance.provenance_id,
            )

        domain = self._domain(memory_class, provenance)
        if domain in scope.blocked_memory or self._blocked_by_scope(memory_class, scope):
            return MemoryRouteDecision(
                memory_id=memory_id,
                action="suppress",
                scope=scope.scope,
                reason="cognitive_scope_mismatch",
                provenance_required=True,
                confidence=max(0.84, scope.confidence),
                memory_class=memory_class,
                allowed_domains=scope.allowed_memory,
                blocked_domains=scope.blocked_memory,
                provenance_id=provenance.provenance_id,
            )
        if memory_class in {"archival", "temp_event"}:
            return MemoryRouteDecision(
                memory_id=memory_id,
                action="defer",
                scope=scope.scope,
                reason="non_contextual_memory_class",
                provenance_required=True,
                confidence=0.82,
                memory_class=memory_class,
                allowed_domains=scope.allowed_memory,
                blocked_domains=scope.blocked_memory,
                provenance_id=provenance.provenance_id,
            )
        if semantic_score >= 0.8 and domain in scope.blocked_memory:
            # Explicitly document retrieval != injection.
            return MemoryRouteDecision(
                memory_id=memory_id,
                action="suppress",
                scope=scope.scope,
                reason="high_retrieval_score_but_blocked_by_scope",
                provenance_required=True,
                confidence=0.9,
                memory_class=memory_class,
                allowed_domains=scope.allowed_memory,
                blocked_domains=scope.blocked_memory,
                provenance_id=provenance.provenance_id,
            )
        return MemoryRouteDecision(
            memory_id=memory_id,
            action="inject",
            scope=scope.scope,
            reason="scope_and_provenance_allow_injection",
            provenance_required=True,
            confidence=min(0.95, max(scope.confidence, provenance.confidence, semantic_score)),
            memory_class=memory_class,
            allowed_domains=scope.allowed_memory,
            blocked_domains=scope.blocked_memory,
            provenance_id=provenance.provenance_id,
        )

    @staticmethod
    def _domain(memory_class: str, provenance: ContextProvenanceRecord) -> str:
        text = " ".join([memory_class, provenance.source_id, *(provenance.retrieval_reason or ())]).lower()
        if "relationship" in text or memory_class in {"relationship_foundation", "core_identity"}:
            return "relationship"
        if "intimacy" in text or "private" in text or "l1_l4" in text:
            return "intimacy"
        if memory_class in {"project_milestone"} or any(term in text for term in ["project", "architecture", "runtime", "technical"]):
            return "project"
        if memory_class == "behavior_preference":
            return "behavior_preference"
        return "normal_episode"

    @staticmethod
    def _blocked_by_scope(memory_class: str, scope: MemoryScopeDecision) -> bool:
        if scope.scope in {"engineering", "planning"} and memory_class in {"relationship_foundation", "core_identity"}:
            return True
        if scope.scope == "emotional" and memory_class in {"project_milestone"}:
            return False
        return False
