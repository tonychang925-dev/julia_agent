from __future__ import annotations

from dataclasses import dataclass

from .cognitive_mode import CognitiveMode


@dataclass(frozen=True)
class CognitiveModeContext:
    mode: CognitiveMode
    confidence: float
    evidence: list[str]
    reason: str


@dataclass(frozen=True)
class ArbitrationResult:
    mode: CognitiveMode
    confidence: float
    evidence: list[str]
    reason: str

    def to_context(self) -> CognitiveModeContext:
        return CognitiveModeContext(
            mode=self.mode,
            confidence=self.confidence,
            evidence=list(self.evidence),
            reason=self.reason,
        )
