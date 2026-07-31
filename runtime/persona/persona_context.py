from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PersonaSource:
    """Raw persistent identity inputs for Persona Runtime.

    This source is intentionally limited to identity-layer files. It does not
    carry runtime/provider/backend/session/TTS metadata.
    """

    identity_yaml: dict[str, Any]
    personality_text: str = ""
    values_text: str = ""
    conversation_contract_text: str = ""


@dataclass(frozen=True)
class PersonaContext:
    """Model-facing Julia persona context.

    PersonaContext answers "who is Julia and how does she communicate?" It is
    not a runtime envelope and must not contain provider/backend/model fields.
    """

    name: str
    identity_summary: str
    speaking_style: list[str]
    values: list[str]
    communication_preferences: list[str]
