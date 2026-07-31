"""Deterministic F2 close validation workflow.

Consumes frozen F1 reports and external truth snapshots. Produces a shadow
validation artifact only; it does not mutate reports, update learning stores,
change strategies, or call trading systems.
"""

from __future__ import annotations

import runtime.capability.financial.contracts as c

VALID_STATUSES = {
    "CONFIRMED",
    "PARTIALLY_CONFIRMED",
    "FALSIFIED",
    "NOT_TRIGGERED",
    "EXPIRED",
    "INVALIDATED_BY_RISK",
    "INSUFFICIENT_DATA",
}
EVALUATOR_VERSION = "deterministic_f2_v1"


def run_close_validation(
    report: c.PremarketResearchReport,
    truth: c.MarketTruthSnapshot,
    *,
    generated_by: str = "julia_financial_shadow",
    model_version: str = "deterministic_f2",
) -> c.CloseValidationResult:
    """Validate F1 shadow cases against an external market truth snapshot."""

    truth_by_stock = {item.stock_code: item for item in truth.candidate_truths}
    evaluations = tuple(
        _evaluate_case(case, truth_by_stock.get(case.stock_code), truth)
        for case in report.investment_cases
    )
    summary = _build_summary(evaluations, truth.evidence_refs)
    return c.CloseValidationResult(
        validation_id=f"close-validation-{report.trade_date.isoformat()}-{truth.truth_snapshot_id}",
        premarket_report_id=report.report_id,
        premarket_input_hash=report.input_hash,
        source_bundle_id=report.source_bundle_id,
        source_snapshot_ids=report.source_snapshot_ids,
        truth_snapshot_id=truth.truth_snapshot_id,
        evaluations=evaluations,
        summary=summary,
        evidence_refs=truth.evidence_refs + report.evidence_refs,
        generated_by=generated_by,
        model_version=model_version,
        evaluator_version=EVALUATOR_VERSION,
        status="shadow",
    )


def _evaluate_case(
    case: c.InvestmentCase,
    truth: c.CandidateTruth | None,
    snapshot: c.MarketTruthSnapshot,
) -> c.InvestmentCaseEvaluation:
    if truth is None:
        status = "INSUFFICIENT_DATA"
        explanation = "Truth snapshot does not contain this candidate."
        evidence_refs = snapshot.evidence_refs
    elif truth.risk_invalidated:
        status = "INVALIDATED_BY_RISK"
        explanation = "Risk truth invalidated the shadow case."
        evidence_refs = truth.evidence_refs
    elif not truth.entry_condition_triggered:
        status = "NOT_TRIGGERED"
        explanation = "Entry condition was not observed, so the case remains untriggered even if price moved."
        evidence_refs = truth.evidence_refs
    elif truth.invalidation_condition_triggered or truth.return_pct < 0:
        status = "FALSIFIED"
        explanation = "Entry/confirmation appeared but the case was invalidated or outcome was adverse."
        evidence_refs = truth.evidence_refs
    elif truth.confirmation_condition_triggered and truth.return_pct > 0:
        status = "CONFIRMED"
        explanation = "Entry and confirmation appeared with favorable outcome."
        evidence_refs = truth.evidence_refs
    else:
        status = "PARTIALLY_CONFIRMED"
        explanation = "Some but not all validation conditions were observed."
        evidence_refs = truth.evidence_refs

    attribution = None if status == "CONFIRMED" else _build_error_attribution(case, status, explanation, evidence_refs)
    trigger_validated = status in {"CONFIRMED", "PARTIALLY_CONFIRMED", "FALSIFIED"}
    thesis_validated = status in {"CONFIRMED", "PARTIALLY_CONFIRMED"}
    risk_validated = status != "INVALIDATED_BY_RISK"
    return c.InvestmentCaseEvaluation(
        evaluation_id=f"evaluation-{case.case_id}",
        case_id=case.case_id,
        stock_code=case.stock_code,
        status=status,
        thesis_validated=thesis_validated,
        trigger_validated=trigger_validated,
        risk_validated=risk_validated,
        explanation=explanation,
        evidence_refs=evidence_refs,
        error_attribution=attribution,
    )


def _build_error_attribution(
    case: c.InvestmentCase,
    status: str,
    explanation: str,
    evidence_refs: tuple[c.EvidenceRef, ...],
) -> c.ErrorAttribution:
    if status == "NOT_TRIGGERED":
        category = "trigger_not_observed"
        dimensions = ("entry_condition", "timing")
    elif status == "FALSIFIED":
        category = "thesis_falsified"
        dimensions = ("entry_condition", "risk_assessment", "outcome")
    elif status == "INVALIDATED_BY_RISK":
        category = "risk_invalidation"
        dimensions = ("risk_assessment",)
    else:
        category = "insufficient_or_partial_feedback"
        dimensions = ("theme_direction", "stock_selection", "evidence_quality")
    return c.ErrorAttribution(
        attribution_id=f"attribution-{case.case_id}-{status.lower()}",
        category=category,
        dimensions=dimensions,
        explanation=explanation,
        evidence_refs=evidence_refs,
    )


def _build_summary(
    evaluations: tuple[c.InvestmentCaseEvaluation, ...],
    evidence_refs: tuple[c.EvidenceRef, ...],
) -> c.CloseValidationSummary:
    count = len(evaluations)
    if count == 0:
        return c.CloseValidationSummary(
            thesis_accuracy=0.0,
            trigger_accuracy=0.0,
            risk_accuracy=0.0,
            evaluation_count=0,
            evidence_refs=evidence_refs,
        )
    return c.CloseValidationSummary(
        thesis_accuracy=sum(1 for item in evaluations if item.thesis_validated) / count,
        trigger_accuracy=sum(1 for item in evaluations if item.trigger_validated) / count,
        risk_accuracy=sum(1 for item in evaluations if item.risk_validated) / count,
        evaluation_count=count,
        evidence_refs=evidence_refs,
    )
