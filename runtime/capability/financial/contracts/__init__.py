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


__all__ = [
    "AttentionView",
    "CandidateView",
    "EvidenceBundle",
    "EvidenceRef",
    "EventView",
    "FinancialBriefingBundle",
    "HypothesisView",
    "InvestmentCase",
    "MarketStateView",
    "MarketThesisView",
    "RiskStateView",
    "Scenario",
    "StockAnalysisView",
    "ThemeAnalysisView",
    "ThemeView",
]
