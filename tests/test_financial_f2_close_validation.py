"""F2 close validation acceptance tests.

Traceability: docs/project_control/PHASE_CONTRACT_F2.md
"""

from __future__ import annotations

import ast
import dataclasses
from datetime import date, datetime
from pathlib import Path

import pytest

from runtime.capability.financial.client.ai_theme_client import AIThemeFinancialClient
from runtime.capability.financial.contracts import (
    CandidateTruth,
    CloseValidationResult,
    ErrorAttribution,
    InvestmentCaseEvaluation,
    MarketTruthSnapshot,
)
from runtime.capability.financial.workflows.close_review import run_close_validation
from runtime.capability.financial.workflows.premarket import run_premarket_research

VALID_STATUSES = {
    "CONFIRMED",
    "PARTIALLY_CONFIRMED",
    "FALSIFIED",
    "NOT_TRIGGERED",
    "EXPIRED",
    "INVALIDATED_BY_RISK",
    "INSUFFICIENT_DATA",
}
FORBIDDEN_TRADE_TERMS = ("buy", "sell", "open_position", "close_position", "order", "execute", "正式推荐", "交易建议")


@pytest.fixture()
def premarket_report():
    bundle = AIThemeFinancialClient.fixture_client().get_market_brief(date(2026, 8, 1), context_type="premarket")
    return run_premarket_research(bundle)


@pytest.fixture()
def evidence_ref(premarket_report):
    return premarket_report.evidence_refs[0]


@pytest.fixture()
def truth_snapshot(premarket_report, evidence_ref) -> MarketTruthSnapshot:
    return MarketTruthSnapshot(
        truth_snapshot_id="truth-20260801-close-fixture",
        trade_date=premarket_report.trade_date,
        as_of=datetime(2026, 8, 1, 15, 30, 0),
        market_close_state="mixed_rotation",
        risk_level="MODERATE",
        candidate_truths=(
            CandidateTruth(
                stock_code="000988",
                stock_name="华工科技",
                entry_condition_triggered=False,
                confirmation_condition_triggered=False,
                invalidation_condition_triggered=False,
                risk_invalidated=False,
                outcome="up_without_entry_trigger",
                return_pct=0.08,
                evidence_refs=(evidence_ref,),
            ),
        ),
        source_snapshot_ids=("truth-close-20260801",),
        evidence_refs=(evidence_ref,),
        producer_version="truth.fixture.v1",
    )


@pytest.fixture()
def falsified_truth_snapshot(premarket_report, evidence_ref) -> MarketTruthSnapshot:
    return MarketTruthSnapshot(
        truth_snapshot_id="truth-20260801-falsified-fixture",
        trade_date=premarket_report.trade_date,
        as_of=datetime(2026, 8, 1, 15, 30, 0),
        market_close_state="failed_breakout",
        risk_level="HIGH",
        candidate_truths=(
            CandidateTruth(
                stock_code="000988",
                stock_name="华工科技",
                entry_condition_triggered=True,
                confirmation_condition_triggered=True,
                invalidation_condition_triggered=True,
                risk_invalidated=False,
                outcome="triggered_then_failed",
                return_pct=-0.04,
                evidence_refs=(evidence_ref,),
            ),
        ),
        source_snapshot_ids=("truth-close-20260801-falsified",),
        evidence_refs=(evidence_ref,),
        producer_version="truth.fixture.v1",
    )


# F2-TC-01 / F2-AT-01
def test_close_validation_does_not_mutate_premarket_report(premarket_report, truth_snapshot) -> None:
    before = premarket_report
    result = run_close_validation(premarket_report, truth_snapshot)

    assert premarket_report == before
    assert result.premarket_report_id == premarket_report.report_id
    with pytest.raises(dataclasses.FrozenInstanceError):
        premarket_report.status = "mutated"  # type: ignore[misc]


# F2-TC-02 / F2-AT-02
def test_market_truth_snapshot_contract_is_frozen_and_evidence_backed(truth_snapshot) -> None:
    assert dataclasses.is_dataclass(truth_snapshot)
    assert truth_snapshot.truth_snapshot_id
    assert truth_snapshot.candidate_truths
    assert truth_snapshot.evidence_refs
    with pytest.raises(dataclasses.FrozenInstanceError):
        truth_snapshot.risk_level = "LOW"  # type: ignore[misc]


# F2-TC-03 / F2-AT-03
def test_each_investment_case_gets_valid_evaluation_status(premarket_report, truth_snapshot) -> None:
    result = run_close_validation(premarket_report, truth_snapshot)

    assert isinstance(result, CloseValidationResult)
    assert len(result.evaluations) == len(premarket_report.investment_cases)
    assert all(isinstance(item, InvestmentCaseEvaluation) for item in result.evaluations)
    assert {item.status for item in result.evaluations} <= VALID_STATUSES


# F2-TC-04 / F2-AT-04
def test_close_validation_distinguishes_not_triggered_from_falsified(premarket_report, truth_snapshot, falsified_truth_snapshot) -> None:
    not_triggered_result = run_close_validation(premarket_report, truth_snapshot)
    falsified_result = run_close_validation(premarket_report, falsified_truth_snapshot)

    assert not_triggered_result.evaluations[0].status == "NOT_TRIGGERED"
    assert falsified_result.evaluations[0].status == "FALSIFIED"


# F2-TC-05 / F2-AT-05
def test_error_attribution_required_for_non_confirmed_cases(premarket_report, truth_snapshot) -> None:
    result = run_close_validation(premarket_report, truth_snapshot)

    evaluation = result.evaluations[0]
    assert evaluation.status != "CONFIRMED"
    assert isinstance(evaluation.error_attribution, ErrorAttribution)
    assert evaluation.error_attribution.category
    assert evaluation.error_attribution.dimensions
    assert evaluation.error_attribution.explanation
    assert evaluation.error_attribution.evidence_refs


# F2-TC-06 / F2-AT-06
def test_close_validation_summary_metrics_are_reported(premarket_report, truth_snapshot) -> None:
    result = run_close_validation(premarket_report, truth_snapshot)

    assert 0.0 <= result.summary.thesis_accuracy <= 1.0
    assert 0.0 <= result.summary.trigger_accuracy <= 1.0
    assert 0.0 <= result.summary.risk_accuracy <= 1.0
    assert result.summary.evaluation_count == len(result.evaluations)


# F2-TC-07 / F2-AT-07
def test_close_validation_outputs_have_evidence_refs(premarket_report, truth_snapshot) -> None:
    result = run_close_validation(premarket_report, truth_snapshot)

    assert truth_snapshot.evidence_refs
    assert result.evidence_refs
    assert result.summary.evidence_refs
    assert all(item.evidence_refs for item in result.evaluations)
    assert all(item.error_attribution is None or item.error_attribution.evidence_refs for item in result.evaluations)


# F2-TC-08 / F2-AT-08
def test_close_validation_preserves_replay_identity(premarket_report, truth_snapshot) -> None:
    result = run_close_validation(premarket_report, truth_snapshot)

    assert result.premarket_input_hash == premarket_report.input_hash
    assert result.source_bundle_id == premarket_report.source_bundle_id
    assert result.source_snapshot_ids == premarket_report.source_snapshot_ids
    assert result.truth_snapshot_id == truth_snapshot.truth_snapshot_id


# F2-TC-09 / F2-AT-09
def test_f2_does_not_emit_trade_decisions_or_orders(premarket_report, truth_snapshot) -> None:
    result = run_close_validation(premarket_report, truth_snapshot)
    serialized = repr(result).lower()

    assert not any(term in serialized for term in FORBIDDEN_TRADE_TERMS)


# F2-TC-10 / F2-AT-10
def test_f2_does_not_modify_strategy_memory_or_world_model() -> None:
    path = Path("runtime/capability/financial/workflows/close_review.py")
    source = path.read_text().lower()
    forbidden = ("write_strategy", "update_strategy", "world_model", "risk_gate.update", "memory.write", "knowledge_base")
    assert not any(term in source for term in forbidden)


# F2-TC-11 / F2-AT-11
def test_close_validation_is_replayable_from_same_inputs(premarket_report, truth_snapshot) -> None:
    result_1 = run_close_validation(premarket_report, truth_snapshot)
    result_2 = run_close_validation(premarket_report, truth_snapshot)

    assert result_1 == result_2
    assert result_1.evaluator_version == "deterministic_f2_v1"
    assert result_1.status == "shadow"


# F2-TC-12 / F2-AT-12
def test_f2_modules_do_not_import_database_memory_or_ai_theme_internals() -> None:
    path = Path("runtime/capability/financial/workflows/close_review.py")
    tree = ast.parse(path.read_text())
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    forbidden_prefixes = ("ai_theme_app", "sqlalchemy", "psycopg", "sqlite3", "memory")
    assert [name for name in imports if name.startswith(forbidden_prefixes)] == []
