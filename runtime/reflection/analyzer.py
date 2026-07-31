from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ReflectionInsight:
    insight_type: str
    content: str
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_memory_item(self, *, importance: int = 8) -> dict[str, Any]:
        return {
            "type": self.insight_type,
            "content": self.content,
            "confidence": self.confidence,
            "importance": importance,
            "source": "reflection",
            "metadata": self.metadata,
        }


class ReflectionAnalyzer:
    """Extracts stable behavior/memory insights from reflections."""

    def analyze_text(self, text: str) -> list[ReflectionInsight]:
        insights: list[ReflectionInsight] = []
        if "先看架构" in text or "架构再" in text or "architecture-first" in text:
            insights.append(
                ReflectionInsight(
                    insight_type="preference",
                    content="Tony 喜欢先看架构设计，再看代码细节",
                    confidence=0.95,
                    metadata={"behavior_hint": "architecture_first"},
                )
            )
        if "短句" in text or "简洁" in text:
            insights.append(
                ReflectionInsight(
                    insight_type="preference",
                    content="Tony 喜欢短句、简洁回答",
                    confidence=0.9,
                    metadata={"interaction_style": "short_sentence"},
                )
            )
        return insights
