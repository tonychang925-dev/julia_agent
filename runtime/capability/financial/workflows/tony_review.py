"""Deterministic F3 Tony review workflow.

Produces independent shadow review artifacts. It does not mutate F2 validation,
write learning stores, update profiles, change strategies, or call trading systems.
"""

from __future__ import annotations

import runtime.capability.financial.contracts as c
from runtime.capability.financial.governance.review_policy import decide_review_governance


def run_tony_review(
    validation: c.CloseValidationResult,
    review_input: c.TonyReviewInput,
    *,
    reviewer_id: str = "tony",
    generated_by: str = "julia_financial_shadow",
    model_version: str = "deterministic_f3",
) -> c.TonyReviewResult:
    decision = decide_review_governance(review_input, validation)
    refs = review_input.evidence_refs or validation.evidence_refs
    record = c.AnalystReviewRecord(
        review_id=review_input.review_id,
        validation_id=review_input.validation_id,
        evaluation_id=review_input.evaluation_id,
        action=review_input.action,
        reviewer_id=reviewer_id or review_input.reviewer_id,
        reason=review_input.reason,
        evidence_refs=refs,
        review_timestamp=review_input.review_timestamp,
    )
    evaluation = _find_evaluation(validation, review_input.evaluation_id)
    override_log = None
    evidence_request = None
    proposal = None
    if decision.decision != "reject" and review_input.action in {"MODIFY", "REJECT"}:
        override_log = c.OverrideLog(
            override_id=f"override-{review_input.review_id}",
            evaluation_id=review_input.evaluation_id,
            reviewer_id=record.reviewer_id,
            override_type=review_input.override_type,
            original_status=evaluation.status if evaluation else "UNKNOWN",
            override_text=review_input.proposed_text,
            reason=review_input.reason,
            evidence_refs=refs,
            review_timestamp=review_input.review_timestamp,
        )
        proposal = c.InvestorProfileUpdateProposal(
            proposal_id=f"profile-proposal-{review_input.review_id}",
            validation_id=validation.validation_id,
            evaluation_id=review_input.evaluation_id,
            proposal_type="InvestorProfileUpdateProposal",
            proposed_change=f"Review future analyst preference for {review_input.override_type}.",
            reason=review_input.reason,
            evidence_refs=refs,
            status="proposal",
        )
    if decision.decision != "reject" and review_input.action == "NEED_MORE_EVIDENCE":
        evidence_request = c.NeedMoreEvidenceRequest(
            request_id=f"need-evidence-{review_input.review_id}",
            validation_id=validation.validation_id,
            evaluation_id=review_input.evaluation_id,
            question=review_input.proposed_text,
            reason=review_input.reason,
            evidence_refs=refs,
            status="draft",
        )
    return c.TonyReviewResult(
        result_id=f"tony-review-result-{review_input.review_id}",
        validation_id=validation.validation_id,
        review_record=record,
        governance_decision=decision,
        override_log=override_log,
        need_more_evidence_request=evidence_request,
        profile_update_proposal=proposal,
        evidence_refs=refs,
        generated_by=generated_by,
        model_version=model_version,
        status="shadow",
    )


def _find_evaluation(
    validation: c.CloseValidationResult,
    evaluation_id: str,
) -> c.InvestmentCaseEvaluation | None:
    for evaluation in validation.evaluations:
        if evaluation.evaluation_id == evaluation_id:
            return evaluation
    return None
