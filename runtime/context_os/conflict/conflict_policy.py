from __future__ import annotations

from dataclasses import dataclass

from .resolution import ConflictItem


@dataclass(frozen=True)
class ConflictPolicy:
    """Authority model for context conflict resolution.

    Priority follows Julia Cognitive Ownership: current explicit user facts and
    governed memory outrank diary/imported context, which outranks assistant
    historical answers and model inference.
    """

    def priority(self, item: ConflictItem) -> float:
        provenance = (item.provenance or "").lower()
        source = item.source_type.lower()
        speaker = (item.speaker or "").lower()
        base = item.authority
        if provenance == "current_user_intent":
            return 1.20 + base
        if provenance in {"current_user_fact", "explicit_user", "tony_input"}:
            return 1.10 + base
        if provenance in {"governed_memory", "memory_governed"} or source == "memory":
            return 0.95 + base
        if speaker == "tony" and source == "archive":
            return 0.90 + base
        if source == "diary" or provenance == "imported_diary":
            return 0.80 + base
        if provenance in {"compact_generated", "reflection_generated"}:
            return 0.65 + base
        if speaker in {"julia", "assistant", "model"} or provenance in {"assistant_response", "llm_reflection", "model_inference"}:
            return 0.25 + base
        return 0.50 + base
