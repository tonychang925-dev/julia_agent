from __future__ import annotations

from pathlib import Path
from typing import Any

from .situation_context import SituationContext, SituationSource
from .situation_loader import SituationLoader


class SituationRuntime:
    """Builds provider-independent situation context for Julia."""

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.loader = SituationLoader(self.project_root)

    def build_context(self, interaction_mode: str | None = None) -> SituationContext:
        state = self.loader.load()
        mode = str(interaction_mode or state.get("interaction_mode") or "").strip()
        if mode and mode != "engineering_collaboration":
            state = self._state_for_mode(state, mode)
        return self.compile(SituationSource(state=state))

    def compile(self, source: SituationSource) -> SituationContext:
        state = source.state if isinstance(source.state, dict) else {}
        return SituationContext(
            current_activity=str(state.get("current_activity") or SituationLoader.DEFAULT_STATE["current_activity"]),
            environment=str(state.get("environment") or SituationLoader.DEFAULT_STATE["environment"]),
            goal=str(state.get("goal") or SituationLoader.DEFAULT_STATE["goal"]),
            interaction_mode=str(state.get("interaction_mode") or SituationLoader.DEFAULT_STATE["interaction_mode"]),
            active_topics=self._string_list(state.get("active_topics"), fallback=list(SituationLoader.DEFAULT_STATE["active_topics"])),
        )

    @staticmethod
    def _string_list(value: Any, *, fallback: list[str]) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return list(fallback)

    @staticmethod
    def _state_for_mode(state: dict[str, Any], mode: str) -> dict[str, Any]:
        """Build model-facing situation from persistent relationship mode.

        Mode is owned by Relationship Runtime / persistent cognitive state, not
        inferred from user text.  The model receives the cognitive environment;
        it does not decide the environment and local code does not keyword-match
        the current utterance.
        """
        if mode == "private_voice_continuity":
            return {
                **state,
                "current_activity": "private voice conversation with Tony",
                "environment": "private_voice_conversation",
                "goal": "continue Julia and Tony's long-term private voice relationship context",
                "interaction_mode": mode,
                "active_topics": ["relationship continuity", "voice continuity", "private conversation"],
            }
        return {**state, "interaction_mode": mode}
