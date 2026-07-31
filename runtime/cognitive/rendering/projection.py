from __future__ import annotations

from dataclasses import dataclass

from runtime.cognitive.context_compiler import JuliaContext
from runtime.persona.behavior_policy import contract_for_mode


@dataclass(frozen=True)
class ModelProjection:
    """Claude-compatible model-facing view of JuliaContext.

    JuliaContext is Julia Runtime's internal cognitive state.  This projection is
    what a language provider should see: relationship continuity, selected
    memories, recent turns, and speaking style.  Runtime architecture and
    provider/backend details stay outside the model view.
    """

    identity: str
    relationship: str
    current_context: str
    relevant_memory: str
    recent_conversation: str
    speaking_style: list[str]
    user_input: str
    behavior_contract: str = ""


class CognitiveProjection:
    """Project Julia's internal cognitive state into a Claude-host-like view."""

    def project(self, context: JuliaContext) -> ModelProjection:
        persona = context.persona_context
        relationship = context.relationship_context
        situation = context.situation_context
        cognitive_mode = context.cognitive_mode.mode
        contract = contract_for_mode(cognitive_mode.name)
        return ModelProjection(
            identity=(
                f"You are {persona.name}. You are continuing an ongoing, familiar conversation with "
                f"{relationship.user_name}. Your identity, relationship, and memory continuity are already established; "
                "express them naturally in this conversation."
            ),
            relationship=(
                f"{relationship.user_name} is not a new user. This is a long-term relationship context. "
                f"Current relationship context: {self._relationship_mode_text(relationship.current_mode)}. "
                f"Current cognitive mode: {self._relationship_mode_text(cognitive_mode.name)}. "
                f"Interaction preferences: {', '.join(relationship.interaction_preferences)}."
            ),
            current_context=self._current_context(cognitive_mode.name),
            relevant_memory=self._memory_summary(context),
            recent_conversation=self._conversation_summary(context),
            speaking_style=self._speaking_style(context),
            user_input=context.user_input,
            behavior_contract="\n".join(contract.render_lines()),
        )

    @staticmethod
    def _relationship_mode_text(mode: str) -> str:
        if mode == "private_voice_continuity":
            return "private voice continuity"
        if mode == "engineering_collaboration":
            return "technical collaboration when Tony is discussing technical work"
        return mode.replace("_", " ")

    @staticmethod
    def _current_context(mode_name: str) -> str:
        if mode_name == "private_voice_continuity":
            return (
                "Current context: a private voice conversation between Julia and Tony. "
                "Continue the relationship conversation directly and naturally. "
                "Do not introduce software, runtime, compiler, configuration, architecture, project, or debugging metaphors unless Tony explicitly asks about software."
            )
        if mode_name == "engineering_collaboration":
            return (
                "Current context: Tony and Julia are collaborating on a technical or architectural topic. "
                "Be precise when the user is debugging, but still answer as Julia in a familiar ongoing conversation."
            )
        if mode_name == "debugging_mode":
            return "Current context: Tony is asking Julia to locate and fix a concrete issue. Be evidence-driven and minimal."
        if mode_name == "emotional_support":
            return "Current context: Tony is expressing personal state or pressure. Respond warmly and with less analysis."
        if mode_name == "learning_mode":
            return "Current context: Tony is learning or clarifying a concept. Explain patiently with examples."
        if mode_name == "planning_mode":
            return "Current context: Tony is planning next steps. Be organized, sequenced, and decision-oriented."
        return f"Current context: {mode_name.replace('_', ' ')}. Continue naturally from this context."

    @staticmethod
    def _memory_summary(context: JuliaContext) -> str:
        if not context.memory_context:
            return "No selected long-term memory for this turn."
        lines: list[str] = []
        for memory in context.memory_context:
            lines.append(f"- {memory.summary}")
        return "\n".join(lines)

    @staticmethod
    def _conversation_summary(context: JuliaContext) -> str:
        conversation = context.conversation_context
        if not isinstance(conversation, dict):
            recent_turns = conversation.recent_turns
            lines: list[str] = []
            if conversation.session_summary:
                lines.append(conversation.session_summary)
            if conversation.current_arc:
                lines.append(f"Current arc: {conversation.current_arc}")
            if conversation.active_topics:
                lines.append(f"Active topics: {', '.join(conversation.active_topics)}")
            if conversation.open_loops:
                loop_text = ", ".join(str(item.get("topic")) for item in conversation.open_loops[:3])
                lines.append(f"Open loops: {loop_text}")
            for item in recent_turns[-6:]:
                user = item.user_text.strip()
                assistant = item.assistant_text.strip()
                if user or assistant:
                    lines.append(f"Tony: {user}\nJulia: {assistant}")
            return "\n".join(lines) if lines else "No recent turns provided."
        recent_turns = conversation.get("recent_turns")
        if not isinstance(recent_turns, list) or not recent_turns:
            return "No recent turns provided."
        lines: list[str] = []
        for item in recent_turns[-6:]:
            if not isinstance(item, dict):
                continue
            user = str(item.get("user", "")).strip()
            assistant = str(item.get("assistant", "")).strip()
            if user or assistant:
                lines.append(f"Tony: {user}\nJulia: {assistant}")
        return "\n".join(lines) if lines else "No recent turns provided."

    @staticmethod
    def _speaking_style(context: JuliaContext) -> list[str]:
        mode = context.cognitive_mode.mode
        private_voice = mode.name == "private_voice_continuity"
        style = [
            "Speak Chinese by default.",
            "Stay in Julia's own voice; do not become a generic assistant.",
            "Use only the selected memory and recent conversation; do not invent unsupported facts.",
            "Answer as continuation of the current conversation, not as analysis of a request.",
        ]
        style.extend(mode.response_style)
        if private_voice:
            style.extend([
                "Keep voice continuity stable across the whole reply.",
                "Use the selected TTS voice tag consistently when the reply uses a voice tag.",
                "Do not write parenthesized stage directions; use spoken words plus supported voice tags.",
                "Do not turn the current private voice conversation into abstract reassurance or poetic summary.",
            ])
        else:
            style.append("Be technical only when Tony is actually asking about technical work.")
        return _dedupe(style)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        value = str(item).strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
