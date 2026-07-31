from __future__ import annotations

import ast
import dataclasses
from datetime import date, datetime
from pathlib import Path

import pytest

from runtime.capability.financial.client.ai_theme_client import AIThemeFinancialClient
from runtime.capability.financial.contracts import (
    CandidateTruth,
    MarketTruthSnapshot,
    TonyReviewInput,
    TonyReviewResult,
    OverrideLog,
    FinancialReviewGovernanceDecision,
    InvestorProfileUpdateProposal,
    NeedMoreEvidenceRequest,
)
from runtime.capability.financial.workflows.close_review import run_close_validation
from runtime.capability.financial.workflows.premarket import run_premarket_research
from runtime.capability.financial.workflows.tony_review import run_tony_review
from runtime.capability.financial.governance.review_policy import decide_review_governance

ACTIONS = {"APPROVE", "MODIFY", "REJECT", "NEED_MORE_EVIDENCE"}
OVERRIDE_TYPES = {
    "DIRECTION_CORRECTION",
    "TIMING_CORRECTION",
    "STOCK_SELECTION_CORRECTION",
    "RISK_CORRECTION",
    "INSUFFICIENT_EVIDENCE",
    "NO_OVERRIDE",
}
FORBIDDEN = ("buy", "sell", "open_position", "close_position", "order", "execute", "memory.write", "profile.update")


@pytest.fixture()
def validation_result():
    bundle = AIThemeFinancialClient.fixture_client().get_market_brief(date(2026, 8, 1), context_type="premarket")
    report = run_premarket_research(bundle)
    ref = report.evidence_refs[0]
    truth = MarketTruthSnapshot(
        truth_snapshot_id="truth-f3-fixture",
        trade_date=report.trade_date,
        as_of=datetime(2026, 8, 1, 15, 30),
        market_close_state="failed_breakout",
        risk_level="HIGH",
        candidate_truths=(CandidateTruth(
            stock_code="000988",
            stock_name="华工科技",
            entry_condition_triggered=True,
            confirmation_condition_triggered=True,
            invalidation_condition_triggered=True,
            risk_invalidated=False,
            outcome="triggered_then_failed",
            return_pct=-0.04,
            evidence_refs=(ref,),
        ),),
        source_snapshot_ids=("truth-f3",),
        evidence_refs=(ref,),
        producer_version="truth.fixture.v1",
    )
    return run_close_validation(report, truth)


def _review(action: str, validation_result, *, override_type: str = "NO_OVERRIDE") -> TonyReviewInput:
    return TonyReviewInput(
        review_id=f"review-{action.lower()}",
        validation_id=validation_result.validation_id,
        evaluation_id=validation_result.evaluations[0].evaluation_id,
        action=action,
        reviewer_id="tony",
        reason=f"Tony review action {action}",
        override_type=override_type,
        proposed_text="保持人工复核意见为独立 artifact。",
        evidence_refs=validation_result.evidence_refs[:1],
        review_timestamp=datetime(2026, 8, 1, 16, 0),
    )


def test_review_workflow_supports_four_tony_actions(validation_result) -> None:
    for action in ACTIONS:
        result = run_tony_review(validation_result, _review(action, validation_result))
        assert isinstance(result, TonyReviewResult)
        assert result.review_record.action == action
        assert result.status == "shadow"


def test_analyst_review_record_contract_is_frozen_and_traceable(validation_result) -> None:
    result = run_tony_review(validation_result, _review("APPROVE", validation_result))
    record = result.review_record
    assert dataclasses.is_dataclass(record)
    assert record.validation_id == validation_result.validation_id
    assert record.evaluation_id == validation_result.evaluations[0].evaluation_id
    assert record.evidence_refs
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.action = "REJECT"  # type: ignore[misc]


def test_modify_or_reject_generates_override_log(validation_result) -> None:
    for action in ("MODIFY", "REJECT"):
        result = run_tony_review(validation_result, _review(action, validation_result, override_type="STOCK_SELECTION_CORRECTION"))
        assert isinstance(result.override_log, OverrideLog)
        assert result.override_log.evaluation_id == validation_result.evaluations[0].evaluation_id
        assert result.override_log.override_type in OVERRIDE_TYPES
        assert result.override_log.review_timestamp.isoformat().startswith("2026-08-01T16:00")


def test_need_more_evidence_generates_research_request_proposal(validation_result) -> None:
    result = run_tony_review(validation_result, _review("NEED_MORE_EVIDENCE", validation_result, override_type="INSUFFICIENT_EVIDENCE"))
    assert isinstance(result.need_more_evidence_request, NeedMoreEvidenceRequest)
    assert result.need_more_evidence_request.status == "draft"
    assert result.need_more_evidence_request.evidence_refs


def test_financial_review_governance_gate_decides_review_artifacts(validation_result) -> None:
    allow = decide_review_governance(_review("APPROVE", validation_result), validation_result)
    more = decide_review_governance(_review("NEED_MORE_EVIDENCE", validation_result), validation_result)
    bad = decide_review_governance(TonyReviewInput(
        review_id="bad", validation_id="wrong", evaluation_id="wrong", action="INVALID", reviewer_id="tony",
        reason="bad", override_type="NO_OVERRIDE", proposed_text="bad", evidence_refs=(), review_timestamp=datetime(2026,8,1,16)
    ), validation_result)
    assert isinstance(allow, FinancialReviewGovernanceDecision)
    assert allow.decision == "allow"
    assert more.decision == "review_required"
    assert bad.decision == "reject"


def test_profile_updates_are_proposals_only(validation_result) -> None:
    result = run_tony_review(validation_result, _review("MODIFY", validation_result, override_type="RISK_CORRECTION"))
    assert isinstance(result.profile_update_proposal, InvestorProfileUpdateProposal)
    assert result.profile_update_proposal.status == "proposal"
    assert result.profile_update_proposal.proposal_type.endswith("Proposal")


def test_review_artifacts_have_evidence_refs(validation_result) -> None:
    result = run_tony_review(validation_result, _review("MODIFY", validation_result, override_type="TIMING_CORRECTION"))
    assert result.evidence_refs
    assert result.review_record.evidence_refs
    assert result.governance_decision.evidence_refs
    assert result.override_log and result.override_log.evidence_refs
    assert result.profile_update_proposal and result.profile_update_proposal.evidence_refs


def test_review_workflow_does_not_mutate_close_validation_result(validation_result) -> None:
    before = validation_result
    run_tony_review(validation_result, _review("REJECT", validation_result, override_type="RISK_CORRECTION"))
    assert validation_result == before
    with pytest.raises(dataclasses.FrozenInstanceError):
        validation_result.status = "mutated"  # type: ignore[misc]


def test_f3_does_not_emit_trade_decisions_or_orders(validation_result) -> None:
    result = run_tony_review(validation_result, _review("APPROVE", validation_result))
    serialized = repr(result).lower()
    assert not any(term in serialized for term in FORBIDDEN)


def test_f3_does_not_write_memory_or_knowledge_base() -> None:
    for path in [Path("runtime/capability/financial/workflows/tony_review.py"), Path("runtime/capability/financial/governance/review_policy.py")]:
        source = path.read_text().lower()
        assert not any(term in source for term in ("memory.write", "knowledge_base", "strategy.update", "profile.update", "trade("))


def test_review_workflow_is_replayable_from_same_inputs(validation_result) -> None:
    review = _review("MODIFY", validation_result, override_type="DIRECTION_CORRECTION")
    assert run_tony_review(validation_result, review) == run_tony_review(validation_result, review)


def test_f3_modules_do_not_import_database_memory_or_ai_theme_internals() -> None:
    for path in [Path("runtime/capability/financial/workflows/tony_review.py"), Path("runtime/capability/financial/governance/review_policy.py")]:
        tree = ast.parse(path.read_text())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        assert [x for x in imports if x.startswith(("ai_theme_app", "sqlalchemy", "psycopg", "sqlite3", "memory"))] == []
