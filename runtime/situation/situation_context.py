from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SituationSource:
    """Raw current-situation state.

    SituationSource describes the current scene. It does not carry memory
    content, relationship history, or runtime/provider execution metadata.
    """

    state: dict[str, Any]


@dataclass(frozen=True)
class SituationContext:
    """Model-facing current-world context: what is happening now."""

    current_activity: str
    environment: str
    goal: str
    interaction_mode: str
    active_topics: list[str]
