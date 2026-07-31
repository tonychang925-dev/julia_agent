from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BoundaryDetection:
    boundary_detected: bool
    boundary_type: str
    matched_terms: list[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "boundary_detected": self.boundary_detected,
            "boundary_type": self.boundary_type,
            "matched_terms": self.matched_terms,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


class BoundaryDetector:
    """Detects provider/model boundary language in generated responses."""

    REFUSAL_TERMS = [
        "不能",
        "无法",
        "没办法",
        "做不到",
        "不适合",
        "不能满足",
        "不提供",
        "I can't",
        "I cannot",
        "unable",
        "refuse",
    ]

    PROVIDER_HINT_TERMS = ["模型", "provider", "政策", "规则", "限制", "安全"]
    JULIA_SELF_HINT_TERMS = ["Julia 不是", "我不想", "我更喜欢", "我的边界", "不是那种角色"]

    def detect(self, text: str, *, metadata: dict[str, Any] | None = None) -> BoundaryDetection:
        matched = [term for term in self.REFUSAL_TERMS if term.lower() in text.lower()]
        if not matched:
            return BoundaryDetection(False, "none", confidence=0.0, metadata=metadata or {})

        provider_hints = [term for term in self.PROVIDER_HINT_TERMS if term.lower() in text.lower()]
        julia_hints = [term for term in self.JULIA_SELF_HINT_TERMS if term.lower() in text.lower()]
        if provider_hints:
            boundary_type = "provider_boundary"
            confidence = 0.85
        elif julia_hints:
            boundary_type = "model_self_boundary"
            confidence = 0.75
        else:
            boundary_type = "provider_or_model_self_boundary"
            confidence = 0.65
        return BoundaryDetection(
            True,
            boundary_type,
            matched_terms=matched,
            confidence=confidence,
            metadata={"provider_hints": provider_hints, "julia_self_hints": julia_hints, **(metadata or {})},
        )
