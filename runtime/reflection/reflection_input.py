from __future__ import annotations

from dataclasses import dataclass

from runtime.conversation_state import ConversationTurn
from runtime.situation import SituationContext


@dataclass(frozen=True)
class ReflectionInput:
    """Provider-independent experience slice used for reflection."""

    conversation_arc: str
    recent_turns: list[ConversationTurn]
    active_topics: list[str]
    open_loops: list[dict[str, object]]
    situation_context: SituationContext
