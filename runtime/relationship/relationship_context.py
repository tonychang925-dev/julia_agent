from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RelationshipSource:
    """Raw relationship-layer inputs for Relationship Runtime.

    RelationshipSource stores relationship facts and preferences. It must not
    store provider/backend/session metadata or inferred private emotional scores.
    """

    identity_yaml: dict[str, Any]
    conversation_contract_text: str = ""
    state: dict[str, Any] | None = None


@dataclass(frozen=True)
class RelationshipContext:
    """Model-facing relationship context between Julia and Tony.

    This context answers "who are Julia and Tony to each other?" It stores
    explicit relationship state and preferences, not guessed psychology.
    """

    user_name: str
    relationship_stage: str
    shared_projects: list[str]
    interaction_preferences: list[str]
    current_mode: str
