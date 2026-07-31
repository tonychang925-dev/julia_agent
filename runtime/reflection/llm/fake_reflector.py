from __future__ import annotations

from runtime.reflection.memory_candidate import MemoryCandidate
from runtime.reflection.reflection_input import ReflectionInput

from .llm_reflector import LLMReflectionResult, LLMReflector


class FakeLLMReflector(LLMReflector):
    """Offline deterministic reflector for architecture tests."""

    def reflect(self, reflection_input: ReflectionInput) -> LLMReflectionResult:
        text = "\n".join(f"{turn.user_text}\n{turn.assistant_text}" for turn in reflection_input.recent_turns).lower()
        events: list[dict[str, object]] = []
        candidates: list[MemoryCandidate] = []
        if "directllmbridge" in text or "host independence" in text or "脱离 claude" in text or "独立运行" in text:
            events.append({"event_type": "project_milestone", "source": "fake_llm"})
            candidates.append(
                MemoryCandidate(
                    memory_type="episodic",
                    summary="Julia Runtime achieved host independence through DirectLLMBridge.",
                    reason="LLM interpreted this as a project milestone; Runtime must still validate and govern it.",
                    importance={"technical": 0.95, "relationship": 0.75, "recurrence": 0.85, "emotional": 0.75},
                    confidence=0.91,
                    topics=["Julia Runtime", "Host Independence", "DirectLLMBridge"],
                    source="llm_reflection_fake",
                )
            )
        if not candidates:
            events.append({"event_type": "noise", "source": "fake_llm"})
        return LLMReflectionResult(
            extracted_events=events,
            memory_candidates=candidates,
            confidence=0.9 if candidates else 0.55,
            explanation="offline fake reflection for deterministic Phase 3.6.5 validation",
        )
