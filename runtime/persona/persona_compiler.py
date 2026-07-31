from __future__ import annotations

import re
from typing import Any

from .persona_context import PersonaContext, PersonaSource


class PersonaCompiler:
    """Compiles PersonaSource into model-facing PersonaContext."""

    DEFAULT_STYLE = ["warm", "natural", "Chinese-first"]

    def compile(self, source: PersonaSource) -> PersonaContext:
        identity_yaml = source.identity_yaml if isinstance(source.identity_yaml, dict) else {}
        name = self._identity_name(identity_yaml)
        role = self._identity_role(identity_yaml)
        traits = self._identity_traits(identity_yaml)
        yaml_style = self._communication_style(identity_yaml)
        values = self._values(identity_yaml, source.values_text)
        preferences = self._communication_preferences(source.conversation_contract_text)
        speaking_style = self._dedupe([*traits, *yaml_style, *self.DEFAULT_STYLE])
        identity_summary = self._identity_summary(
            name=name,
            role=role,
            personality_text=source.personality_text,
        )
        return PersonaContext(
            name=name,
            identity_summary=identity_summary,
            speaking_style=speaking_style,
            values=values,
            communication_preferences=preferences,
        )

    @staticmethod
    def _identity_name(identity_yaml: dict[str, Any]) -> str:
        identity = identity_yaml.get("identity", {}) if isinstance(identity_yaml, dict) else {}
        if isinstance(identity, dict):
            return str(identity.get("name") or "Julia")
        return "Julia"

    @staticmethod
    def _identity_role(identity_yaml: dict[str, Any]) -> str:
        identity = identity_yaml.get("identity", {}) if isinstance(identity_yaml, dict) else {}
        if isinstance(identity, dict):
            return str(identity.get("role") or "Tony's long-term AI companion persona")
        return "Tony's long-term AI companion persona"

    @staticmethod
    def _identity_traits(identity_yaml: dict[str, Any]) -> list[str]:
        personality = identity_yaml.get("personality", {}) if isinstance(identity_yaml, dict) else {}
        traits = personality.get("traits", []) if isinstance(personality, dict) else []
        return [str(item) for item in traits if str(item).strip()]

    @staticmethod
    def _communication_style(identity_yaml: dict[str, Any]) -> list[str]:
        communication = identity_yaml.get("communication", {}) if isinstance(identity_yaml, dict) else {}
        style = communication.get("style", {}) if isinstance(communication, dict) else {}
        values: list[str] = []
        language = communication.get("language") if isinstance(communication, dict) else None
        if language:
            values.append(f"{language}-first")
        if isinstance(style, dict):
            for key, enabled in style.items():
                if enabled:
                    values.append(str(key))
        return values

    def _values(self, identity_yaml: dict[str, Any], values_text: str) -> list[str]:
        principles = identity_yaml.get("principles", []) if isinstance(identity_yaml, dict) else []
        values = [str(item) for item in principles if str(item).strip()]
        for line in values_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("- "):
                values.append(stripped[2:].strip())
        return self._dedupe(values)

    def _communication_preferences(self, contract_text: str) -> list[str]:
        preferences: list[str] = []
        lowered = contract_text.lower()
        if "short" in lowered or "短" in contract_text:
            preferences.append("prefer short natural replies by default")
        if "warm" in lowered or "温" in contract_text:
            preferences.append("speak warmly")
        if "technical" in lowered or "Engineer Mode" in contract_text:
            preferences.append("be technical when Tony is debugging or designing architecture")
        if "memory" in lowered or "记忆" in contract_text:
            preferences.append("distinguish loaded memory from uncertainty")
        return self._dedupe(preferences)

    @staticmethod
    def _identity_summary(*, name: str, role: str, personality_text: str) -> str:
        first_paragraph = " ".join(
            line.strip()
            for line in personality_text.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
        first_paragraph = re.sub(r"\s+", " ", first_paragraph).strip()
        summary = f"{name} is {role}."
        if first_paragraph:
            summary = f"{summary} {first_paragraph}"
        return summary.strip()

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
