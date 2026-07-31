from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CognitivePromptPackage:
    """Provider-neutral rendered cognitive view.

    This is not a provider request. Provider-specific adapters format this view
    into OpenAI/Claude/Gemini message shapes.
    """

    system_context: str
    conversation_messages: list[dict[str, str]]
    memory_summary: str
    style_constraints: list[str]
