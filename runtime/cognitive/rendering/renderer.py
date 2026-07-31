from __future__ import annotations

from runtime.cognitive.context_compiler import JuliaContext

from .model_view import CognitivePromptPackage
from .projection import CognitiveProjection, ModelProjection


class CognitiveRenderer:
    """Renders JuliaContext v2 through a provider-neutral cognitive projection."""

    def __init__(self, projection: CognitiveProjection | None = None):
        self.projection = projection or CognitiveProjection()

    def render(self, context: JuliaContext) -> CognitivePromptPackage:
        view = self.projection.project(context)
        system_context = self._system_context(view)
        return CognitivePromptPackage(
            system_context=system_context,
            conversation_messages=[{"role": "user", "content": view.user_input}],
            memory_summary=view.relevant_memory,
            style_constraints=view.speaking_style,
        )

    @staticmethod
    def _system_context(view: ModelProjection) -> str:
        sections = [
            view.identity,
            "",
            "Relationship continuity:",
            view.relationship,
            "",
            view.current_context,
            "",
            "Selected memory:",
            view.relevant_memory,
            "",
            "Recent conversation:",
            view.recent_conversation,
            "",
            "Provider-neutral behavior contract:",
            view.behavior_contract,
            "",
            "Speaking style:",
            *[f"- {item}" for item in view.speaking_style],
        ]
        return "\n".join(sections).strip()
