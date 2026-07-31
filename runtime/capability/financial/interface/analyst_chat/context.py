"""Intent-aware minimal context builder for F4 analyst chat."""

from __future__ import annotations

from dataclasses import dataclass

import runtime.capability.financial.contracts as c


@dataclass(frozen=True, slots=True)
class AnalystChatContext:
    intent: str
    context_scope: tuple[str, ...]
    market_state: c.MarketStateView | None
    top_themes: tuple[c.ThemeView, ...]
    risk_state: c.RiskStateView | None
    candidates: tuple[c.CandidateView, ...]
    target_evidence: tuple[c.EvidenceBundle, ...]
    evidence_refs: tuple[c.EvidenceRef, ...]


def build_context(session, intent: str, message: str) -> AnalystChatContext:
    brief = session.client.get_market_brief(session.trade_date, context_type="premarket")
    if intent == "morning_brief":
        refs = brief.market_state.evidence_refs + brief.attention.evidence_refs + brief.risk_state.evidence_refs
        return AnalystChatContext(
            intent=intent,
            context_scope=("market_state", "top_themes", "risk_state"),
            market_state=brief.market_state,
            top_themes=brief.top_themes[:5],
            risk_state=brief.risk_state,
            candidates=(),
            target_evidence=(),
            evidence_refs=refs,
        )
    if intent == "deep_dive":
        ref_ids = tuple(dict.fromkeys(ref.ref_id for ref in brief.evidence_refs))[:3]
        evidence = tuple(session.client.get_evidence(ref_id) for ref_id in ref_ids)
        return AnalystChatContext(
            intent=intent,
            context_scope=("target_candidate", "theme_evidence", "risk_evidence"),
            market_state=None,
            top_themes=(),
            risk_state=brief.risk_state,
            candidates=brief.candidates,
            target_evidence=evidence,
            evidence_refs=tuple(bundle.ref for bundle in evidence),
        )
    if intent == "research":
        return AnalystChatContext(
            intent=intent,
            context_scope=("theme_summary", "evidence_gap"),
            market_state=None,
            top_themes=brief.top_themes[:3],
            risk_state=None,
            candidates=brief.candidates,
            target_evidence=(),
            evidence_refs=brief.evidence_refs[:3],
        )
    return AnalystChatContext(
        intent="unknown",
        context_scope=(),
        market_state=None,
        top_themes=(),
        risk_state=None,
        candidates=(),
        target_evidence=(),
        evidence_refs=(),
    )
