from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class JuliaContext:
    """One cognitive turn snapshot for Julia.

    JuliaContext is not a database and not a provider prompt. It is the stable
    world snapshot Julia Runtime gives to a cognitive provider for one turn.
    """

    identity: dict[str, Any]
    relationship: dict[str, Any]
    memory: list[dict[str, Any]]
    conversation: dict[str, Any]
    capability: dict[str, Any]
    policy: dict[str, Any]
    runtime_state: dict[str, Any]
    emotional_context: dict[str, Any]
    current_input: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
