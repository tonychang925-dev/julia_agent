from __future__ import annotations

from enum import Enum


class ContextIntentType(str, Enum):
    IDENTITY_QUESTION = "identity_question"
    RELATIONSHIP_QUESTION = "relationship_question"
    CURRENT_TASK_QUESTION = "current_task_question"
    PERSONAL_HISTORY_RECALL = "personal_history_recall"
    TECHNICAL_DEBUG = "technical_debug"
    PLANNING = "planning"
    EMOTIONAL_SUPPORT = "emotional_support"
    PRIVATE_VOICE_CONTINUITY = "private_voice_continuity"
    CASUAL = "casual"
