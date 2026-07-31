# Julia Financial Analyst — Phase F0 Codex Task Specification

> **从属文档**: Julia_Financial_Analyst_Integration_Design_v1.0.md  
> **目标执行者**: Codex  
> **审查者**: Claude (Julia session)  
> **原则**: 测试先行、只读接口、Typed Contract、不直连数据库

---

## TASK F0.1 — ai_theme_app Analyst Gateway Contracts

**文件**: `ai_theme_app/analyst_gateway/contracts/`

**创建以下文件，每个文件一个dataclass：**

### F0.1.1 `market_brief.py`

```python
from dataclasses import dataclass
from datetime import date, datetime
from typing import Mapping, Tuple

@dataclass(frozen=True, slots=True)
class FinancialBriefingBundle:
    bundle_id: str
    trade_date: date
    as_of: datetime
    context_type: str
    market_state: "MarketStateView"
    attention: "AttentionView"
    top_themes: Tuple["ThemeView", ...]
    candidates: Tuple["CandidateView", ...]
    news_drivers: Tuple["EventView", ...]
    risk_state: "RiskStateView"
    active_hypotheses: Tuple["HypothesisView", ...]
    source_snapshot_ids: Tuple[str, ...]
    producer_versions: Mapping[str, str]
    module_coverage: Mapping[str, str]
    evidence_refs: Tuple[str, ...]
    schema_version: str
```

### F0.1.2 `market_state.py`

```python
from dataclasses import dataclass
from datetime import date, datetime

@dataclass(frozen=True, slots=True)
class MarketStateView:
    trade_date: date
    as_of: datetime
    market_phase: str               # trending_up / trending_down / ranging / volatile
    index_summary: str              # 主要指数表现概述
    volume_trend: str               # 量能趋势: expanding / contracting / stable
    breadth_summary: str            # 涨跌比概述
    leading_sectors: tuple[str, ...]
    lagging_sectors: tuple[str, ...]
    evidence_ref: str

@dataclass(frozen=True, slots=True)
class RiskStateView:
    trade_date: date
    risk_level: str                 # LOW / MODERATE / ELEVATED / HIGH / EXTREME
    risk_factors: tuple[str, ...]
    trading_allowed: bool
    position_limit_pct: float
    special_restrictions: tuple[str, ...]
    evidence_ref: str
```

### F0.1.3 `theme_view.py`

```python
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True, slots=True)
class ThemeView:
    subject_id: str
    theme_name: str
    trade_date: date
    attention_level: str            # CRITICAL / HIGH / MEDIUM / LOW
    attention_score: float
    lifecycle_stage: str            # emerging / diffusing / accelerating / climax / declining
    rank_in_sector: int
    key_drivers: tuple[str, ...]
    leader_stocks: tuple[str, ...]
    capital_flow_summary: str
    evidence_refs: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class ThemeAnalysisView:
    subject_id: str
    theme_name: str
    trade_date: date
    attention: "AttentionView"
    causal_chain: tuple[str, ...]   # 事件→题材→扩散 因果链
    lifecycle_assessment: str
    capital_structure: str          # 机构/游资/散户结构
    leader_evolution: str           # 龙头生命周期状态
    risk_assessment: str
    evidence_refs: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class AttentionView:
    trade_date: date
    total_themes_observed: int
    high_attention_themes: int
    top_theme_ids: tuple[str, ...]
    cognitive_budget_used: int
    evidence_ref: str
```

### F0.1.4 `stock_view.py`

```python
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True, slots=True)
class StockAnalysisView:
    stock_code: str
    stock_name: str
    trade_date: date
    close_price: float
    pct_change: float
    volume_ratio: float             # 相对量比
    belongs_to_themes: tuple[str, ...]
    theme_role: str                 # 龙头/中军/补涨/跟风
    technical_summary: str
    capital_flow_summary: str
    evidence_refs: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class CandidateView:
    stock_code: str
    stock_name: str
    trade_date: date
    strategy_id: str                # weak_to_strong / mainline_rotation / etc
    candidate_rank: int
    signal_strength: str            # STRONG / MODERATE / WEAK
    key_signals: tuple[str, ...]
    entry_zone_low: float | None
    entry_zone_high: float | None
    invalidation_price: float | None
    evidence_refs: tuple[str, ...]
```

### F0.1.5 `event_view.py`

```python
from dataclasses import dataclass
from datetime import date, datetime

@dataclass(frozen=True, slots=True)
class EventView:
    event_id: str
    trade_date: date
    published_at: datetime
    title: str
    summary: str
    event_type: str                 # news / announcement / policy / external
    impact_level: str               # HIGH / MEDIUM / LOW
    affected_themes: tuple[str, ...]
    affected_stocks: tuple[str, ...]
    evidence_ref: str
```

### F0.1.6 `hypothesis_view.py`

```python
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True, slots=True)
class HypothesisView:
    hypothesis_id: str
    trade_date: date
    thesis: str
    status: str                     # active / confirmed / falsified / expired
    expected_observations: tuple[str, ...]
    actual_observations: tuple[str, ...]
    evidence_refs: tuple[str, ...]
```

### F0.1.7 `evidence_bundle.py`

```python
from dataclasses import dataclass
from datetime import date, datetime

@dataclass(frozen=True, slots=True)
class EvidenceRef:
    ref_id: str
    ref_type: str                   # theme / stock / event / market_state / hypothesis
    object_id: str
    trade_date: date
    source_module: str              # M1 / M2 / M3 / M8 / etc
    source_version: str
    frozen_at: datetime
    description: str

@dataclass(frozen=True, slots=True)
class EvidenceBundle:
    ref: EvidenceRef
    content: str
    data_quality: str               # HIGH / MEDIUM / LOW / UNAVAILABLE
    limitations: tuple[str, ...]
```

### F0.1.8 `__init__.py`

Re-export all public types.

**验收**:
```
python3 -c "from ai_theme_app.analyst_gateway.contracts import *; print('All contracts importable')"
```

---

## TASK F0.2 — ai_theme_app Analyst Gateway API

**文件**: `ai_theme_app/analyst_gateway/api/analyst_api.py`

**创建只读API类**:

```python
class AnalystAPI:
    """Read-only gateway for Julia Financial Analyst. Never writes to business tables."""

    def get_market_brief(self, trade_date: date, context_type: str = "full") -> FinancialBriefingBundle:
        """聚合市场概览 — 盘前研究入口"""
        ...

    def get_market_thesis(self, trade_date: date) -> MarketStateView:
        """M8 Market Thesis 输出"""
        ...

    def get_attention_radar(self, trade_date: date) -> AttentionView:
        """M8.5 Attention Engine 输出"""
        ...

    def get_top_themes(self, trade_date: date, limit: int = 10) -> tuple[ThemeView, ...]:
        """今日关注度最高的题材"""
        ...

    def get_theme_analysis(self, subject_id: str, trade_date: date) -> ThemeAnalysisView:
        """单个题材深度分析"""
        ...

    def get_stock_analysis(self, stock_code: str, trade_date: date) -> StockAnalysisView:
        """单只股票综合分析"""
        ...

    def get_candidate_watchlist(self, trade_date: date, strategy_id: str | None = None) -> tuple[CandidateView, ...]:
        """所有策略的候选池，可按策略过滤"""
        ...

    def get_w2s_candidates(self, trade_date: date) -> tuple[CandidateView, ...]:
        """弱转强候选池 (strategy_id='weak_to_strong')"""
        ...

    def get_risk_state(self, trade_date: date) -> RiskStateView:
        """M7 风险状态"""
        ...

    def get_daily_events(self, trade_date: date) -> tuple[EventView, ...]:
        """当日事件驱动列表"""
        ...

    def get_evidence(self, ref_id: str) -> EvidenceBundle:
        """展开单个 EvidenceRef"""
        ...

    def get_active_hypotheses(self, trade_date: date) -> tuple[HypothesisView, ...]:
        """当前活跃假设"""
        ...

    def health_check(self) -> dict:
        """连通性检查"""
        ...
```

**实现约束**:
- 所有方法只读，不写数据库
- 数据缺失返回空tuple或标记 `data_quality=UNAVAILABLE`
- 不 import ai_theme_app 内部未冻结的模块
- 通过现有的 M8/M8.5 输出接口获取数据

**验收**:
```python
api = AnalystAPI()
assert api.health_check()["status"] == "ok"
brief = api.get_market_brief(date.today(), "full")
assert brief.schema_version == "julia.financial.briefing.v1"
```

---

## TASK F0.3 — Julia Financial Contracts

**文件**: `julia_agent/runtime/capability/financial/contracts/`

**创建以下文件，镜像 ai_theme_app 的类型定义：**

### F0.3.1 文件列表

```
contracts/
├── __init__.py
├── briefing.py          # FinancialBriefingBundle
├── market_state.py      # MarketStateView, RiskStateView
├── theme_view.py         # ThemeView, ThemeAnalysisView, AttentionView
├── stock_view.py         # StockAnalysisView, CandidateView
├── event_view.py         # EventView
├── hypothesis_view.py    # HypothesisView
├── evidence_bundle.py    # EvidenceRef, EvidenceBundle
└── investment_case.py    # InvestmentCase, Scenario (Julia侧独有)
```

### F0.3.2 `investment_case.py` (Julia 独有，不在 ai_theme_app 侧)

```python
from dataclasses import dataclass
from datetime import date

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
    causal_chain: tuple[str, ...]
    theme_role: str
    stock_role: str
    lifecycle_stage: str
    supporting_evidence_refs: tuple[str, ...]
    counter_evidence_refs: tuple[str, ...]
    entry_conditions: tuple[str, ...]
    confirmation_conditions: tuple[str, ...]
    invalidation_conditions: tuple[str, ...]
    exit_conditions: tuple[str, ...]
    expected_scenarios: tuple[Scenario, ...]
    prediction_probability: float
    source_quality_score: float
    risk_flags: tuple[str, ...]
    max_attention_level: str       # A / B / C
    generated_by: str
    model_version: str
    policy_versions: dict[str, str]
    status: str                    # draft / reviewed / approved / rejected / frozen

@dataclass(frozen=True, slots=True)
class Scenario:
    scenario_id: str
    description: str
    probability: float
    expected_observations: tuple[str, ...]
    falsifiers: tuple[str, ...]
```

**验收**:
```python
from julia_agent.runtime.capability.financial.contracts import *
ic = InvestmentCase(case_id="test", trade_date=date.today(), ...)
assert ic.status == "draft"
```

---

## TASK F0.4 — Julia Financial Client

**文件**: `julia_agent/runtime/capability/financial/client/ai_theme_client.py`

**创建Julia侧客户端**:

```python
class AIThemeClient:
    """Julia's read-only client to ai_theme_app Analyst Gateway."""

    def __init__(self, gateway: "AnalystGatewayProtocol"):
        self._gateway = gateway

    def get_daily_briefing(self, trade_date: date) -> FinancialBriefingBundle:
        """早晨拉取完整市场简报"""
        ...

    def get_premarket_context(self, trade_date: date) -> dict:
        """拼接盘前Context: Market Overview + Attention Pack"""
        ...

    def get_targeted_evidence(self, refs: tuple[str, ...]) -> tuple[EvidenceBundle, ...]:
        """按需展开证据"""
        ...

    def get_stock_deep_dive(self, stock_code: str, trade_date: date) -> dict:
        """个股深度分析 (Tony 问某只股票时调用)"""
        ...

    def health_check(self) -> bool:
        ...
```

**客户端约束**:
- 只通过 `AnalystGatewayProtocol` 调用
- 不 import ai_theme_app 内部模块
- 所有异常转为 Julia 可消费的错误类型
- 网络/数据异常不 crash Julia ConversationLoop

**验收**:
```python
client = AIThemeClient(gateway=LocalMockGateway())  # 本地 mock 用于测试
assert client.health_check()
briefing = client.get_daily_briefing(date.today())
assert briefing.schema_version is not None
```

---

## TASK F0.5 — F0 集成测试

**文件**: `julia_agent/tests/test_financial_f0_contract.py`

**10项验收测试**:

```python
class TestF0ContractReadiness:

    def test_01_all_contracts_importable(self):
        """Julia侧和ai_theme_app侧所有contract类型可导入"""

    def test_02_briefing_bundle_has_evidence_refs(self):
        """每个BriefingBundle携带evidence_refs"""

    def test_03_candidate_view_has_evidence_refs(self):
        """每个CandidateView携带evidence_refs"""

    def test_04_investment_case_is_frozen(self):
        """InvestmentCase创建后不可修改"""

    def test_05_client_does_not_import_ai_theme_internals(self):
        """AIThemeClient不import ai_theme_app内部模块"""

    def test_06_health_check_roundtrip(self):
        """Julia → ai_theme_app 健康检查通过"""

    def test_07_get_market_brief_returns_valid_bundle(self):
        """get_market_brief返回完整FinancialBriefingBundle"""

    def test_08_get_w2s_candidates_returns_candidates(self):
        """get_w2s_candidates返回弱转强候选"""

    def test_09_evidence_ref_can_be_resolved(self):
        """EvidenceRef可以展开为EvidenceBundle"""

    def test_10_provider_switch_preserves_contract(self):
        """切换Provider后输出契约保持一致"""
```

---

## 实现顺序与依赖

```
F0.1 (ai_theme_app contracts)     ← 最先，无依赖
    ↓
F0.2 (ai_theme_app API)           ← 依赖 F0.1
    ↓
F0.3 (Julia contracts)            ← 镜像 F0.1，无代码依赖
    ↓
F0.4 (Julia client)               ← 依赖 F0.2 + F0.3
    ↓
F0.5 (集成测试)                    ← 依赖全部
```

---

## 工程约束 (Codex 必须遵守)

1. 所有 dataclass 使用 `frozen=True, slots=True`
2. 所有 tuple 字段使用 `tuple[...]` 而非 `list[...]`
3. 不直接使用 `dict` 作为公共接口 — 用 dataclass
4. 日期字段统一 `from datetime import date`
5. 所有 EvidenceRef 包含 source_module + source_version
6. Julia 侧客户端不 import ai_theme_app 任何模块
7. ai_theme_app AnalystAPI 不写数据库
8. 测试文件独立可运行: `python3 -m pytest tests/test_financial_f0_contract.py -v`
