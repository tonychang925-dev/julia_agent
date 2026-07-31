from __future__ import annotations

from dataclasses import dataclass

from audio.segment import SpeechSegment


@dataclass(frozen=True)
class STTResult:
    text: str
    ok: bool = True
    confidence: float = 1.0
    error: str | None = None


class MockSTTFinalizer:
    """Deterministic STT finalizer for Phase 3.2.2 tests."""

    def __init__(self, text: str = "Julia，在吗？"):
        self.text = text

    def finalize(self, segment: SpeechSegment) -> STTResult:
        if segment.duration_ms <= 0:
            return STTResult(text="", ok=False, confidence=0.0, error="empty segment")
        return STTResult(text=self.text, confidence=1.0)
