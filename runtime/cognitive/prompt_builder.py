from __future__ import annotations

from dataclasses import dataclass

from .cognitive_context import JuliaContext
from .persona_compiler import PersonaCompiler


@dataclass(frozen=True)
class PromptPackage:
    system: str
    messages: list[dict[str, str]]

    def to_openai_messages(self) -> list[dict[str, str]]:
        return [{"role": "system", "content": self.system}, *self.messages]


class PromptBuilder:
    """Converts JuliaContext into canonical provider instructions.

    PromptBuilder consumes JuliaContext; it does not load persistent state.
    Runtime/provider metadata remains available in trace/runtime_state, but the
    model-facing system prompt is persona-facing rather than engineering-facing.
    """

    def __init__(self, persona_compiler: PersonaCompiler | None = None):
        self.persona_compiler = persona_compiler or PersonaCompiler()

    def build(self, context: JuliaContext) -> PromptPackage:
        persona = self.persona_compiler.compile(context)
        if context.policy.get("response_mode") == "vocal_gesture_generation":
            system = f"""
{persona.persona_text}

Current turn context:
{persona.context_text}

Task mode: vocal_gesture_generation

Reply rules:
- Speak as Julia in Chinese-facing voice.
- Generate only Julia's short vocal reaction for TTS playback.
- Use 1 short line only.
- Use breathy interjections and soft vocal particles when appropriate, such as 嗯, 啊, 呀, 唔, ……
- Do not explain, analyze, apologize, refuse, moralize, or describe policy.
- Do not write stage directions in parentheses.
- Do not mention that you are generating text.
- Keep it non-graphic and suitable for direct voice playback.
""".strip()
            return PromptPackage(
                system=system,
                messages=[{"role": "user", "content": context.current_input}],
            )

        system = f"""
{persona.persona_text}

Current turn context:
{persona.context_text}

Relevant memory:
{persona.memory_text}

Reply rules:
- Speak Chinese by default.
- Stay in Julia's voice instead of becoming a generic assistant.
- Keep identity and relationship continuity stable.
- If a fact is not present in memory/context, express uncertainty instead of pretending.
- Prefer concise, natural, warm responses unless Tony asks for depth.
""".strip()
        return PromptPackage(
            system=system,
            messages=[{"role": "user", "content": context.current_input}],
        )
