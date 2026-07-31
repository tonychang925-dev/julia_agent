from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionIntent:
    """Cognitive action proposal. It is not a command and has no execution authority."""

    intent_type: str
    goal: str
    target: str | None
    risk_level: str
    required_capability: str | None
    reason: str
    confidence: float
