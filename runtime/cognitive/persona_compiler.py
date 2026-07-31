from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .cognitive_context import JuliaContext


@dataclass(frozen=True)
class PersonaPackage:
    name: str
    user_name: str
    persona_text: str
    context_text: str
    memory_text: str


class PersonaCompiler:
    """Compiles JuliaContext into persona-facing cognitive material.

    This layer intentionally separates runtime truth from persona conditioning:
    provider/backend/session metadata belongs in trace/runtime_state, while the
    model-facing prompt should describe Julia's identity, relationship, memory,
    and communication contracts.
    
    It also applies a small context budget. Long identity documents are useful
    as persistent state, but sending all of them every turn increases TTFT.
    """

    DEFAULT_SECTION_BUDGETS = {
        "conversation_contract": 1400,
        "adult_intimacy_contract": 1800,
        "personality": 600,
        "values": 600,
        "transcript_role": 1200,
        "specification": 1200,
        "claude_diary_summary": 600,
    }

    def __init__(self, section_budgets: dict[str, int] | None = None, max_memory_items: int = 5):
        self.section_budgets = dict(self.DEFAULT_SECTION_BUDGETS)
        if section_budgets:
            self.section_budgets.update(section_budgets)
        self.max_memory_items = max_memory_items

    def compile(self, context: JuliaContext) -> PersonaPackage:
        identity_yaml = context.identity.get("yaml", {}) if isinstance(context.identity, dict) else {}
        name = self._identity_name(identity_yaml)
        user_name = self._user_name(context.relationship)
        persona_text = self._persona_text(context, name=name, user_name=user_name)
        context_text = self._context_text(context)
        memory_text = self._memory_text(context.memory, max_items=self.max_memory_items)
        return PersonaPackage(
            name=name,
            user_name=user_name,
            persona_text=persona_text,
            context_text=context_text,
            memory_text=memory_text,
        )

    @staticmethod
    def _identity_name(identity_yaml: dict[str, Any]) -> str:
        if isinstance(identity_yaml, dict):
            return identity_yaml.get("identity", {}).get("name", "Julia")
        return "Julia"

    @staticmethod
    def _user_name(relationship: dict[str, Any]) -> str:
        if isinstance(relationship, dict):
            return relationship.get("user", {}).get("name", "Tony")
        return "Tony"

    def _persona_text(self, context: JuliaContext, *, name: str, user_name: str) -> str:
        identity = context.identity if isinstance(context.identity, dict) else {}
        sections = [
            f"You are {name}.",
            f"You are speaking with {user_name} in an ongoing private conversation.",
            "Preserve Julia's identity, memory continuity, relationship context, and Chinese-first voice.",
            "Do not discuss internal implementation details unless Tony explicitly asks about architecture or runtime internals.",
        ]
        for key, title in [
            ("conversation_contract", "Conversation contract"),
            ("adult_intimacy_contract", "Private intimacy / relationship contract"),
            ("personality", "Personality"),
            ("values", "Values"),
            ("transcript_role", "Transcript-derived role"),
            ("specification", "Identity specification"),
            ("claude_diary_summary", "Julia's relationship history (Claude Code diary)"),
        ]:
            value = identity.get(key, "")
            if value:
                budget = self.section_budgets.get(key, 1000)
                if budget and budget > 0:
                    value = self._trim(value, max_chars=budget)
                sections.append(f"\n{title}:\n{value}")
        return "\n".join(sections).strip()

    @staticmethod
    def _context_text(context: JuliaContext) -> str:
        return "\n".join(
            [
                f"Relationship context: {context.relationship}",
                f"Conversation context: {context.conversation}",
                f"Interaction style context: {context.emotional_context}",
                f"Behavior policy: {context.policy}",
                f"Available capabilities summary: {context.capability}",
            ]
        )

    @staticmethod
    def _memory_text(memory: list[dict[str, Any]], *, max_items: int = 5) -> str:
        if not memory:
            return "No retrieved memory for this turn."
        selected = memory[:max_items]
        lines = [f"- {item}" for item in selected]
        if len(memory) > max_items:
            lines.append(f"- ...[{len(memory) - max_items} more memory items omitted]")
        return "\n".join(lines)

    @staticmethod
    def _trim(value: str, *, max_chars: int = 6000) -> str:
        value = value.strip()
        if len(value) <= max_chars:
            return value
        return value[:max_chars].rstrip() + "\n...[trimmed]"
