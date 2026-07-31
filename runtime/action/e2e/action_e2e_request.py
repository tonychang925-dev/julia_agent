from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionE2ERequest:
    text: str
    session_id: str = "e2e_alpha"
    turn_id: int = 1
    mode: str = "engineering_collaboration"
    alpha_mode: bool = True
    allow_side_effects: bool = False
    max_action_steps: int = 1

    def __post_init__(self) -> None:
        if self.alpha_mode and self.allow_side_effects:
            raise ValueError("E2E Alpha does not allow side effects")
        if self.max_action_steps != 1:
            raise ValueError("E2E Alpha is single-step only")
