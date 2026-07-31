"""Session boundary and deterministic keyword intent detection for F4."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import uuid4

import runtime.capability.financial.contracts as c
from runtime.capability.financial.client.ai_theme_client import AIThemeFinancialClient
from runtime.capability.financial.interface.analyst_chat.context import build_context


@dataclass(frozen=True, slots=True)
class AnalystResponseEnvelope:
    session_id: str
    intent: str
    text: str
    evidence_refs: tuple[c.EvidenceRef, ...]
    rendered_evidence_links: tuple[str, ...]
    context_scope: tuple[str, ...]
    confidence: float
    limitations: tuple[str, ...]
    status: str


@dataclass(slots=True)
class AnalystSession:
    trade_date: date
    client: AIThemeFinancialClient = field(default_factory=AIThemeFinancialClient.fixture_client)
    session_id: str = field(default_factory=lambda: f"analyst-session-{uuid4().hex}")
    closed: bool = False

    def handle_text(self, message: str) -> AnalystResponseEnvelope:
        intent = detect_intent(message)
        context = build_context(self, intent, message)
        text, confidence, limitations = _compose_text(intent, context)
        return AnalystResponseEnvelope(
            session_id=self.session_id,
            intent=intent,
            text=text,
            evidence_refs=context.evidence_refs,
            rendered_evidence_links=tuple(f"EvidenceRef: {ref.ref_id}" for ref in context.evidence_refs),
            context_scope=context.context_scope,
            confidence=confidence,
            limitations=limitations,
            status="shadow",
        )

    def close(self) -> None:
        self.closed = True


def detect_intent(message: str) -> str:
    text = message.strip().lower()
    if "为什么" in text:
        return "deep_dive"
    if "今天" in text or "怎么看" in text:
        return "morning_brief"
    if "研究" in text or text.endswith("?") or text.endswith("？"):
        return "research"
    return "unknown"


def _compose_text(intent: str, context) -> tuple[str, float, tuple[str, ...]]:
    if intent == "morning_brief":
        themes = "、".join(theme.name for theme in context.top_themes) or "暂无重点题材"
        return (
            f"今天先看市场状态、重点题材和风险状态。当前重点题材包括：{themes}。这是条件观察层输出。",
            0.72,
            ("V0.1 只展示已有 EvidenceRef，不接实时新闻。",),
        )
    if intent == "deep_dive":
        names = "、".join(candidate.stock_name for candidate in context.candidates) or "目标候选"
        return (
            f"我会按目标证据解释 {names} 的观察逻辑，并标出当前证据限制。",
            0.68,
            ("V0.1 deep_dive 只加载目标证据，不加载历史 episode。",),
        )
    if intent == "research":
        return (
            "这是研究型问题。我会先列出证据缺口和下一步研究方向，不自动查询真实市场。",
            0.55,
            ("证据请求仅为草案，不自动触发外部查询。",),
        )
    return (
        "请告诉我你想研究的方向、标的或交易日，我再加载对应金融上下文。",
        0.0,
        ("unknown intent 不加载金融重上下文。",),
    )
