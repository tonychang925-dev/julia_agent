from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from runtime.cognitive.context_compiler import JuliaContext


@dataclass(frozen=True)
class ContextCacheKey:
    """Stable cache key for context blocks that are safe to reuse.

    The key intentionally excludes current user input, semantic evidence route
    decisions, action decisions, provider output, and runtime envelope fields.
    """

    session_id: str
    persona_version: str
    relationship_version: str
    task_state_version: str
    memory_version: str
    context_mode: str
    component: str

    @classmethod
    def from_julia_context(
        cls,
        *,
        session_id: str,
        julia_context: JuliaContext,
        component: str,
        task_state_version: str | None = None,
        memory_version: str | None = None,
    ) -> "ContextCacheKey":
        persona = julia_context.persona_context
        relationship = julia_context.relationship_context
        conversation = julia_context.conversation_context
        return cls(
            session_id=session_id,
            persona_version=_stable_hash({
                "name": persona.name,
                "identity_summary": persona.identity_summary,
                "speaking_style": persona.speaking_style,
                "values": persona.values,
                "communication_preferences": persona.communication_preferences,
            }),
            relationship_version=_stable_hash({
                "user_name": relationship.user_name,
                "relationship_stage": relationship.relationship_stage,
                "shared_projects": relationship.shared_projects,
                "interaction_preferences": relationship.interaction_preferences,
                "current_mode": relationship.current_mode,
            }),
            task_state_version=task_state_version or _stable_hash({
                "active_topics": conversation.active_topics,
                "open_loops": conversation.open_loops,
                "current_arc": conversation.current_arc,
            }),
            memory_version=memory_version or _stable_hash([
                {"id": item.id, "type": item.type, "summary": item.summary, "topics": item.topics}
                for item in julia_context.memory_context
            ]),
            context_mode=julia_context.cognitive_mode.mode.name,
            component=component,
        )

    @property
    def digest(self) -> str:
        return _stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, str]:
        return {
            "session_id": self.session_id,
            "persona_version": self.persona_version,
            "relationship_version": self.relationship_version,
            "task_state_version": self.task_state_version,
            "memory_version": self.memory_version,
            "context_mode": self.context_mode,
            "component": self.component,
        }


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
