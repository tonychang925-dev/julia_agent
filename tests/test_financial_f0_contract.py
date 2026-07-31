"""F0 Financial Analyst Contract acceptance tests.

Traceability: docs/project_control/PHASE_CONTRACT_F0.md
"""

from __future__ import annotations

import ast
import dataclasses
from datetime import date
from pathlib import Path

import pytest

from runtime.capability.financial.client.ai_theme_client import AIThemeFinancialClient
from runtime.capability.financial.contracts import (
    CandidateView,
    EvidenceBundle,
    EvidenceRef,
    FinancialBriefingBundle,
    RiskStateView,
    ThemeView,
)


TRADE_DATE = date(2026, 8, 1)


@pytest.fixture()
def client() -> AIThemeFinancialClient:
    return AIThemeFinancialClient.fixture_client()


# F0-TC-01 / F0-AT-01
def test_market_brief_contract_reads_daily_market_state(client: AIThemeFinancialClient) -> None:
    brief = client.get_market_brief(TRADE_DATE, context_type="premarket")

    assert isinstance(brief, FinancialBriefingBundle)
    assert brief.trade_date == TRADE_DATE
    assert brief.market_state.trade_date == TRADE_DATE
    assert brief.schema_version


# F0-TC-02 / F0-AT-02
def test_attention_top_themes_have_evidence_refs(client: AIThemeFinancialClient) -> None:
    themes = client.get_top_themes(TRADE_DATE, limit=5)

    assert themes
    assert all(isinstance(theme, ThemeView) for theme in themes)
    assert all(theme.theme_id and theme.name and theme.attention_level for theme in themes)
    assert all(theme.evidence_refs for theme in themes)


# F0-TC-03 / F0-AT-03
def test_w2s_candidates_have_strategy_and_evidence(client: AIThemeFinancialClient) -> None:
    candidates = client.get_w2s_candidates(TRADE_DATE)

    assert candidates
    assert all(isinstance(candidate, CandidateView) for candidate in candidates)
    assert all(candidate.stock_code and candidate.stock_name for candidate in candidates)
    assert all(candidate.strategy_id for candidate in candidates)
    assert all(candidate.evidence_refs for candidate in candidates)


# F0-TC-04 / F0-AT-04
def test_event_evidence_bundle_is_traceable(client: AIThemeFinancialClient) -> None:
    brief = client.get_market_brief(TRADE_DATE, context_type="premarket")
    ref = brief.news_drivers[0].evidence_refs[0]
    evidence = client.get_evidence(ref.ref_id)

    assert isinstance(evidence, EvidenceBundle)
    assert evidence.ref.ref_id == ref.ref_id
    assert evidence.source_type
    assert evidence.source_snapshot_id in brief.source_snapshot_ids


# F0-TC-05 / F0-AT-05
def test_risk_state_view_exposes_m7_risk(client: AIThemeFinancialClient) -> None:
    risk_state = client.get_risk_state(TRADE_DATE)

    assert isinstance(risk_state, RiskStateView)
    assert risk_state.risk_level in {"LOW", "MODERATE", "HIGH", "CRITICAL"}
    assert risk_state.risk_flags
    assert risk_state.evidence_refs


# F0-TC-06 / F0-AT-06
def test_all_conclusions_require_evidence_ref(client: AIThemeFinancialClient) -> None:
    brief = client.get_market_brief(TRADE_DATE, context_type="premarket")

    assert brief.evidence_refs
    assert brief.market_state.evidence_refs
    assert brief.attention.evidence_refs
    assert brief.risk_state.evidence_refs
    assert all(theme.evidence_refs for theme in brief.top_themes)
    assert all(candidate.evidence_refs for candidate in brief.candidates)
    assert all(event.evidence_refs for event in brief.news_drivers)


# F0-TC-07 / F0-AT-07
def test_financial_client_has_no_database_access() -> None:
    source = Path("runtime/capability/financial/client/ai_theme_client.py").read_text()
    forbidden = ("sqlite", "postgres", "psycopg", "sqlalchemy", "create_engine", "select *", " from ")

    lowered = source.lower()
    assert not any(token in lowered for token in forbidden)


# F0-TC-08 / F0-AT-08
def test_financial_client_import_boundary() -> None:
    source_path = Path("runtime/capability/financial/client/ai_theme_client.py")
    tree = ast.parse(source_path.read_text())
    forbidden_imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            forbidden_imports.extend(alias.name for alias in node.names if alias.name.startswith("ai_theme_app"))
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("ai_theme_app"):
            forbidden_imports.append(node.module)

    assert forbidden_imports == []


# F0-TC-09 / F0-AT-09
def test_f0_outputs_no_formal_trade_decision(client: AIThemeFinancialClient) -> None:
    brief = client.get_market_brief(TRADE_DATE, context_type="premarket")
    serialized = repr(brief).lower()
    forbidden = ("order_id", "buy_order", "sell_order", "正式推荐", "交易建议")

    assert not any(token in serialized for token in forbidden)
    assert all(candidate.observation_level in {"A", "B", "C", "FORBIDDEN"} for candidate in brief.candidates)


# F0-TC-10 / F0-AT-10
def test_market_brief_is_frozen_and_replayable(client: AIThemeFinancialClient) -> None:
    brief_1 = client.get_market_brief(TRADE_DATE, context_type="premarket")
    brief_2 = client.get_market_brief(TRADE_DATE, context_type="premarket")

    assert brief_1 == brief_2
    assert dataclasses.is_dataclass(brief_1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        brief_1.schema_version = "mutated"  # type: ignore[misc]
    assert brief_1.source_snapshot_ids
    assert brief_1.producer_versions


# F0-TC-11 / F0-AT-11
def test_provider_switch_keeps_contract_shape(client: AIThemeFinancialClient) -> None:
    deterministic = AIThemeFinancialClient.fixture_client(provider_name="deterministic")

    brief_1 = client.get_market_brief(TRADE_DATE, context_type="premarket")
    brief_2 = deterministic.get_market_brief(TRADE_DATE, context_type="premarket")

    assert type(brief_1) is type(brief_2)
    assert tuple(field.name for field in dataclasses.fields(brief_1)) == tuple(
        field.name for field in dataclasses.fields(brief_2)
    )
    assert all(isinstance(ref, EvidenceRef) for ref in brief_2.evidence_refs)
