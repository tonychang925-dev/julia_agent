from __future__ import annotations

from .behavior_contract import BehaviorContract
from .emotional_policy import emotional_contract
from .intimacy_policy import private_voice_contract
from .technical_policy import technical_contract


def contract_for_mode(mode: str) -> BehaviorContract:
    if mode == "private_voice_continuity":
        return private_voice_contract()
    if mode == "emotional_support":
        return emotional_contract()
    if mode in {"engineering_collaboration", "debugging_mode", "planning_mode", "learning_mode"}:
        return technical_contract(mode)
    return technical_contract(mode)
