"""Deterministic F3 review governance gate."""

from __future__ import annotations

import runtime.capability.financial.contracts as c

VALID_ACTIONS = {"APPROVE", "MODIFY", "REJECT", "NEED_MORE_EVIDENCE"}
VALID_OVERRIDE_TYPES = {
    "DIRECTION_CORRECTION",
    "TIMING_CORRECTION",
    "STOCK_SELECTION_CORRECTION",
    "RISK_CORRECTION",
    "INSUFFICIENT_EVIDENCE",
    "NO_OVERRIDE",
}


def decide_review_governance(
    review_input: c.TonyReviewInput,
    validation: c.CloseValidationResult,
) -> c.FinancialReviewGovernanceDecision:
    refs = review_input.evidence_refs or validation.evidence_refs
    if review_input.validation_id != validation.validation_id:
        decision = "reject"
        reason = "Review validation_id does not match close validation result."
    elif review_input.action not in VALID_ACTIONS:
        decision = "reject"
        reason = "Unsupported Tony review action."
    elif review_input.override_type not in VALID_OVERRIDE_TYPES:
        decision = "reject"
        reason = "Unsupported override type."
    elif not refs:
        decision = "reject"
        reason = "Review artifact lacks EvidenceRef."
    elif review_input.action == "NEED_MORE_EVIDENCE":
        decision = "review_required"
        reason = "Additional evidence request must stay draft until evidence pipeline approval."
    else:
        decision = "allow"
        reason = "Review artifact passes deterministic governance gate."
    return c.FinancialReviewGovernanceDecision(
        decision_id=f"review-governance-{review_input.review_id}",
        review_id=review_input.review_id,
        decision=decision,
        reason=reason,
        evidence_refs=refs,
    )
