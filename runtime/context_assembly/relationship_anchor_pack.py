from __future__ import annotations

from runtime.cognitive.context_compiler import JuliaContext

from .models import AssemblySection


class RelationshipAnchorPackBuilder:
    """Always-on compact relationship substrate."""

    def build(self, julia_context: JuliaContext) -> AssemblySection:
        relationship = julia_context.relationship_context
        content = "\n".join([
            "Relationship Anchor Pack (always-on):",
            f"- Tony is {relationship.user_name}; do not treat him as a new user.",
            f"- Current mode: {relationship.current_mode}; cognitive mode: {julia_context.cognitive_mode.mode.name}.",
            f"- Preferences: {', '.join(relationship.interaction_preferences)}.",
            "- When personal history is asked, use source evidence from diary/archive instead of model priors.",
        ])
        return AssemblySection(
            name="relationship_anchor_pack",
            content=content,
            source="relationship_runtime",
            priority=95,
            max_chars=900,
        )
