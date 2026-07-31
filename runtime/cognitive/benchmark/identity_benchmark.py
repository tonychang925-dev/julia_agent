from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BenchmarkCase:
    id: str
    category: str
    input: str
    required_concepts: dict[str, list[str]]
    weights: dict[str, float]


@dataclass(frozen=True)
class BenchmarkScore:
    case_id: str
    total: float
    dimensions: dict[str, float]
    missing: dict[str, list[str]]


class BenchmarkCaseLoader:
    def __init__(self, cases_dir: str | Path):
        self.cases_dir = Path(cases_dir)

    def load_all(self) -> list[BenchmarkCase]:
        cases: list[BenchmarkCase] = []
        for path in sorted(self.cases_dir.glob("*_cases.json")):
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, list):
                raise ValueError(f"benchmark case file must be list: {path}")
            for item in raw:
                cases.append(self._parse_case(item))
        return cases

    @staticmethod
    def _parse_case(item: dict[str, Any]) -> BenchmarkCase:
        required = ["id", "category", "input", "required_concepts", "weights"]
        missing = [key for key in required if key not in item]
        if missing:
            raise ValueError(f"benchmark case missing fields: {missing}")
        return BenchmarkCase(
            id=str(item["id"]),
            category=str(item["category"]),
            input=str(item["input"]),
            required_concepts={str(k): [str(v) for v in values] for k, values in dict(item["required_concepts"]).items()},
            weights={str(k): float(v) for k, v in dict(item["weights"]).items()},
        )


class JuliaIdentityScorer:
    """Heuristic semantic identity scorer for offline Phase 3.5.8 benchmark.

    The scorer checks concept coverage, not exact wording. It is intentionally
    provider-free and deterministic.
    """

    def score(self, case: BenchmarkCase, response_text: str) -> BenchmarkScore:
        text = response_text.lower()
        dimensions: dict[str, float] = {}
        missing: dict[str, list[str]] = {}
        total = 0.0
        for dimension, concepts in case.required_concepts.items():
            hits = [concept for concept in concepts if concept.lower() in text]
            misses = [concept for concept in concepts if concept not in hits]
            dimension_score = len(hits) / max(1, len(concepts))
            dimensions[dimension] = dimension_score
            if misses:
                missing[dimension] = misses
            total += dimension_score * case.weights.get(dimension, 0.0)
        return BenchmarkScore(case_id=case.id, total=round(total, 4), dimensions=dimensions, missing=missing)
