from __future__ import annotations

from enum import Enum


class MessageLifecycleState(str, Enum):
    """Model-facing lifecycle state for a conversation message."""

    ACTIVE = "ACTIVE"
    COMPRESSED = "COMPRESSED"
    ARCHIVED = "ARCHIVED"
    RETRIEVED = "RETRIEVED"
    DROPPED = "DROPPED"


class MessageSpeaker(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class CognitiveRole(str, Enum):
    IDENTITY = "identity"
    RELATIONSHIP = "relationship"
    TASK = "task"
    EVIDENCE = "evidence"
    DECISION = "decision"
    EMOTION = "emotion"
    CASUAL = "casual"
    RUNTIME = "runtime"
