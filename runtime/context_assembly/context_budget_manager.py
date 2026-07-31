from __future__ import annotations

from .models import AssemblySection


class ContextBudgetManager:
    """Small char-budget allocator for Julia context assembly.

    Phase 3.6.9 uses character budgets instead of token counting to keep this
    layer deterministic and dependency-free. Provider-specific token accounting
    can replace this later without changing section contracts.
    """

    DEFAULT_TOTAL_CHARS = 7000

    def __init__(self, *, total_chars: int = DEFAULT_TOTAL_CHARS):
        self.total_chars = total_chars

    def apply(self, sections: list[AssemblySection]) -> tuple[list[AssemblySection], dict[str, object]]:
        ordered = sorted(sections, key=lambda section: section.priority, reverse=True)
        kept: list[AssemblySection] = []
        used = 0
        clipped_count = 0
        dropped: list[str] = []
        for section in ordered:
            clipped = section.clipped()
            if not clipped.content:
                continue
            remaining = self.total_chars - used
            if remaining <= 0:
                dropped.append(section.name)
                continue
            content = clipped.content
            if len(content) > remaining:
                content = content[:remaining].rstrip() + "…"
                clipped_count += 1
            kept_section = AssemblySection(
                name=clipped.name,
                content=content,
                source=clipped.source,
                priority=clipped.priority,
                max_chars=clipped.max_chars,
            )
            kept.append(kept_section)
            used += len(content)
        return kept, {
            "total_chars": self.total_chars,
            "used_chars": used,
            "section_count": len(kept),
            "clipped_count": clipped_count,
            "dropped": dropped,
        }
