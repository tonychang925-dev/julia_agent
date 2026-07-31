from __future__ import annotations

import ast
import dataclasses
from datetime import date
from pathlib import Path

from runtime.capability.financial.client.ai_theme_client import AIThemeFinancialClient
from runtime.capability.financial.interface.analyst_chat.context import build_context
from runtime.capability.financial.interface.analyst_chat.session import (
    AnalystSession,
    detect_intent,
)
from runtime.capability.financial.interface.analyst_chat.voice import VOICE_STATUS, voice_placeholder


FORBIDDEN_RESPONSE_TERMS = ("buy", "sell", "order", "execute", "正式推荐", "交易建议")


def test_session_lifecycle_text_message_response_close() -> None:
    session = AnalystSession(trade_date=date(2026, 8, 1), client=AIThemeFinancialClient.fixture_client())
    assert session.closed is False

    response = session.handle_text("今天怎么看AI？")
    assert response.session_id == session.session_id
    assert response.status == "shadow"
    assert response.text
    assert dataclasses.is_dataclass(response)

    session.close()
    assert session.closed is True


def test_intent_detection_is_deterministic_and_priority_ordered() -> None:
    text = "为什么今天 AI 是主线？"
    assert detect_intent(text) == detect_intent(text) == "deep_dive"
    assert detect_intent("今天怎么看AI") == "morning_brief"
    assert detect_intent("帮我研究一下PCB?") == "research"
    assert detect_intent("随便聊聊") == "unknown"


def test_context_isolation_by_intent() -> None:
    client = AIThemeFinancialClient.fixture_client()
    session = AnalystSession(trade_date=date(2026, 8, 1), client=client)

    morning = build_context(session, "morning_brief", "今天怎么看")
    deep = build_context(session, "deep_dive", "为什么关注华工科技")
    unknown = build_context(session, "unknown", "随便聊聊")

    assert morning.context_scope == ("market_state", "top_themes", "risk_state")
    assert morning.target_evidence == ()
    assert deep.context_scope == ("target_candidate", "theme_evidence", "risk_evidence")
    assert deep.target_evidence
    assert unknown.context_scope == ()
    assert unknown.evidence_refs == ()


def test_financial_response_requires_evidence_unless_unknown() -> None:
    session = AnalystSession(trade_date=date(2026, 8, 1), client=AIThemeFinancialClient.fixture_client())

    response = session.handle_text("今天怎么看？")
    unknown = session.handle_text("你好")

    assert response.intent == "morning_brief"
    assert response.evidence_refs
    assert response.rendered_evidence_links
    assert unknown.intent == "unknown"
    assert unknown.evidence_refs == ()


def test_response_envelope_is_complete_and_has_limitations() -> None:
    session = AnalystSession(trade_date=date(2026, 8, 1), client=AIThemeFinancialClient.fixture_client())
    response = session.handle_text("为什么关注华工科技？")

    assert response.intent == "deep_dive"
    assert response.context_scope
    assert isinstance(response.confidence, float)
    assert 0.0 <= response.confidence <= 1.0
    assert response.limitations
    assert all("EvidenceRef:" in item for item in response.rendered_evidence_links)


def test_websocket_api_symbol_exists_and_api_file_stays_transport_only() -> None:
    from runtime.capability.financial.interface.analyst_chat.api import analyst_chat, router

    assert analyst_chat is not None
    assert router is not None
    source = Path("runtime/capability/financial/interface/analyst_chat/api.py").read_text()
    assert "detect_intent" not in source
    assert "build_context" not in source


def test_voice_is_placeholder_only() -> None:
    assert VOICE_STATUS == "placeholder"
    assert voice_placeholder()["enabled"] is False


def test_four_file_boundary_and_forbidden_imports() -> None:
    base = Path("runtime/capability/financial/interface/analyst_chat")
    expected = {"api.py", "session.py", "context.py", "voice.py", "__init__.py"}
    assert {p.name for p in base.iterdir() if p.is_file()} == expected

    for path in base.glob("*.py"):
        tree = ast.parse(path.read_text())
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        assert [name for name in imports if name.startswith(("ai_theme_app", "sqlalchemy", "psycopg", "sqlite3", "memory"))] == []
        lowered = path.read_text().lower()
        assert not any(term in lowered for term in ("memory.write", "strategy.update", "profile.update", "trade("))


def test_response_has_no_trading_language() -> None:
    session = AnalystSession(trade_date=date(2026, 8, 1), client=AIThemeFinancialClient.fixture_client())
    for text in ["今天怎么看？", "为什么关注华工科技？", "帮我研究一下PCB?"]:
        response = session.handle_text(text)
        lowered = repr(response).lower()
        assert not any(term in lowered for term in FORBIDDEN_RESPONSE_TERMS)
