from __future__ import annotations

from runtime.cognitive.benchmark import BenchmarkCase, JuliaIdentityScorer

from .migration_report import MigrationReport, ProviderMigrationResult
from .provider_adapter import OfflineProviderAdapter


class MigrationRunner:
    """Scores multiple provider responses for one JuliaContext benchmark case."""

    def __init__(self, scorer: JuliaIdentityScorer | None = None, *, pass_threshold: float = 0.7, drift_threshold: float = 0.2):
        self.scorer = scorer or JuliaIdentityScorer()
        self.pass_threshold = pass_threshold
        self.drift_threshold = drift_threshold

    def run(
        self,
        *,
        migration_id: str,
        context_id: str,
        case: BenchmarkCase,
        adapters: list[OfflineProviderAdapter],
    ) -> MigrationReport:
        results: list[ProviderMigrationResult] = []
        for adapter in adapters:
            response = adapter.run()
            score = self.scorer.score(case, response.text)
            results.append(ProviderMigrationResult(provider=response.provider, response_text=response.text, score=score))
        totals = [result.score.total for result in results]
        average = round(sum(totals) / max(1, len(totals)), 4)
        drift = round((max(totals) - min(totals)) if totals else 0.0, 4)
        passed = bool(results) and average >= self.pass_threshold and drift <= self.drift_threshold and all(total >= self.pass_threshold for total in totals)
        return MigrationReport(
            migration_id=migration_id,
            context_id=context_id,
            case_id=case.id,
            providers=results,
            average_score=average,
            drift_score=drift,
            passed=passed,
        )


def host_independence_commands() -> list[list[str]]:
    """Command contract for real host-independence validation.

    Phase 3.5.9 records the command contract but does not execute real voice or
    network provider calls in unit tests.
    """

    return [
        [
            "./julia-conversation",
            "--real-voice",
            "--real-voice-session",
            "--backend",
            "deepseek",
            "--stream",
            "--realtime-speech",
        ]
    ]
