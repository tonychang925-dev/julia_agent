"""Frozen F0 financial analyst contract types."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Mapping, Tuple


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    ref_id: str
    object_type: str
    object_id: str
    trade_date: date
    source_snapshot_id: str
    schema_version: str = "financial.f0.v1"


@dataclass(frozen=True, slots=True)
class EvidenceBundle:
    ref: EvidenceRef
    title: str
    summary: str
    source_type: str
    source_snapshot_id: str
    observed_at: datetime
    producer_version: str
    schema_version: str = "financial.f0.v1"


@dataclass(frozen=True, slots=True)
class MarketStateView:
    trade_date: date
    market_phase: str
    risk_appetite: str
    turnover_state: str
    evidence_refs: Tuple[EvidenceRef, ...]
    schema_version: str = "financial.f0.v1"


@dataclass(frozen=True, slots=True)
class RiskStateView:
    trade_date: date
    risk_level: str
    risk_flags: Tuple[str, ...]
    gate_name: str
    evidence_refs: Tuple[EvidenceRef, ...]
    schema_version: str = "financial.f0.v1"


@dataclass(frozen=True, slots=True)
class ThemeView:
    theme_id: str
    name: str
    attention_level: str
    lifecycle_stage: str
    evidence_refs: Tuple[EvidenceRef, ...]
    schema_version: str = "financial.f0.v1"


@dataclass(frozen=True, slots=True)
class AttentionView:
    trade_date: date
    attention_level: str
    top_theme_ids: Tuple[str, ...]
    evidence_refs: Tuple[EvidenceRef, ...]
    schema_version: str = "financial.f0.v1"


@dataclass(frozen=True, slots=True)
class CandidateView:
    stock_code: str
    stock_name: str
    strategy_id: str
    opportunity_type: str
    observation_level: str
    thesis: str
    evidence_refs: Tuple[EvidenceRef, ...]
    schema_version: str = "financial.f0.v1"


@dataclass(frozen=True, slots=True)
class EventView:
    event_id: str
    title: str
    event_type: str
    impact_level: str
    evidence_refs: Tuple[EvidenceRef, ...]
    schema_version: str = "financial.f0.v1"


@dataclass(frozen=True, slots=True)
class HypothesisView:
    hypothesis_id: str
    trade_date: date
    statement: str
    status: str
    evidence_refs: Tuple[EvidenceRef, ...]
    schema_version: str = "financial.f0.v1"


@dataclass(frozen=True, slots=True)
class MarketThesisView:
    trade_date: date
    thesis: str
    evidence_refs: Tuple[EvidenceRef, ...]
    schema_version: str = "financial.f0.v1"


@dataclass(frozen=True, slots=True)
class StockAnalysisView:
    stock_code: str
    stock_name: str
    trade_date: date
    summary: str
    evidence_refs: Tuple[EvidenceRef, ...]
    schema_version: str = "financial.f0.v1"


@dataclass(frozen=True, slots=True)
class ThemeAnalysisView:
    theme_id: str
    trade_date: date
    summary: str
    evidence_refs: Tuple[EvidenceRef, ...]
    schema_version: str = "financial.f0.v1"


@dataclass(frozen=True, slots=True)
class Scenario:
    scenario_id: str
    description: str
    probability: float
    expected_observations: Tuple[str, ...]
    falsifiers: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class InvestmentCase:
    case_id: str
    trade_date: date
    stock_code: str
    stock_name: str
    strategy_id: str
    opportunity_type: str
    time_horizon: str
    thesis: str
    causal_chain: Tuple[str, ...]
    supporting_evidence_refs: Tuple[EvidenceRef, ...]
    counter_evidence_refs: Tuple[EvidenceRef, ...]
    entry_conditions: Tuple[str, ...]
    confirmation_conditions: Tuple[str, ...]
    invalidation_conditions: Tuple[str, ...]
    exit_conditions: Tuple[str, ...]
    expected_scenarios: Tuple[Scenario, ...]
    prediction_probability: float
    source_quality_score: float
    risk_flags: Tuple[str, ...]
    max_attention_level: str
    generated_by: str
    model_version: str
    policy_versions: Mapping[str, str]
    status: str
    case_type: str = "shadow_research"
    schema_version: str = "financial.f0.v1"


@dataclass(frozen=True, slots=True)
class FinancialBriefingBundle:
    bundle_id: str
    trade_date: date
    as_of: datetime
    context_type: str
    market_state: MarketStateView
    attention: AttentionView
    top_themes: Tuple[ThemeView, ...]
    candidates: Tuple[CandidateView, ...]
    news_drivers: Tuple[EventView, ...]
    risk_state: RiskStateView
    active_hypotheses: Tuple[HypothesisView, ...]
    source_snapshot_ids: Tuple[str, ...]
    producer_versions: Mapping[str, str]
    module_coverage: Mapping[str, str]
    evidence_refs: Tuple[EvidenceRef, ...]
    schema_version: str = "financial.f0.v1"


@dataclass(frozen=True, slots=True)
class ConclusionWithEvidence:
    conclusion_id: str
    text: str
    evidence_refs: Tuple[EvidenceRef, ...]
    confidence: str = "medium"
    schema_version: str = "financial.f1.v1"


@dataclass(frozen=True, slots=True)
class PremarketResearchReport:
    report_id: str
    trade_date: date
    as_of: datetime
    market_summary: ConclusionWithEvidence
    main_conflict: ConclusionWithEvidence
    top_themes: Tuple[ThemeView, ...]
    conditional_watchlist: Tuple[CandidateView, ...]
    investment_cases: Tuple[InvestmentCase, ...]
    risk_items: Tuple[ConclusionWithEvidence, ...]
    forbidden_items: Tuple[ConclusionWithEvidence, ...]
    auction_confirmation_points: Tuple[ConclusionWithEvidence, ...]
    evidence_refs: Tuple[EvidenceRef, ...]
    source_bundle_id: str
    source_snapshot_ids: Tuple[str, ...]
    input_hash: str
    generated_by: str
    model_version: str
    status: str
    schema_version: str = "financial.f1.v1"


@dataclass(frozen=True, slots=True)
class CandidateTruth:
    stock_code: str
    stock_name: str
    entry_condition_triggered: bool
    confirmation_condition_triggered: bool
    invalidation_condition_triggered: bool
    risk_invalidated: bool
    outcome: str
    return_pct: float
    evidence_refs: Tuple[EvidenceRef, ...]
    schema_version: str = "financial.f2.v1"


@dataclass(frozen=True, slots=True)
class MarketTruthSnapshot:
    truth_snapshot_id: str
    trade_date: date
    as_of: datetime
    market_close_state: str
    risk_level: str
    candidate_truths: Tuple[CandidateTruth, ...]
    source_snapshot_ids: Tuple[str, ...]
    evidence_refs: Tuple[EvidenceRef, ...]
    producer_version: str
    schema_version: str = "financial.f2.v1"


@dataclass(frozen=True, slots=True)
class ErrorAttribution:
    attribution_id: str
    category: str
    dimensions: Tuple[str, ...]
    explanation: str
    evidence_refs: Tuple[EvidenceRef, ...]
    schema_version: str = "financial.f2.v1"


@dataclass(frozen=True, slots=True)
class InvestmentCaseEvaluation:
    evaluation_id: str
    case_id: str
    stock_code: str
    status: str
    thesis_validated: bool
    trigger_validated: bool
    risk_validated: bool
    explanation: str
    evidence_refs: Tuple[EvidenceRef, ...]
    error_attribution: ErrorAttribution | None
    schema_version: str = "financial.f2.v1"


@dataclass(frozen=True, slots=True)
class CloseValidationSummary:
    thesis_accuracy: float
    trigger_accuracy: float
    risk_accuracy: float
    evaluation_count: int
    evidence_refs: Tuple[EvidenceRef, ...]
    schema_version: str = "financial.f2.v1"


@dataclass(frozen=True, slots=True)
class CloseValidationResult:
    validation_id: str
    premarket_report_id: str
    premarket_input_hash: str
    source_bundle_id: str
    source_snapshot_ids: Tuple[str, ...]
    truth_snapshot_id: str
    evaluations: Tuple[InvestmentCaseEvaluation, ...]
    summary: CloseValidationSummary
    evidence_refs: Tuple[EvidenceRef, ...]
    generated_by: str
    model_version: str
    evaluator_version: str
    status: str
    schema_version: str = "financial.f2.v1"


@dataclass(frozen=True, slots=True)
class TonyReviewInput:
    review_id: str
    validation_id: str
    evaluation_id: str
    action: str
    reviewer_id: str
    reason: str
    override_type: str
    proposed_text: str
    evidence_refs: Tuple[EvidenceRef, ...]
    review_timestamp: datetime
    schema_version: str = "financial.f3.v1"


@dataclass(frozen=True, slots=True)
class AnalystReviewRecord:
    review_id: str
    validation_id: str
    evaluation_id: str
    action: str
    reviewer_id: str
    reason: str
    evidence_refs: Tuple[EvidenceRef, ...]
    review_timestamp: datetime
    schema_version: str = "financial.f3.v1"


@dataclass(frozen=True, slots=True)
class OverrideLog:
    override_id: str
    evaluation_id: str
    reviewer_id: str
    override_type: str
    original_status: str
    override_text: str
    reason: str
    evidence_refs: Tuple[EvidenceRef, ...]
    review_timestamp: datetime
    schema_version: str = "financial.f3.v1"


@dataclass(frozen=True, slots=True)
class NeedMoreEvidenceRequest:
    request_id: str
    validation_id: str
    evaluation_id: str
    question: str
    reason: str
    evidence_refs: Tuple[EvidenceRef, ...]
    status: str
    schema_version: str = "financial.f3.v1"


@dataclass(frozen=True, slots=True)
class InvestorProfileUpdateProposal:
    proposal_id: str
    validation_id: str
    evaluation_id: str
    proposal_type: str
    proposed_change: str
    reason: str
    evidence_refs: Tuple[EvidenceRef, ...]
    status: str
    schema_version: str = "financial.f3.v1"


@dataclass(frozen=True, slots=True)
class FinancialReviewGovernanceDecision:
    decision_id: str
    review_id: str
    decision: str
    reason: str
    evidence_refs: Tuple[EvidenceRef, ...]
    schema_version: str = "financial.f3.v1"


@dataclass(frozen=True, slots=True)
class TonyReviewResult:
    result_id: str
    validation_id: str
    review_record: AnalystReviewRecord
    governance_decision: FinancialReviewGovernanceDecision
    override_log: OverrideLog | None
    need_more_evidence_request: NeedMoreEvidenceRequest | None
    profile_update_proposal: InvestorProfileUpdateProposal | None
    evidence_refs: Tuple[EvidenceRef, ...]
    generated_by: str
    model_version: str
    status: str
    schema_version: str = "financial.f3.v1"


__all__ = [
    "AnalystReviewRecord",
    "AttentionView",
    "CandidateView",
    "CandidateTruth",
    "CloseValidationResult",
    "CloseValidationSummary",
    "ConclusionWithEvidence",
    "EvidenceBundle",
    "ErrorAttribution",
    "EvidenceRef",
    "EventView",
    "FinancialBriefingBundle",
    "FinancialReviewGovernanceDecision",
    "HypothesisView",
    "InvestorProfileUpdateProposal",
    "InvestmentCase",
    "InvestmentCaseEvaluation",
    "MarketStateView",
    "MarketTruthSnapshot",
    "NeedMoreEvidenceRequest",
    "OverrideLog",
    "MarketThesisView",
    "PremarketResearchReport",
    "RiskStateView",
    "Scenario",
    "StockAnalysisView",
    "ThemeAnalysisView",
    "ThemeView",
    "TonyReviewInput",
    "TonyReviewResult",
]
