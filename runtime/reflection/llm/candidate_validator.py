from __future__ import annotations

from dataclasses import dataclass

from runtime.reflection.memory_candidate import MemoryCandidate

_RUNTIME_FORBIDDEN = ["provider", "backend", "deepseek", "claude-code", "latency", "tts", "stt", "session_id", "turn_id"]


@dataclass(frozen=True)
class CandidateValidationResult:
    accepted: bool
    candidate: MemoryCandidate | None
    reason: str


class CandidateValidator:
    """Validates LLM-proposed MemoryCandidate objects before policy/persistence."""

    def validate(self, candidate: object) -> CandidateValidationResult:
        if not isinstance(candidate, MemoryCandidate):
            return CandidateValidationResult(False, None, "LLM output must be MemoryCandidate, not MemoryObject or raw dict")
        if self._has_runtime_leakage(candidate):
            return CandidateValidationResult(False, None, "candidate contains runtime metadata")
        if candidate.confidence < 0.0 or candidate.confidence > 1.0:
            return CandidateValidationResult(False, None, "candidate confidence out of range")
        if not candidate.summary.strip():
            return CandidateValidationResult(False, None, "candidate summary missing")
        return CandidateValidationResult(True, candidate, "candidate accepted")

    def validate_many(self, candidates: list[object]) -> list[MemoryCandidate]:
        accepted: list[MemoryCandidate] = []
        for candidate in candidates:
            result = self.validate(candidate)
            if result.accepted and result.candidate is not None:
                accepted.append(result.candidate)
        return accepted

    @staticmethod
    def _has_runtime_leakage(candidate: MemoryCandidate) -> bool:
        text = str(candidate).lower()
        return any(token in text for token in _RUNTIME_FORBIDDEN)
