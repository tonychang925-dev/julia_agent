from __future__ import annotations

from .model_view import CognitivePromptPackage


class ProviderFormatter:
    """Formats provider-neutral CognitivePromptPackage into provider message shapes."""

    def to_openai_messages(self, package: CognitivePromptPackage) -> list[dict[str, str]]:
        return [{"role": "system", "content": package.system_context}, *package.conversation_messages]
