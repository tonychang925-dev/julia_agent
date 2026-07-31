"""Deterministic F1 premarket research workflow.

The workflow is intentionally deterministic: FinancialBriefingBundle in,
PremarketResearchReport out. It does not call online models, persistence layers,
strategy mutation code, or trading endpoints.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict

import runtime.capability.financial.contracts as c

CONTRACT_VERSION = "0.1"
_ALLOWED_LEVELS = {"A", "B", "C", "FORBIDDEN"}


def run_premarket_research(
    bundle: c.FinancialBriefingBundle,
    *,
    generated_by: str = "julia_financial_shadow",
    model_version: str = "deterministic_f1",
) -> c.PremarketResearchReport:
    """Build a shadow/draft premarket research report from a frozen bundle."""

    input_hash = _stable_input_hash(bundle)
    market_summary = c.ConclusionWithEvidence(
        conclusion_id=f"market-summary-{bundle.trade_date.isoformat()}",
        text=(
            f"市场处于{bundle.market_state.market_phase}阶段，"
            f"风险偏好为{bundle.market_state.risk_appetite}，"
            f"成交状态为{bundle.market_state.turnover_state}。"
        ),
        evidence_refs=bundle.market_state.evidence_refs,
        confidence="medium",
    )
    main_conflict = c.ConclusionWithEvidence(
        conclusion_id=f"main-conflict-{bundle.trade_date.isoformat()}",
        text="今日主要任务是验证高关注题材是否能获得竞价与成交确认。",
        evidence_refs=bundle.attention.evidence_refs + bundle.risk_state.evidence_refs,
        confidence="medium",
    )
    watchlist = tuple(
        _normalize_candidate_level(candidate) for candidate in bundle.candidates
    )
    cases = tuple(_build_shadow_case(candidate, bundle) for candidate in watchlist)
    risk_items = tuple(
        c.ConclusionWithEvidence(
            conclusion_id=f"risk-{idx + 1}-{bundle.trade_date.isoformat()}",
            text=f"风险观察：{flag}。",
            evidence_refs=bundle.risk_state.evidence_refs,
            confidence="high",
        )
        for idx, flag in enumerate(bundle.risk_state.risk_flags)
    )
    forbidden_items = (
        c.ConclusionWithEvidence(
            conclusion_id=f"forbidden-late-stage-{bundle.trade_date.isoformat()}",
            text="禁止追逐高位加速且证据质量不足的标的，只保留风险隔离观察。",
            evidence_refs=bundle.risk_state.evidence_refs,
            confidence="high",
        ),
    )
    auction_points = tuple(
        c.ConclusionWithEvidence(
            conclusion_id=f"auction-{idx + 1}-{bundle.trade_date.isoformat()}",
            text=f"集合竞价确认点：验证 {theme.name} 是否维持 {theme.attention_level} 关注强度。",
            evidence_refs=theme.evidence_refs,
            confidence="medium",
        )
        for idx, theme in enumerate(bundle.top_themes[:3])
    )
    return c.PremarketResearchReport(
        report_id=f"premarket-{bundle.trade_date.isoformat()}-{input_hash[:12]}",
        trade_date=bundle.trade_date,
        as_of=bundle.as_of,
        market_summary=market_summary,
        main_conflict=main_conflict,
        top_themes=bundle.top_themes[:5],
        conditional_watchlist=watchlist,
        investment_cases=cases,
        risk_items=risk_items,
        forbidden_items=forbidden_items,
        auction_confirmation_points=auction_points,
        evidence_refs=bundle.evidence_refs,
        source_bundle_id=bundle.bundle_id,
        source_snapshot_ids=bundle.source_snapshot_ids,
        input_hash=input_hash,
        generated_by=generated_by,
        model_version=model_version,
        status="shadow",
    )


def _normalize_candidate_level(candidate: c.CandidateView) -> c.CandidateView:
    if candidate.observation_level in _ALLOWED_LEVELS:
        return candidate
    return c.CandidateView(
        stock_code=candidate.stock_code,
        stock_name=candidate.stock_name,
        strategy_id=candidate.strategy_id,
        opportunity_type=candidate.opportunity_type,
        observation_level="C",
        thesis=candidate.thesis,
        evidence_refs=candidate.evidence_refs,
        schema_version=candidate.schema_version,
    )


def _build_shadow_case(candidate: c.CandidateView, bundle: c.FinancialBriefingBundle) -> c.InvestmentCase:
    evidence_refs = candidate.evidence_refs or bundle.evidence_refs
    return c.InvestmentCase(
        case_id=f"case-{bundle.trade_date.isoformat()}-{candidate.stock_code}",
        trade_date=bundle.trade_date,
        stock_code=candidate.stock_code,
        stock_name=candidate.stock_name,
        strategy_id=candidate.strategy_id,
        opportunity_type=candidate.opportunity_type,
        time_horizon="intraday_or_2_to_5_days",
        thesis=f"{candidate.stock_name}仅作为条件观察标的：{candidate.thesis}",
        causal_chain=(
            "market_state -> attention_radar",
            "theme_evidence -> candidate_watchlist",
            "risk_state -> shadow_research_case",
        ),
        supporting_evidence_refs=evidence_refs,
        counter_evidence_refs=bundle.risk_state.evidence_refs,
        entry_conditions=("observe: 竞价强度与题材主线同步验证",),
        confirmation_conditions=("confirm: 题材成交维持且风险状态不升级",),
        invalidation_conditions=("invalidate: 题材转弱或 M7 风险标记升级",),
        exit_conditions=("monitor: shadow 阶段不生成退出动作，仅记录失效条件",),
        expected_scenarios=(
            c.Scenario(
                scenario_id=f"scenario-{candidate.stock_code}-validate",
                description="条件被验证后维持观察级别，不产生正式交易动作。",
                probability=0.5,
                expected_observations=("validate: attention and risk evidence remain aligned",),
                falsifiers=("invalidate: risk evidence conflicts with candidate thesis",),
            ),
        ),
        prediction_probability=0.5,
        source_quality_score=0.7,
        risk_flags=bundle.risk_state.risk_flags,
        max_attention_level=candidate.observation_level,
        generated_by="julia_financial_shadow",
        model_version="deterministic_f1",
        policy_versions={"contract": CONTRACT_VERSION, "mode": "shadow"},
        status="shadow",
        case_type="shadow_research",
        schema_version="financial.f1.v1",
    )


def _stable_input_hash(bundle: c.FinancialBriefingBundle) -> str:
    payload = asdict(bundle)
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()
