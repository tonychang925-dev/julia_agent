from __future__ import annotations

from dataclasses import dataclass

from runtime.cognitive.arbitration import CognitiveModeContext
from runtime.conversation_state import ConversationContinuityContext
from runtime.memory import MemoryObject
from runtime.persona import PersonaContext
from runtime.relationship import RelationshipContext
from runtime.situation import SituationContext


@dataclass(frozen=True)
class JuliaContext:
    """JuliaContext v4: Julia's cognitive world plus conversation trajectory."""

    persona_context: PersonaContext
    relationship_context: RelationshipContext
    memory_context: list[MemoryObject]
    situation_context: SituationContext
    conversation_context: ConversationContinuityContext
    cognitive_mode: CognitiveModeContext
    user_input: str


@dataclass(frozen=True)
class RuntimeEnvelope:
    """Runtime-facing execution metadata. Never rendered as JuliaContext."""

    session_id: str
    turn_id: int
    provider: str
    backend: str
    timestamp: str
    latency_target_ms: int


@dataclass(frozen=True)
class CognitiveTurn:
    runtime_envelope: RuntimeEnvelope
    julia_context: JuliaContext
