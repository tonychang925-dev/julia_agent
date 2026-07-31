from __future__ import annotations

from enum import Enum


class TerminationReason(str, Enum):
    NONE = "none"
    NO_ACTION = "no_action"
    GOAL_SATISFIED = "goal_satisfied"
    ASK_USER = "user_confirmation_required"
    GOVERNANCE_REJECT = "governance_reject"
    INVARIANT_VIOLATION = "invariant_violation"
    STEP_LIMIT = "step_limit_reached"
    FAILURE_LIMIT = "failure_limit_reached"
    DUPLICATE_INTENT = "duplicate_intent_guard"
    RISK_LIMIT = "risk_limit_reached"
    CONTEXT_QUALITY = "context_quality_below_threshold"
    CAPABILITY_FAILURE = "capability_failure"
