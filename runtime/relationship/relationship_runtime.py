from __future__ import annotations

from pathlib import Path
from typing import Any

from .relationship_context import RelationshipContext, RelationshipSource
from .relationship_loader import RelationshipLoader


class RelationshipRuntime:
    """Builds provider-independent relationship context for Julia."""

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.loader = RelationshipLoader(self.project_root)

    def build_context(self) -> RelationshipContext:
        return self.compile(self.loader.load())

    def compile(self, source: RelationshipSource) -> RelationshipContext:
        identity_yaml = source.identity_yaml if isinstance(source.identity_yaml, dict) else {}
        state = source.state if isinstance(source.state, dict) else {}
        return RelationshipContext(
            user_name=self._user_name(identity_yaml),
            relationship_stage=str(state.get("relationship_stage") or "long_term_collaboration"),
            shared_projects=self._string_list(state.get("shared_projects"), fallback=["Julia Runtime", "AI Agent Architecture"]),
            interaction_preferences=self._interaction_preferences(state, source.conversation_contract_text),
            current_mode=str(state.get("current_mode") or "engineering_collaboration"),
        )

    @staticmethod
    def _user_name(identity_yaml: dict[str, Any]) -> str:
        relationship = identity_yaml.get("relationship", {}) if isinstance(identity_yaml, dict) else {}
        user = relationship.get("user", {}) if isinstance(relationship, dict) else {}
        if isinstance(user, dict):
            return str(user.get("name") or "Tony")
        return "Tony"

    def _interaction_preferences(self, state: dict[str, Any], contract_text: str) -> list[str]:
        preferences = self._string_list(state.get("interaction_preferences"), fallback=[])
        lowered = contract_text.lower()
        if "Engineer Mode" in contract_text or "technical" in lowered:
            preferences.append("technical_when_needed")
        if "short" in lowered or "短" in contract_text:
            preferences.append("concise")
        if "warm" in lowered or "温" in contract_text:
            preferences.append("warm")
        if "memory" in lowered or "记忆" in contract_text:
            preferences.append("context_continuity")
        return self._dedupe(preferences)

    @staticmethod
    def _string_list(value: Any, *, fallback: list[str]) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return list(fallback)

    @staticmethod
    def _dedupe(items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            value = str(item).strip()
            if not value or value in seen:
                continue
            seen.add(value)
            result.append(value)
        return result
