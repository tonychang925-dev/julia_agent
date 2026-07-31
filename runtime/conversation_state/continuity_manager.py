from __future__ import annotations

from dataclasses import replace

from .conversation_memory import ConversationContinuityContext
from .conversation_turn import ConversationTurn
from .session_summary import SessionSummaryBuilder
from .topic_tracker import TopicTracker
from .unresolved_context import UnresolvedContextTracker


class ContinuityManager:
    """Turns raw turns into a compact conversation trajectory."""

    def __init__(self, *, max_recent_turns: int = 8, max_active_topics: int = 8):
        self.max_recent_turns = max_recent_turns
        self.max_active_topics = max_active_topics
        self.topic_tracker = TopicTracker()
        self.unresolved_tracker = UnresolvedContextTracker()
        self.summary_builder = SessionSummaryBuilder()

    def build_context(
        self,
        *,
        previous_state: ConversationContinuityContext | dict[str, object] | None = None,
        recent_turns: list[ConversationTurn | dict[str, object]] | None = None,
        current_user_input: str = "",
        cognitive_mode: str = "",
    ) -> ConversationContinuityContext:
        previous = self._coerce_state(previous_state)
        turns = self._coerce_turns(recent_turns or [])
        active_topics = self._merge_topics(
            previous.active_topics if previous else [],
            [topic for turn in turns for topic in turn.topics],
            self.topic_tracker.extract_topics(current_user_input),
        )
        open_loops = self.unresolved_tracker.merge(
            previous.open_loops if previous else [],
            self.unresolved_tracker.detect_open_loops(current_user_input, active_topics),
        )
        current_arc = self._derive_arc(
            current_user_input=current_user_input,
            active_topics=active_topics,
            cognitive_mode=cognitive_mode,
            previous_arc=previous.current_arc if previous else "",
        )
        context = ConversationContinuityContext(
            active_topics=active_topics,
            open_loops=open_loops,
            current_arc=current_arc,
            recent_turns=turns[-self.max_recent_turns :],
            session_summary="",
        )
        return replace(context, session_summary=self.summary_builder.from_state(context))

    def update(self, previous_state: ConversationContinuityContext | None, new_turn: ConversationTurn) -> ConversationContinuityContext:
        previous_turns = list(previous_state.recent_turns) if previous_state else []
        return self.build_context(
            previous_state=previous_state,
            recent_turns=[*previous_turns, new_turn],
            current_user_input=new_turn.user_text,
            cognitive_mode=new_turn.cognitive_mode,
        )

    def _coerce_state(self, value: ConversationContinuityContext | dict[str, object] | None) -> ConversationContinuityContext | None:
        if isinstance(value, ConversationContinuityContext):
            return value
        if not isinstance(value, dict):
            return None
        return ConversationContinuityContext(
            active_topics=[str(item) for item in value.get("active_topics", [])] if isinstance(value.get("active_topics"), list) else [],
            open_loops=[dict(item) for item in value.get("open_loops", []) if isinstance(item, dict)] if isinstance(value.get("open_loops"), list) else [],
            current_arc=str(value.get("current_arc") or ""),
            recent_turns=self._coerce_turns(value.get("recent_turns", []) if isinstance(value.get("recent_turns"), list) else []),
            session_summary=str(value.get("session_summary") or ""),
        )

    @staticmethod
    def _coerce_turns(values: list[ConversationTurn | dict[str, object]]) -> list[ConversationTurn]:
        turns: list[ConversationTurn] = []
        for index, item in enumerate(values):
            if isinstance(item, ConversationTurn):
                turns.append(item)
            elif isinstance(item, dict):
                turns.append(ConversationTurn.from_dict(item, fallback_turn_id=index + 1))
        return turns

    def _merge_topics(self, *groups: list[str]) -> list[str]:
        merged: list[str] = []
        for group in groups:
            for topic in group:
                value = str(topic).strip()
                if value and value not in merged:
                    merged.append(value)
        return merged[-self.max_active_topics :]

    @staticmethod
    def _derive_arc(*, current_user_input: str, active_topics: list[str], cognitive_mode: str, previous_arc: str) -> str:
        text = current_user_input.lower()
        if "Project Pressure" in active_topics and (
            any(signal in text for signal in ["压力", "做不完", "没完成", "完不成", "撑不住", "累"])
            or previous_arc == "project_pressure"
        ):
            return "project_pressure"
        if "Health Follow-up" in active_topics:
            return "health_followup"
        if cognitive_mode == "debugging_mode" or "Debugging" in active_topics:
            return "debugging_issue"
        if cognitive_mode == "engineering_collaboration" or any(topic in active_topics for topic in ["Julia Runtime", "Cognitive Architecture"]):
            return "technical_progress"
        if cognitive_mode == "emotional_support":
            return "emotional_check_in"
        return previous_arc or "ongoing_conversation"
