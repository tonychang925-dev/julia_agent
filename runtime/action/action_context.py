from __future__ import annotations

from dataclasses import dataclass

from runtime.cognitive.arbitration import CognitiveModeContext
from runtime.conversation_state import ConversationContinuityContext
from runtime.relationship import RelationshipContext
from runtime.situation import SituationContext


@dataclass(frozen=True)
class ActionContext:
    """Julia-facing action planning context. Runtime/provider metadata is excluded."""

    situation_context: SituationContext
    cognitive_mode: CognitiveModeContext
    conversation_context: ConversationContinuityContext
    relationship_context: RelationshipContext
    user_input: str
