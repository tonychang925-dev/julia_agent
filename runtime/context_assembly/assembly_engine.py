from __future__ import annotations

from pathlib import Path

from runtime.cognitive.context_compiler import JuliaContext
from runtime.context_os.cache import ContextCacheKey, ContextSnapshotCache

from .context_budget_manager import ContextBudgetManager
from .core_identity_pack import CoreIdentityPackBuilder
from .relationship_anchor_pack import RelationshipAnchorPackBuilder
from .source_memory_resolver import SourceAwareMemoryResolver
from .conflict_resolver import ConflictResolver
from .models import AssembledContext, AssemblySection


class ContextAssemblyEngine:
    """Claude-style context assembly owned by Julia Runtime.

    This layer builds a stable cognitive substrate every turn. It complements
    JuliaContext rather than replacing Persona/Relationship/Memory runtimes.
    """

    def __init__(self, project_root: str | Path, *, budget_manager: ContextBudgetManager | None = None):
        self.project_root = Path(project_root)
        self.core_identity = CoreIdentityPackBuilder(self.project_root)
        self.relationship_anchor = RelationshipAnchorPackBuilder()
        self.source_resolver = SourceAwareMemoryResolver(self.project_root)
        self.conflict_resolver = ConflictResolver()
        self.budget_manager = budget_manager or ContextBudgetManager()
        self.stable_section_cache: ContextSnapshotCache[list[AssemblySection]] = ContextSnapshotCache()

    def assemble(self, user_input: str, *, session_id: str, julia_context: JuliaContext) -> AssembledContext:
        cache_key = ContextCacheKey.from_julia_context(
            session_id=session_id,
            julia_context=julia_context,
            component="context_assembly_stable_sections.v1",
            task_state_version="excluded_from_stable_cache",
            memory_version="excluded_from_stable_cache",
        )
        stable_sections = self.stable_section_cache.get(cache_key)
        cache_status = "hit" if stable_sections is not None else "miss"
        if stable_sections is None:
            stable_sections = self._build_stable_sections(julia_context)
            self.stable_section_cache.set(cache_key, stable_sections)

        # Real-time evidence is intentionally outside the cache: it depends on
        # current user input, Memory Router decisions, and source freshness.
        resolved_sections, resolver_meta = self.source_resolver.resolve(
            user_input,
            session_id=session_id,
            julia_context=julia_context,
        )
        sections = [*stable_sections, *resolved_sections]
        kept, budget_meta = self.budget_manager.apply(sections)
        prompt = self._render(kept)
        startup_memory = dict(self.core_identity.last_startup_memory_metadata)
        return AssembledContext(
            prompt_section=prompt,
            metadata={
                "enabled": True,
                "version": "phase3.6.9.context_assembly.v1",
                "startup_memory": startup_memory,
                "sections": [section.name for section in kept],
                "sources": [section.source for section in kept],
                "budget": budget_meta,
                "resolver": resolver_meta,
                "conflict_resolver": self.conflict_resolver.metadata(),
                "cache": {
                    "enabled": True,
                    "status": cache_status,
                    "component": cache_key.component,
                    "key_digest": cache_key.digest,
                    "key": cache_key.to_dict(),
                    "cached_sections": [section.name for section in stable_sections],
                    "excluded_from_cache": [
                        "current_user_input",
                        "semantic_evidence",
                        "memory_route_decisions",
                        "action_governance_decisions",
                        "provider_output",
                    ],
                    "stats": self.stable_section_cache.stats(),
                },
            },
        )

    def _build_stable_sections(self, julia_context: JuliaContext) -> list[AssemblySection]:
        return [
            self.core_identity.build(julia_context),
            self.relationship_anchor.build(julia_context),
            AssemblySection(
                name="conflict_resolver",
                content=self.conflict_resolver.prompt(),
                source="context_assembly",
                priority=98,
                max_chars=700,
            ),
        ]

    @staticmethod
    def _render(sections: list[AssemblySection]) -> str:
        if not sections:
            return ""
        blocks = ["Julia Context Assembly Runtime (stable cognitive substrate):"]
        for section in sections:
            blocks.append(f"\n## {section.name}\n{section.content.strip()}")
        return "\n".join(blocks).strip()
