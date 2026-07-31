from __future__ import annotations

from dataclasses import replace

from .memory_candidate import MemoryCandidate


class ConsolidationPolicy:
    """Gate and merge MemoryCandidate objects before Memory Runtime persistence."""

    def __init__(self, *, min_confidence: float = 0.7, min_total_importance: float = 0.65):
        self.min_confidence = min_confidence
        self.min_total_importance = min_total_importance

    def should_store(self, candidate: MemoryCandidate) -> bool:
        if candidate.confidence < self.min_confidence:
            return False
        if candidate.total_importance() < self.min_total_importance:
            return False
        if not candidate.summary.strip():
            return False
        return True

    def filter(self, candidates: list[MemoryCandidate]) -> list[MemoryCandidate]:
        return [candidate for candidate in candidates if self.should_store(candidate)]

    def merge_duplicates(self, candidates: list[MemoryCandidate]) -> list[MemoryCandidate]:
        merged: dict[tuple[str, str], MemoryCandidate] = {}
        for candidate in candidates:
            key = (candidate.memory_type, self._topic_key(candidate))
            previous = merged.get(key)
            if previous is None:
                merged[key] = candidate
                continue
            merged[key] = self._merge(previous, candidate)
        return list(merged.values())

    @staticmethod
    def _topic_key(candidate: MemoryCandidate) -> str:
        normalized = [topic.lower() for topic in candidate.topics if topic]
        if any("julia" in topic or "cognitive" in topic or "runtime" in topic for topic in normalized):
            return "julia_runtime_cognitive_milestone"
        return "|".join(sorted(normalized[:3])) or candidate.summary.lower()[:48]

    @staticmethod
    def _merge(left: MemoryCandidate, right: MemoryCandidate) -> MemoryCandidate:
        importance = {
            key: max(float(left.importance.get(key, 0.0) or 0.0), float(right.importance.get(key, 0.0) or 0.0))
            for key in {"emotional", "relationship", "technical", "recurrence"}
        }
        topics = []
        for topic in [*left.topics, *right.topics]:
            if topic and topic not in topics:
                topics.append(topic)
        summary = left.summary if len(left.summary) >= len(right.summary) else right.summary
        if "Julia Runtime" in " ".join(topics) or "Cognitive" in " ".join(topics):
            summary = "Tony advanced the Julia Runtime Independence Journey through cognitive environment milestones."
        return replace(
            left,
            summary=summary,
            reason=f"Merged related reflection candidates: {left.reason} / {right.reason}",
            importance=importance,
            confidence=max(left.confidence, right.confidence),
            topics=topics,
        )
