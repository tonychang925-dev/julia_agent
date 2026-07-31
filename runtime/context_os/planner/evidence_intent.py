from __future__ import annotations

from enum import Enum


class EvidenceIntentType(str, Enum):
    SHARED_STORY = "shared_story"
    CREATIVE_WORK = "creative_work"
    LIFE_EXPERIENCE = "life_experience"
    RELATIONSHIP_ORIGIN = "relationship_origin"
    IDENTITY_ANCHOR = "identity_anchor"
    PROJECT_STATE = "project_state"
    TECHNICAL_EVIDENCE = "technical_evidence"
    RECENT_CONVERSATION = "recent_conversation"
    EMOTIONAL_CONTEXT = "emotional_context"
    OPEN_LOOP = "open_loop"
