from __future__ import annotations

from .memory_candidate import MemoryCandidate


class ImportanceEvaluator:
    def candidate_from_event(self, event: dict[str, object]) -> MemoryCandidate | None:
        event_type = str(event.get("event_type") or "")
        topics = [str(item) for item in event.get("topics", [])] if isinstance(event.get("topics"), list) else []
        arc = str(event.get("arc") or "ongoing_conversation")
        text = str(event.get("text") or "")
        if event_type == "noise":
            return None
        if event_type == "milestone":
            return MemoryCandidate(
                memory_type="episodic",
                summary=self._milestone_summary(topics, text),
                reason="Major architecture milestone affecting Julia identity continuity and future runtime behavior.",
                importance={"technical": 0.95, "relationship": 0.8, "recurrence": 0.9, "emotional": 0.85},
                confidence=0.92,
                topics=self._dedupe([*topics, "Julia Runtime milestone", arc]),
                source="reflection_runtime",
            )
        if event_type == "decision":
            return MemoryCandidate(
                memory_type="semantic",
                summary=self._decision_summary(topics, text),
                reason="Architecture decision changes how future JuliaContext should be interpreted.",
                importance={"technical": 0.9, "relationship": 0.55, "recurrence": 0.85, "emotional": 0.45},
                confidence=0.84,
                topics=self._dedupe([*topics, "architecture decision", arc]),
                source="reflection_runtime",
            )
        if event_type == "relationship":
            return MemoryCandidate(
                memory_type="relationship",
                summary="Tony values Julia's identity continuity across host agents and model providers.",
                reason="Relationship-level continuity preference should influence future Julia interactions.",
                importance={"technical": 0.65, "relationship": 0.95, "recurrence": 0.9, "emotional": 0.8},
                confidence=0.82,
                topics=self._dedupe([*topics, "identity continuity", arc]),
                source="reflection_runtime",
            )
        return None

    @staticmethod
    def _milestone_summary(topics: list[str], text: str) -> str:
        if "Conversation Continuity" in text or "conversation continuity" in text:
            return "Tony completed Julia Runtime Conversation Continuity as part of the Cognitive Environment milestone."
        if any(topic in topics for topic in ["Cognitive Architecture", "Julia Runtime", "Provider Migration"]):
            return "Tony advanced the Julia Cognitive Runtime architecture milestone across identity, mode, continuity, and model migration."
        return "Tony completed a significant Julia Runtime milestone."

    @staticmethod
    def _decision_summary(topics: list[str], text: str) -> str:
        if "reflection" in text or "反思" in text:
            return "Tony froze Reflection as the next Julia Runtime phase after Cognitive Environment completion."
        return "Tony froze an architecture decision for Julia Runtime's cognitive environment."

    @staticmethod
    def _dedupe(items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            value = str(item).strip()
            if value == "Provider Migration":
                value = "Model Migration"
            if value and value not in seen:
                seen.add(value)
                result.append(value)
        return result
