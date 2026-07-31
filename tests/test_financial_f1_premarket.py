"""F1 Shadow Morning Analyst acceptance tests.

Traceability: docs/project_control/PHASE_CONTRACT_F1.md
"""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import pytest

from runtime.capability.financial.client.ai_theme_client import AIThemeFinancialClient
from runtime.capability.financial.contracts import (
    ConclusionWithEvidence,
    InvestmentCase,
    PremarketResearchReport,
)
from runtime.capability.financial.rendering.report_renderer import render_premarket_report
from runtime.capability.financial.workflows.premarket import run_premarket_research


FORBIDDEN_TRADE_TERMS = (
    "buy",
    "sell",
    "open_position",
    "close_position",
    "order",
    "execute",
    "今日推荐股票",
    "正式推荐",
    "交易建议",
)
ALLOWED_OBSERVATION_LEVELS = {"A", "B", "C", "FORBIDDEN"}


@pytest.fixture()
def report() -> PremarketResearchReport:
    bundle = AIThemeFinancialClient.fixture_client().get_market_brief(
        __import__("datetime").date(2026, 8, 1),
        context_type="premarket",
    )
    return run_premarket_research(bundle)


# F1-TC-01 / F1-AT-01
def test_premarket_workflow_generates_daily_research_briefing(report: PremarketResearchReport) -> None:
    assert isinstance(report, PremarketResearchReport)
    assert report.trade_date.isoformat() == "2026-08-01"
    assert report.as_of.isoformat().startswith("2026-08-01T08:00:00")
    assert report.schema_version
    assert report.status == "shadow"


# F1-TC-02 / F1-AT-02
def test_premarket_report_includes_market_state_with_evidence(report: PremarketResearchReport) -> None:
    assert isinstance(report.market_summary, ConclusionWithEvidence)
    assert report.market_summary.text
    assert report.market_summary.evidence_refs


# F1-TC-03 / F1-AT-03
def test_premarket_report_includes_top_themes_with_evidence(report: PremarketResearchReport) -> None:
    assert 1 <= len(report.top_themes) <= 5
    assert all(theme.theme_id and theme.name for theme in report.top_themes)
    assert all(theme.attention_level and theme.lifecycle_stage for theme in report.top_themes)
    assert all(theme.evidence_refs for theme in report.top_themes)


# F1-TC-04 / F1-AT-04
def test_premarket_report_includes_conditional_watchlist(report: PremarketResearchReport) -> None:
    assert report.conditional_watchlist
    assert all(item.stock_code and item.stock_name for item in report.conditional_watchlist)
    assert all(item.strategy_id and item.observation_level for item in report.conditional_watchlist)
    assert all(item.evidence_refs for item in report.conditional_watchlist)


# F1-TC-05 / F1-AT-05
def test_each_candidate_has_falsifiable_investment_case(report: PremarketResearchReport) -> None:
    assert len(report.investment_cases) == len(report.conditional_watchlist)
    for case in report.investment_cases:
        assert isinstance(case, InvestmentCase)
        assert case.status == "shadow"
        assert case.entry_conditions
        assert case.confirmation_conditions
        assert case.invalidation_conditions
        assert case.risk_flags
        assert case.supporting_evidence_refs
        assert case.case_type == "shadow_research"


# F1-TC-06 / F1-AT-06
def test_observation_levels_are_governed(report: PremarketResearchReport) -> None:
    assert {item.observation_level for item in report.conditional_watchlist} <= ALLOWED_OBSERVATION_LEVELS
    assert {case.max_attention_level for case in report.investment_cases} <= ALLOWED_OBSERVATION_LEVELS


# F1-TC-07 / F1-AT-07
def test_premarket_report_includes_risk_and_forbidden_items(report: PremarketResearchReport) -> None:
    assert report.risk_items
    assert all(isinstance(item, ConclusionWithEvidence) for item in report.risk_items)
    assert all(item.evidence_refs for item in report.risk_items)
    assert report.forbidden_items
    assert all(item.evidence_refs for item in report.forbidden_items)


# F1-TC-08 / F1-AT-08
def test_premarket_report_has_no_unsupported_claims(report: PremarketResearchReport) -> None:
    conclusion_nodes = [
        report.market_summary,
        report.main_conflict,
        *report.risk_items,
        *report.forbidden_items,
        *report.auction_confirmation_points,
    ]
    assert all(node.evidence_refs for node in conclusion_nodes)
    assert report.evidence_refs
    assert all(case.supporting_evidence_refs for case in report.investment_cases)


# F1-TC-09 / F1-AT-09
def test_f1_does_not_emit_trade_decisions_or_orders(report: PremarketResearchReport) -> None:
    serialized = repr(report).lower()
    assert not any(term in serialized for term in FORBIDDEN_TRADE_TERMS)


# F1-TC-10 / F1-AT-10
def test_f1_does_not_modify_strategy_or_world_model() -> None:
    paths = [
        Path("runtime/capability/financial/workflows/premarket.py"),
        Path("runtime/capability/financial/rendering/report_renderer.py"),
    ]
    forbidden = ("write_strategy", "update_strategy", "world_model", "risk_gate.update", "memory.write")
    for path in paths:
        source = path.read_text().lower()
        assert not any(term in source for term in forbidden)


# F1-TC-11 / F1-AT-11
def test_f1_outputs_shadow_draft_only(report: PremarketResearchReport) -> None:
    assert report.status in {"draft", "shadow"}
    assert all(case.status in {"draft", "shadow"} for case in report.investment_cases)


# F1-TC-12 / F1-AT-12
def test_premarket_report_is_replayable_from_same_snapshot() -> None:
    client = AIThemeFinancialClient.fixture_client()
    bundle = client.get_market_brief(__import__("datetime").date(2026, 8, 1), context_type="premarket")

    report_1 = run_premarket_research(bundle)
    report_2 = run_premarket_research(bundle)

    assert report_1 == report_2
    assert report_1.input_hash == report_2.input_hash
    assert dataclasses.is_dataclass(report_1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        report_1.status = "mutated"  # type: ignore[misc]


def test_renderer_outputs_julia_premarket_markdown_without_recommendation_language(report: PremarketResearchReport) -> None:
    markdown = render_premarket_report(report)

    assert "《Julia盘前研究》2026-08-01" in markdown
    assert "市场状态" in markdown
    assert "重点题材" in markdown
    assert "条件观察标的" in markdown
    assert "风险与禁止项" in markdown
    assert "集合竞价确认点" in markdown
    assert "EvidenceRef:" in markdown
    assert "今日推荐股票" not in markdown


def test_f1_modules_do_not_import_database_memory_or_ai_theme_internals() -> None:
    for path in [
        Path("runtime/capability/financial/workflows/premarket.py"),
        Path("runtime/capability/financial/rendering/report_renderer.py"),
    ]:
        tree = ast.parse(path.read_text())
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        forbidden_prefixes = ("ai_theme_app", "sqlalchemy", "psycopg", "sqlite3", "memory")
        assert [name for name in imports if name.startswith(forbidden_prefixes)] == []
