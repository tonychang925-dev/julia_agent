"""F0 read-only AI Theme financial capability client."""

import datetime as _dt

import runtime.capability.financial.contracts as c


class AIThemeFinancialClient:
    """Read-only client over a stable F0 financial briefing contract."""

    def __init__(self, provider_name: str = "fixture") -> None:
        self._provider_name = provider_name
        self._brief = _build_fixture_brief()
        self._evidence = {bundle.ref.ref_id: bundle for bundle in _build_fixture_evidence(self._brief)}

    @classmethod
    def fixture_client(cls, provider_name: str = "fixture") -> "AIThemeFinancialClient":
        return cls(provider_name=provider_name)

    def get_market_brief(self, trade_date: _dt.date, context_type: str) -> c.FinancialBriefingBundle:
        if trade_date != self._brief.trade_date:
            raise KeyError(f"no fixture snapshot for trade_date={trade_date.isoformat()}")
        if context_type != self._brief.context_type:
            raise KeyError(f"no fixture snapshot for context_type={context_type}")
        return self._brief

    def get_market_thesis(self, trade_date: _dt.date) -> c.MarketThesisView:
        brief = self.get_market_brief(trade_date, "premarket")
        return c.MarketThesisView(
            trade_date=brief.trade_date,
            thesis="市场维持结构性轮动，关注高证据质量主线的条件验证。",
            evidence_refs=brief.evidence_refs,
        )

    def get_attention_radar(self, trade_date: _dt.date) -> c.AttentionView:
        return self.get_market_brief(trade_date, "premarket").attention

    def get_risk_state(self, trade_date: _dt.date) -> c.RiskStateView:
        return self.get_market_brief(trade_date, "premarket").risk_state

    def get_top_themes(self, trade_date: _dt.date, limit: int = 10) -> tuple[c.ThemeView, ...]:
        return self.get_market_brief(trade_date, "premarket").top_themes[:limit]

    def get_w2s_candidates(self, trade_date: _dt.date) -> tuple[c.CandidateView, ...]:
        return tuple(
            candidate
            for candidate in self.get_market_brief(trade_date, "premarket").candidates
            if candidate.strategy_id == "weak_to_strong"
        )

    def get_candidate_watchlist(self, trade_date: _dt.date, strategy_id: str) -> tuple[c.CandidateView, ...]:
        return tuple(
            candidate
            for candidate in self.get_market_brief(trade_date, "premarket").candidates
            if candidate.strategy_id == strategy_id
        )

    def get_evidence(self, evidence_ref: str) -> c.EvidenceBundle:
        return self._evidence[evidence_ref]

    def get_evidence_for_object(
        self,
        object_type: str,
        object_id: str,
        trade_date: _dt.date,
    ) -> tuple[c.EvidenceBundle, ...]:
        self.get_market_brief(trade_date, "premarket")
        return tuple(
            bundle
            for bundle in self._evidence.values()
            if bundle.ref.object_type == object_type and bundle.ref.object_id == object_id
        )


def _ref(ref_id: str, object_type: str, object_id: str, snapshot_id: str) -> c.EvidenceRef:
    return c.EvidenceRef(
        ref_id=ref_id,
        object_type=object_type,
        object_id=object_id,
        trade_date=_dt.date(2026, 8, 1),
        source_snapshot_id=snapshot_id,
    )


def _build_fixture_brief() -> c.FinancialBriefingBundle:
    snapshot_ids = ("snapshot-20260801-preopen", "m7-risk-20260801")
    market_ref = _ref("market-20260801-001", "market", "A_SHARE", snapshot_ids[0])
    attention_ref = _ref("attention-20260801-001", "attention", "radar", snapshot_ids[0])
    theme_ref = _ref("theme-cpo-20260801", "theme", "CPO", snapshot_ids[0])
    w2s_ref = _ref("w2s-20260801-003", "stock", "000988", snapshot_ids[0])
    event_ref = _ref("event-20260801-001", "event", "overnight-ai-infra", snapshot_ids[0])
    risk_ref = _ref("risk-m7-20260801", "risk", "M7", snapshot_ids[1])
    hypothesis_ref = _ref("hypothesis-20260801-001", "hypothesis", "mainline-confirmation", snapshot_ids[0])

    risk_state = c.RiskStateView(
        trade_date=_dt.date(2026, 8, 1),
        risk_level="MODERATE",
        risk_flags=("avoid_late_stage_acceleration", "confirm_mainline_before_attention_upgrade"),
        gate_name="M7",
        evidence_refs=(risk_ref,),
    )
    top_themes = (
        c.ThemeView(
            theme_id="CPO",
            name="CPO/光通信",
            attention_level="HIGH",
            lifecycle_stage="diffusion",
            evidence_refs=(theme_ref, attention_ref),
        ),
        c.ThemeView(
            theme_id="ROBOTICS",
            name="机器人",
            attention_level="HIGH_DECAYING",
            lifecycle_stage="late_divergence",
            evidence_refs=(attention_ref, risk_ref),
        ),
    )
    candidates = (
        c.CandidateView(
            stock_code="000988",
            stock_name="华工科技",
            strategy_id="weak_to_strong",
            opportunity_type="conditional_observation",
            observation_level="A",
            thesis="CPO 主线若获得竞价确认，该候选可进入条件观察。",
            evidence_refs=(w2s_ref, theme_ref, risk_ref),
        ),
    )
    events = (
        c.EventView(
            event_id="overnight-ai-infra",
            title="AI 基建链隔夜事件增强",
            event_type="news_driver",
            impact_level="MEDIUM",
            evidence_refs=(event_ref,),
        ),
    )
    hypotheses = (
        c.HypothesisView(
            hypothesis_id="mainline-confirmation",
            trade_date=_dt.date(2026, 8, 1),
            statement="若 CPO 龙头竞价不弱且成交维持，则主线确认概率提升。",
            status="shadow",
            evidence_refs=(hypothesis_ref, theme_ref),
        ),
    )
    evidence_refs = (market_ref, attention_ref, theme_ref, w2s_ref, event_ref, risk_ref, hypothesis_ref)
    return c.FinancialBriefingBundle(
        bundle_id="briefing-20260801-premarket-fixture",
        trade_date=_dt.date(2026, 8, 1),
        as_of=_dt.datetime(2026, 8, 1, 8, 0, 0),
        context_type="premarket",
        market_state=c.MarketStateView(
            trade_date=_dt.date(2026, 8, 1),
            market_phase="preopen",
            risk_appetite="controlled_aggressive",
            turnover_state="warming",
            evidence_refs=(market_ref,),
        ),
        attention=c.AttentionView(
            trade_date=_dt.date(2026, 8, 1),
            attention_level="HIGH",
            top_theme_ids=tuple(theme.theme_id for theme in top_themes),
            evidence_refs=(attention_ref,),
        ),
        top_themes=top_themes,
        candidates=candidates,
        news_drivers=events,
        risk_state=risk_state,
        active_hypotheses=hypotheses,
        source_snapshot_ids=snapshot_ids,
        producer_versions={"analyst_gateway": "f0.fixture.v1", "m7_risk": "f0.fixture.v1"},
        module_coverage={"market_state": "fixture", "attention": "fixture", "w2s": "fixture", "risk": "fixture"},
        evidence_refs=evidence_refs,
    )


def _build_fixture_evidence(brief: c.FinancialBriefingBundle) -> tuple[c.EvidenceBundle, ...]:
    observed_at = brief.as_of
    bundles = []
    for ref in brief.evidence_refs:
        bundles.append(
            c.EvidenceBundle(
                ref=ref,
                title=f"F0 evidence {ref.ref_id}",
                summary=f"Frozen fixture evidence for {ref.object_type}:{ref.object_id}.",
                source_type="frozen_fixture",
                source_snapshot_id=ref.source_snapshot_id,
                observed_at=observed_at,
                producer_version="f0.fixture.v1",
            )
        )
    return tuple(bundles)
