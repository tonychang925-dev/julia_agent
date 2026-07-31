from __future__ import annotations

from dataclasses import dataclass

from runtime.cognitive.benchmark import BenchmarkScore


@dataclass(frozen=True)
class ProviderMigrationResult:
    provider: str
    response_text: str
    score: BenchmarkScore


@dataclass(frozen=True)
class MigrationReport:
    migration_id: str
    context_id: str
    case_id: str
    providers: list[ProviderMigrationResult]
    average_score: float
    drift_score: float
    passed: bool
