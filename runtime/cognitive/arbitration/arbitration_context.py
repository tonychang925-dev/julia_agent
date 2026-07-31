from __future__ import annotations

from dataclasses import dataclass, field

from runtime.relationship import RelationshipContext
from runtime.situation import SituationContext


@dataclass(frozen=True)
class ArbitrationContext:
    relationship_context: RelationshipContext
    situation_context: SituationContext
    conversation_context: dict[str, object]
    recent_turns: list[dict[str, str]] = field(default_factory=list)
    user_intent: dict[str, object] = field(default_factory=dict)
