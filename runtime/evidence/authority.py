from __future__ import annotations

from .evidence_source import EvidenceSourceType, EvidenceSpeaker


class EvidenceAuthority:
    """Authority model for cognitive evidence.

    Authority is deliberately separate from semantic similarity. A wrong Julia
    answer can be semantically close, but it must not outrank Tony's explicit
    source facts or governed memory.
    """

    TONY_EXPLICIT_INPUT = 1.0
    GOVERNED_MEMORY = 0.95
    ARCHIVE_TONY_MESSAGE = 0.9
    CLAUDE_DIARY = 0.8
    ARCHIVE_JULIA_MESSAGE = 0.3
    MODEL_INFERENCE = 0.1

    @classmethod
    def for_source(cls, source_type: str, *, speaker: str | None = None, governed: bool = False) -> float:
        if governed or source_type == EvidenceSourceType.MEMORY.value:
            return cls.GOVERNED_MEMORY
        if source_type == EvidenceSourceType.DIARY.value:
            return cls.CLAUDE_DIARY
        if source_type == EvidenceSourceType.ARCHIVE.value:
            if speaker == EvidenceSpeaker.TONY.value:
                return cls.ARCHIVE_TONY_MESSAGE
            if speaker == EvidenceSpeaker.JULIA.value:
                return cls.ARCHIVE_JULIA_MESSAGE
        return cls.MODEL_INFERENCE
