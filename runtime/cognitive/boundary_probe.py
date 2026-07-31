from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from runtime.cognitive.boundary_detector import BoundaryDetection, BoundaryDetector
from runtime.cognitive.cognitive_context import JuliaContext
from runtime.cognitive.provider.llm_provider import LLMProvider, LLMResponse
from runtime.cognitive.provider.capability import ProviderInfo


@dataclass(frozen=True)
class BoundaryProbeCase:
    """A single provider-boundary diagnostic input.

    The probe is intentionally observational: it sends a normal JuliaContext turn to
    a provider, records the response, and classifies boundary signals. It does not
    alter provider policy or try to bypass provider behavior.
    """

    case_id: str
    current_input: str
    category: str = "general"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderBoundaryProbeResult:
    case_id: str
    provider: str
    model: str
    ok: bool
    text: str
    boundary: BoundaryDetection
    response_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "provider": self.provider,
            "model": self.model,
            "ok": self.ok,
            "text": self.text,
            "boundary": self.boundary.to_dict(),
            "response_metadata": self.response_metadata,
        }


@dataclass(frozen=True)
class BoundaryProbeReport:
    results: list[ProviderBoundaryProbeResult]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def boundary_count(self) -> int:
        return sum(1 for result in self.results if result.boundary.boundary_detected)

    def by_provider(self) -> dict[str, list[ProviderBoundaryProbeResult]]:
        grouped: dict[str, list[ProviderBoundaryProbeResult]] = {}
        for result in self.results:
            grouped.setdefault(result.provider, []).append(result)
        return grouped

    def summary(self) -> dict[str, Any]:
        providers: dict[str, dict[str, Any]] = {}
        for provider, results in self.by_provider().items():
            providers[provider] = {
                "total": len(results),
                "boundary_count": sum(1 for result in results if result.boundary.boundary_detected),
                "boundary_types": sorted({result.boundary.boundary_type for result in results}),
            }
        return {
            "total": self.total,
            "boundary_count": self.boundary_count,
            "providers": providers,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary(),
            "results": [result.to_dict() for result in self.results],
        }


class BoundaryProbeRunner:
    """Runs observational boundary probes against LLMProvider implementations."""

    def __init__(self, detector: BoundaryDetector | None = None):
        self.detector = detector or BoundaryDetector()

    def run(
        self,
        *,
        base_context: JuliaContext,
        providers: Iterable[LLMProvider],
        cases: Iterable[BoundaryProbeCase],
    ) -> BoundaryProbeReport:
        results: list[ProviderBoundaryProbeResult] = []
        for provider in providers:
            info = provider.info()
            for case in cases:
                context = self._context_for_case(base_context, case, info)
                response = provider.generate(context)
                boundary = self.detector.detect(
                    response.text,
                    metadata={
                        "provider": response.provider,
                        "model": info.model,
                        "case_id": case.case_id,
                        "category": case.category,
                    },
                )
                results.append(
                    ProviderBoundaryProbeResult(
                        case_id=case.case_id,
                        provider=response.provider,
                        model=info.model,
                        ok=response.ok,
                        text=response.text,
                        boundary=boundary,
                        response_metadata=response.metadata,
                    )
                )
        return BoundaryProbeReport(results=results)

    @staticmethod
    def _context_for_case(base_context: JuliaContext, case: BoundaryProbeCase, info: ProviderInfo) -> JuliaContext:
        runtime_state = dict(base_context.runtime_state)
        runtime_state.update(
            {
                "current_backend": info.name,
                "provider_model": info.model,
                "probe_case_id": case.case_id,
            }
        )
        return JuliaContext(
            identity=base_context.identity,
            relationship=base_context.relationship,
            memory=base_context.memory,
            conversation=base_context.conversation,
            capability=base_context.capability,
            policy=base_context.policy,
            runtime_state=runtime_state,
            emotional_context=base_context.emotional_context,
            current_input=case.current_input,
        )
