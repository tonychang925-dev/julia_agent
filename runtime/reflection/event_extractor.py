from __future__ import annotations

from runtime.conversation_state import ConversationTurn


class EventExtractor:
    """Extracts durable event signals from a continuity trajectory.

    First version is deterministic and metadata-based: it detects milestones,
    decisions, relationship facts, and noise without calling an LLM.
    """

    MILESTONE_SIGNALS = ["完成", "已完成", "实现", "implemented", "finished", "completed", "migrated", "迁移", "冻结", "上线"]
    DECISION_SIGNALS = ["决定", "确定", "冻结", "采用", "命名", "原则", "架构决策"]
    RELATIONSHIP_SIGNALS = ["偏好", "喜欢", "不喜欢", "关系", "陪伴方式", "交流方式"]

    def extract(self, turns: list[ConversationTurn], *, active_topics: list[str], conversation_arc: str) -> list[dict[str, object]]:
        joined = "\n".join(f"{turn.user_text}\n{turn.assistant_text}" for turn in turns).lower()
        if not joined.strip():
            return []
        events: list[dict[str, object]] = []
        if self._has_any(joined, self.MILESTONE_SIGNALS) and self._is_architecture_context(active_topics, joined):
            events.append({"event_type": "milestone", "topics": active_topics, "arc": conversation_arc, "text": joined})
            return events
        if self._has_any(joined, self.DECISION_SIGNALS) and self._is_architecture_context(active_topics, joined):
            events.append({"event_type": "decision", "topics": active_topics, "arc": conversation_arc, "text": joined})
        if self._has_any(joined, self.RELATIONSHIP_SIGNALS) and any(topic in active_topics for topic in ["Provider Migration", "Cognitive Architecture", "Julia Runtime"]):
            events.append({"event_type": "relationship", "topics": active_topics, "arc": conversation_arc, "text": joined})
        if not events:
            events.append({"event_type": "noise", "topics": active_topics, "arc": conversation_arc, "text": joined})
        return events

    @staticmethod
    def _has_any(text: str, signals: list[str]) -> bool:
        return any(signal.lower() in text for signal in signals)

    @staticmethod
    def _is_architecture_context(active_topics: list[str], text: str) -> bool:
        if any(topic in active_topics for topic in ["Julia Runtime", "Cognitive Architecture", "Provider Migration"]):
            return True
        return any(signal in text for signal in ["julia runtime", "context", "runtime", "cognitive", "架构", "认知"])
