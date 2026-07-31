from __future__ import annotations

from .event_extractor import EventExtractor
from .importance_evaluator import ImportanceEvaluator
from .memory_candidate import MemoryCandidate
from .reflection_input import ReflectionInput
from .reflection_policy import ConsolidationPolicy
from .llm import CandidateValidator, LLMReflector


class ReflectionEngine:
    """Experience -> event signals -> gated, merged memory candidates."""

    def __init__(
        self,
        *,
        extractor: EventExtractor | None = None,
        evaluator: ImportanceEvaluator | None = None,
        policy: ConsolidationPolicy | None = None,
    ):
        self.extractor = extractor or EventExtractor()
        self.evaluator = evaluator or ImportanceEvaluator()
        self.policy = policy or ConsolidationPolicy()

    def reflect(self, reflection_input: ReflectionInput) -> list[MemoryCandidate]:
        events = self.extractor.extract(
            reflection_input.recent_turns,
            active_topics=reflection_input.active_topics,
            conversation_arc=reflection_input.conversation_arc,
        )
        candidates = [candidate for event in events if (candidate := self.evaluator.candidate_from_event(event)) is not None]
        return self.policy.merge_duplicates(self.policy.filter(candidates))

    def reflect_with_llm(self, reflection_input: ReflectionInput, reflector: LLMReflector) -> list[MemoryCandidate]:
        result = reflector.reflect(reflection_input)
        validated = CandidateValidator().validate_many(list(result.memory_candidates))
        return self.policy.merge_duplicates(self.policy.filter(validated))
