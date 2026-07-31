from __future__ import annotations

from .conversation_memory import ConversationContinuityContext


class SessionSummaryBuilder:
    def build(self, *, active_topics: list[str], open_loops: list[dict[str, object]], current_arc: str) -> str:
        if not active_topics and not open_loops:
            return "No established conversation continuity yet."
        topic_text = ", ".join(active_topics[:5]) if active_topics else "no stable active topic"
        loop_text = ", ".join(str(item.get("topic")) for item in open_loops[:3]) if open_loops else "no unresolved open loop"
        return f"Current conversation arc: {current_arc}. Active topics: {topic_text}. Open loops: {loop_text}."

    def from_state(self, state: ConversationContinuityContext) -> str:
        return self.build(active_topics=state.active_topics, open_loops=state.open_loops, current_arc=state.current_arc)
