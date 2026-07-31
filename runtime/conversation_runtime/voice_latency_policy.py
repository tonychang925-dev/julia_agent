from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceLatencyPolicy:
    """Provider-message shaping for realtime voice latency.

    This policy is deliberately outside Persona/Relationship/Memory/Mode. It
    only adds delivery constraints for embodied voice: short first sentence,
    bounded total length, and TTS-friendly formatting.  Cognitive ownership is
    unchanged; selected memory and recent turns remain intact.
    """

    enabled: bool = False
    max_tokens: int = 320
    first_sentence_chars: int = 24
    max_sentences: int = 8
    protected_terms: tuple[str, ...] = ("Julia Runtime", "Julia", "Tony", "Cognitive Runtime", "Memory Runtime", "Persona Package")

    def apply(self, messages: list[dict[str, str]], metadata: dict[str, object]) -> list[dict[str, str]]:
        if not self.enabled:
            return messages
        optimized = [dict(message) for message in messages]
        if not optimized:
            return optimized
        policy_text = self._policy_text()
        if optimized[0].get("role") == "system":
            optimized[0]["content"] = f"{optimized[0].get('content', '').rstrip()}\n\n{policy_text}"
        else:
            optimized.insert(0, {"role": "system", "content": policy_text})
        metadata["voice_latency_policy"] = {
            "enabled": True,
            "first_sentence_chars": self.first_sentence_chars,
            "max_sentences": self.max_sentences,
            "max_tokens": self.max_tokens,
            "scope": "voice_delivery_only",
            "semantic_guard": {
                "scope": "core_object_preservation",
                "protected_terms": list(self.protected_terms),
            },
        }
        return optimized

    def _policy_text(self) -> str:
        return (
            "Voice latency policy:\n"
            f"- Start with one complete, self-contained spoken first sentence within {self.first_sentence_chars} Chinese characters when possible; end it with 。 before giving details.\n"
            f"- Keep the whole voice reply within {self.max_sentences} short spoken sentences unless Tony explicitly asks for detail.\n"
            "- Do not use markdown, bullet lists, code fences, or parenthesized stage directions in voice output.\n"
            "- Preserve core objects: say Julia Runtime / Julia / Tony / Persona Package when those are the actual topic; do not replace them with vague phrases like 这个项目, 你的系统, 身份系统, or 那个东西.\n"
            "- Preserve Julia identity, selected memory, relationship continuity, and cognitive mode; this policy only controls delivery length."
        )
