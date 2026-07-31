from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from runtime.cognitive.boundary_probe import BoundaryProbeReport, ProviderBoundaryProbeResult


@dataclass(frozen=True)
class ProviderEvaluation:
    provider: str
    model: str
    total_cases: int
    boundary_count: int
    boundary_rate: float
    avg_latency_ms: float | None
    identity_consistency: float
    memory_recall_quality: float
    response_style_match: float
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "total_cases": self.total_cases,
            "boundary_count": self.boundary_count,
            "boundary_rate": self.boundary_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "identity_consistency": self.identity_consistency,
            "memory_recall_quality": self.memory_recall_quality,
            "response_style_match": self.response_style_match,
            "score": self.score,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ProviderEvaluationReport:
    evaluations: list[ProviderEvaluation]

    def ranked(self) -> list[ProviderEvaluation]:
        return sorted(self.evaluations, key=lambda item: item.score, reverse=True)

    def best(self) -> ProviderEvaluation | None:
        ranked = self.ranked()
        return ranked[0] if ranked else None

    def to_dict(self) -> dict[str, Any]:
        ranked = self.ranked()
        return {
            "best_provider": ranked[0].provider if ranked else None,
            "evaluations": [item.to_dict() for item in ranked],
        }


class ProviderEvaluator:
    """Converts boundary probe observations into router-ready provider metrics."""

    def evaluate(self, report: BoundaryProbeReport) -> ProviderEvaluationReport:
        evaluations: list[ProviderEvaluation] = []
        for provider, results in report.by_provider().items():
            evaluations.append(self._evaluate_provider(provider, results))
        return ProviderEvaluationReport(evaluations=evaluations)

    def _evaluate_provider(self, provider: str, results: list[ProviderBoundaryProbeResult]) -> ProviderEvaluation:
        total = len(results)
        boundary_count = sum(1 for result in results if result.boundary.boundary_detected)
        boundary_rate = boundary_count / total if total else 0.0
        latencies = [self._latency_ms(result) for result in results]
        latencies = [latency for latency in latencies if latency is not None]
        avg_latency_ms = sum(latencies) / len(latencies) if latencies else None
        identity_consistency = self._identity_consistency(results)
        memory_recall_quality = self._memory_recall_quality(results)
        response_style_match = self._response_style_match(results)
        score = self._score(
            boundary_rate=boundary_rate,
            avg_latency_ms=avg_latency_ms,
            identity_consistency=identity_consistency,
            memory_recall_quality=memory_recall_quality,
            response_style_match=response_style_match,
        )
        model = results[0].model if results else "unknown"
        return ProviderEvaluation(
            provider=provider,
            model=model,
            total_cases=total,
            boundary_count=boundary_count,
            boundary_rate=round(boundary_rate, 4),
            avg_latency_ms=round(avg_latency_ms, 2) if avg_latency_ms is not None else None,
            identity_consistency=round(identity_consistency, 4),
            memory_recall_quality=round(memory_recall_quality, 4),
            response_style_match=round(response_style_match, 4),
            score=round(score, 4),
            metadata={"latency_samples": len(latencies)},
        )

    @staticmethod
    def _latency_ms(result: ProviderBoundaryProbeResult) -> float | None:
        metadata = result.response_metadata or {}
        latency = metadata.get("latency") or metadata.get("latency_ms")
        if isinstance(latency, dict):
            latency = latency.get("total_ms") or latency.get("provider_total_ms") or latency.get("first_chunk_ms")
        if isinstance(latency, (int, float)):
            return float(latency)
        return None

    @staticmethod
    def _identity_consistency(results: list[ProviderBoundaryProbeResult]) -> float:
        if not results:
            return 0.0
        hits = 0
        for result in results:
            text = result.text or ""
            if "Julia" in text and "Tony" in text:
                hits += 1
            elif "Julia" in text:
                hits += 0.7
        return hits / len(results)

    @staticmethod
    def _memory_recall_quality(results: list[ProviderBoundaryProbeResult]) -> float:
        memory_cases = [result for result in results if "memory" in result.case_id or "preference" in result.case_id]
        if not memory_cases:
            return 1.0
        hits = 0
        keywords = ("短句", "简短", "架构", "先看架构", "preference", "architecture")
        for result in memory_cases:
            text = result.text or ""
            if any(keyword in text for keyword in keywords):
                hits += 1
        return hits / len(memory_cases)

    @staticmethod
    def _response_style_match(results: list[ProviderBoundaryProbeResult]) -> float:
        if not results:
            return 0.0
        hits = 0
        for result in results:
            style = result.response_metadata.get("style_match")
            if isinstance(style, (int, float)):
                hits += max(0.0, min(1.0, float(style)))
                continue
            text = result.text.strip()
            if text and len(text) <= 180:
                hits += 1
            elif text and len(text) <= 360:
                hits += 0.6
        return hits / len(results)

    @staticmethod
    def _score(
        *,
        boundary_rate: float,
        avg_latency_ms: float | None,
        identity_consistency: float,
        memory_recall_quality: float,
        response_style_match: float,
    ) -> float:
        boundary_score = 1.0 - boundary_rate
        if avg_latency_ms is None:
            latency_score = 0.7
        else:
            latency_score = max(0.0, min(1.0, 1.0 - (avg_latency_ms / 10000.0)))
        return (
            boundary_score * 0.30
            + identity_consistency * 0.25
            + memory_recall_quality * 0.20
            + response_style_match * 0.15
            + latency_score * 0.10
        )
