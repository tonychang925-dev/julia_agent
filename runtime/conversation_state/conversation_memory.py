from __future__ import annotations

from dataclasses import dataclass, field

from .conversation_turn import ConversationTurn


@dataclass(frozen=True)
class ConversationContinuityContext:
    """Conversation meaning over time: arc, topics, open loops, and summary."""

    active_topics: list[str]
    open_loops: list[dict[str, object]]
    current_arc: str
    recent_turns: list[ConversationTurn]
    session_summary: str


# Alias kept explicit for code that wants the state-oriented name.
ConversationState = ConversationContinuityContext
