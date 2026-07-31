from __future__ import annotations

from runtime.reflection.reflection_input import ReflectionInput


class ReflectionPromptBuilder:
    """Builds an instruction payload for future LLM reflection providers.

    The prompt explicitly asks for MemoryCandidate-shaped proposals only. It is
    not used to persist memory and contains no provider/runtime metadata.
    """

    def build(self, reflection_input: ReflectionInput) -> str:
        turns = "\n".join(f"Tony: {turn.user_text}\nJulia: {turn.assistant_text}" for turn in reflection_input.recent_turns[-8:])
        topics = ", ".join(reflection_input.active_topics)
        return (
            "Extract durable experience meaning from this Julia conversation trajectory.\n"
            "Return only proposed MemoryCandidate items, never MemoryObject and never runtime metadata.\n"
            f"Conversation arc: {reflection_input.conversation_arc}\n"
            f"Active topics: {topics}\n"
            f"Turns:\n{turns}"
        ).strip()
