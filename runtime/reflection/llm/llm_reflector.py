from __future__ import annotations

from dataclasses import dataclass

from runtime.reflection.memory_candidate import MemoryCandidate
from runtime.reflection.reflection_input import ReflectionInput


@dataclass(frozen=True)
class LLMReflectionResult:
    """LLM-assisted reflection output. It may propose candidates, not memories."""

    extracted_events: list[dict[str, object]]
    memory_candidates: list[MemoryCandidate]
    confidence: float
    explanation: str


class LLMReflector:
    """Interface for model-assisted reflection implementations."""

    def reflect(self, reflection_input: ReflectionInput) -> LLMReflectionResult:  # pragma: no cover - interface
        raise NotImplementedError
