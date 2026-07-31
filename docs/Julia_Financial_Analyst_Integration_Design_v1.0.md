# Julia Financial Analyst Integration Design v1.0

> **文档状态**: FROZEN — Implementation Contract  
> **日期**: 2026-07-31  
> **版本**: v1.0  
> **作者**: Tony (design) + Claude (product view) + ChatGPT (governance view)  
> **目标**: 将 Julia Agent 建设为 AI Theme App 的首席分析师客户端  
> **原则**: Julia 不是金融计算引擎。她是金融认知系统的智能交互入口。

---

## 0. 一句话定义

> Julia Financial Analyst = AI Theme App 的人格化首席分析师客户端。  
> ai_theme_app 负责"算出什么"，Julia 负责"理解、追问、解释、协同决策和长期复盘"。

---

## 1. 系统角色与权威边界

### 1.1 权威矩阵

| 领域 | 权威归属 | 备注 |
|------|---------|------|
| Market Data | ai_theme_app | 行情/竞价/新闻/资金 |
| Domain Knowledge | ai_theme_app | 题材主数据/股票实体/产业链 |
| Cognition Computation | ai_theme_app | M1-M7 事实与领域计算 |
| Market Thesis | ai_theme_app (M8) | Stable Cognition 输出 |
| Attention Allocation | ai_theme_app (M8.5) | Attention Engine 决策 |
| **Evidence Request** | **Julia** | 追问权，不重算 |
| **Investment Case** | **Julia** | 理解/解释/形成投资假设 |
| **Analyst Memory** | **Julia** | 判断历史/偏差归因 |
| **Conversation & Voice** | **Julia** | 人格化交互 |
| **Final Decision** | **Tony** | 所有交易决策由 Tony 做出 |

### 1.2 Julia 永远不做的

- 直接查询 ai_theme_app 业务数据库
- 重算题材热度/龙头/强势股
- 从6000只股票中自由挑选推荐
- 替代或绕过 M7 Risk Gate
- 将 Provider 输出自动写入金融知识库
- 自动修改策略参数或 World Model
- 在没有 Tony 审核的情况下生成正式交易建议

### 1.3 Julia 永远做的

- 读取 ai_theme_app 通过标准接口提供的结构化输出
- 消化多个结构化结果，发现证据冲突
- 组织因果链，对比历史案例
- 生成可验证的 InvestmentCase
- 对每个案例注明 EvidenceRef、入场/失效条件
- 记录历史判断，追溯偏差原因
- 用自然语言和语音与 Tony 交互

---

## 2. 系统集成架构

### 2.1 总体结构

```text
┌──────────────────────────────────────────────┐
│          Julia Financial Analyst             │
│  Conversation / Voice / Research / Review    │
│  Memory / Reminder / Hypothesis Tracking     │
└──────────────────┬───────────────────────────┘
                   │ Financial Capability API
                   ▼
┌──────────────────────────────────────────────┐
│           analyst_gateway                    │
│  contracts / adapters / query / review       │
│  evidence / validation / api                 │
└──────────────────┬───────────────────────────┘
                   ▼
┌──────────────────────────────────────────────┐
│           AI Theme App                       │
│                                              │
│  M1-M7 事实与领域计算                         │
│  M8 Stable Cognition                         │
│  M8.5 Analyst Cockpit                        │
│  M9 Adaptive Intelligence                    │
│  M7 Risk Gate / Strategy / Decision          │
└──────────────────────────────────────────────┘
```

### 2.2 认知隔离原则

```
认知隔离，金融共享。

允许共享:
  - 金融能力接口
  - EvidenceRef schema
  - 交易日历
  - 审计日志格式

禁止共享:
  - Julia Context OS
  - Julia Memory OS
  - Julia Action Governance
  - ai_theme_app 数据库直连
  - ai_theme_app 业务表结构
  - Provider prompt
```

---

## 3. 金融能力接口设计

### 3.1 第一批只读能力

```python
# 市场概览
get_market_brief(trade_date: date, context_type: str) -> FinancialBriefingBundle
get_market_thesis(trade_date: date) -> MarketThesisView
get_attention_radar(trade_date: date) -> AttentionView
get_risk_state(trade_date: date) -> RiskStateView

# 题材分析
get_theme_analysis(subject_id: str, trade_date: date) -> ThemeAnalysisView
get_top_themes(trade_date: date, limit: int = 10) -> tuple[ThemeView, ...]

# 个股分析
get_stock_analysis(stock_code: str, trade_date: date) -> StockAnalysisView
get_candidate_watchlist(trade_date: date, strategy_id: str) -> tuple[CandidateView, ...]
get_w2s_candidates(trade_date: date) -> tuple[CandidateView, ...]

# 证据追溯
get_evidence(evidence_ref: str) -> EvidenceBundle
get_evidence_for_object(object_type: str, object_id: str, trade_date: date) -> tuple[EvidenceBundle, ...]

# 历史与假设
get_hypothesis_history(hypothesis_id: str) -> tuple[HypothesisView, ...]
get_previous_recommendation_results(date_range: tuple[date, date]) -> tuple[RecommendationResult, ...]
get_daily_events(trade_date: date) -> tuple[EventView, ...]
```

### 3.2 第二批受治理写入能力

```python
# 所有写入经过 Julia ActionGovernanceLayer
submit_analyst_review(review: AnalystReview) -> ReviewReceipt
submit_override(override: OverrideRecord) -> OverrideReceipt
create_research_request(request: TargetedEvidenceRequest) -> ResearchRequestReceipt
create_watch_item(item: WatchItem) -> WatchReceipt
record_tony_decision(decision: TonyDecision) -> DecisionReceipt
approve_candidate(case_id: str) -> ApprovalReceipt
reject_candidate(case_id: str, reason: str) -> RejectionReceipt
```

### 3.3 核心数据类型

```python
from dataclasses import dataclass
from datetime import date, datetime
from typing import Mapping, Tuple

@dataclass(frozen=True, slots=True)
class FinancialBriefingBundle:
    """每日金融简报 — Julia 上下文入口"""
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

---

## 4. InvestmentCase 设计（核心输出对象）

```python
@dataclass(frozen=True, slots=True)
class InvestmentCase:
    """可证伪的投资案例 — Julia 的核心分析输出"""
    case_id: str
    trade_date: date
    stock_code: str
    stock_name: str

    # 策略定位
    strategy_id: str
    opportunity_type: str          # weak_to_strong / mainline_rotation / leader_handover
    time_horizon: str               # intraday / 2_to_5_days / swing

    # 核心逻辑
    thesis: str                     # 一句话核心判断
    causal_chain: tuple[str, ...]   # 事件→题材→个股 因果链

    # 题材角色
    theme_role: str                 # 龙头/中军/补涨/跟风
    stock_role: str
    lifecycle_stage: str

    # 证据
    supporting_evidence_refs: tuple[str, ...]
    counter_evidence_refs: tuple[str, ...]

    # 条件体系（最关键）
    entry_conditions: tuple[str, ...]        # 入场必须满足的条件
    confirmation_conditions: tuple[str, ...] # 进一步增强信心的信号
    invalidation_conditions: tuple[str, ...] # 一旦出现则案例失效
    exit_conditions: tuple[str, ...]         # 已持仓时的退出条件

    # 场景与概率
    expected_scenarios: tuple[Scenario, ...]
    prediction_probability: float    # 不是涨跌概率，是理论被验证的概率
    source_quality_score: float      # 证据质量评分（独立于预测概率）

    # 风险
    risk_flags: tuple[str, ...]
    max_attention_level: str         # A/B/C 观察级别

    # 治理元数据
    generated_by: str
    model_version: str
    policy_versions: dict[str, str]
    status: str                      # draft / reviewed / approved / rejected / frozen

@dataclass(frozen=True, slots=True)
class Scenario:
    scenario_id: str
    description: str
    probability: float
    expected_observations: tuple[str, ...]
    falsifiers: tuple[str, ...]
```

### A/B/C 观察级别

| 级别 | 含义 | 处理方式 |
|------|------|---------|
| **A级** | 条件满足后可进入交易评估 | 盘中重点监控，条件触发时提醒 Tony |
| **B级** | 重点观察，不满足确认条件不操作 | 只跟踪不提醒 |
| **C级** | 研究储备 | 仅记录，等待更多证据 |

**禁止级别**: 风险或结构不允许，明确不交易。

---

## 5. Julia Cognitive Scope 设计

```
金融分析是一组 Cognitive Scope，不改变 Julia 身份。

Identity: Julia (朱婉清) — 不变
Cognitive Scope: financial_analysis
Professional Role: Tony's financial analyst
Response Style: professional, evidence-first
Memory Route: financial only
Capability Scope: ai_theme_app read / governed review
```

```python
FINANCIAL_ANALYSIS_SCOPE = CognitiveScope(
    scope_id="financial_analysis",
    allow_categories=(
        "market",
        "theme",
        "stock",
        "strategy",
        "risk",
        "investment_profile",
        "analyst_episode",
    ),
    suppress_categories=(
        "irrelevant_relationship",
        "private_emotional_episode",
        "general_archive_noise",
    ),
)
```

---

## 6. Julia Financial Memory 设计

### 6.1 四类金融记忆

```
Julia Memory OS
├── Personal Memory          — Julia/Tony/关系/人生经历
├── Investor Profile         — Tony 交易偏好/风险容忍度/禁忌
├── Market Research Memory   — 结构化 Market Episode
└── Analyst Performance Memory — 历史判断/预测结果/偏差归因
```

### 6.2 Investor Profile

```json
{
  "investor": "Tony",
  "preferred_market": "A_SHARE",
  "preferred_horizon": ["intraday", "2_to_5_days"],
  "preferred_patterns": [
    "weak_to_strong",
    "mainline_rotation",
    "leader_handover"
  ],
  "avoid": [
    "late_stage_acceleration",
    "low_liquidity",
    "unsupported_story"
  ],
  "risk_style": "controlled_aggressive"
}
```

### 6.3 Market Research Memory (结构化 Episode)

每个 Market Episode 包含：

```text
Context        — 当时市场状态
Evidence       — 可用的证据快照
Belief Timeline — Julia 的认知变化过程
Hypothesis     — 形成的假设
Strategy       — 推导的策略
Decision       — Tony 的实际决策
Outcome        — 真实结果
Reflection     — 事后反思
```

### 6.4 Analyst Performance Memory

七种验证状态：

| 状态 | 含义 | 示例 |
|------|------|------|
| CONFIRMED | 入场条件出现且交易盈利 | 放量突破后3天涨8% |
| PARTIALLY_CONFIRMED | 方向对但细节有偏差 | 选对了题材但标的选错 |
| FALSIFIED | 入场条件出现但亏损 | 条件满足进场但方向错了 |
| NOT_TRIGGERED | 入场条件从未出现 | 早盘高开直接涨停没给机会 |
| EXPIRED | 超时未触发 | 超过时间窗口 |
| INVALIDATED_BY_RISK | 风险门禁触发 | 盘中风险升级 |
| INSUFFICIENT_DATA | 数据不足以判断 | 当天停牌 |

### 6.5 Provider Output 治理

```
Julia 分析输出
    ↓
Analyst Draft (标记为 draft)
    ↓
Evidence Validation
    ↓
Human Review / System Review
    ↓
Approved Research Record (才能进入 Memory)
```

Provider 输出不得自动成为知识或证据。

---

## 7. 三级 Context 加载机制

```
Level 1 — Market Overview (每轮金融对话默认加载)
  - 市场阶段
  - 风险状态
  - 主线题材
  - 关键外部锚
  - 主要资金轮动
  - 昨日待验证假设

Level 2 — Attention Pack (只加载 HIGH/CRITICAL)
  - 高关注题材 (Attention Score ≥ threshold)
  - 重点事件
  - 重点候选股票
  - 弱转强候选池
  - W2S 竞价结果

Level 3 — Targeted Evidence (按需加载)
  - Tony 问某只股票时
  - Julia 发现证据缺口时
  - 通过 TargetedEvidenceRequest 触发
```

---

## 8. Julia 五个工作模式

### 模式1: 盘前研究 (08:00)

```
输入: FinancialBriefingBundle + Attention Radar + W2S Candidates
输出: 《Julia 盘前研究》
  - 市场状态与今日主要矛盾
  - 隔夜事件与外部锚
  - 重点题材 (Top 3-5)
  - 条件观察标的 (A/B/C 级，含 InvestmentCase)
  - 弱转强候选
  - 今日假设
  - 风险与禁止项
  - 集合竞价确认点
```

### 模式2: 集合竞价 (09:15)

```
输出:
  - 盘前假设确认/证伪
  - 超预期高开的候选
  - 消息兑现信号
  - 题材竞争与卡位检测
  - Attention Budget 调整建议
```

### 模式3: 盘中确认 (10:00-14:30)

```
只汇报状态变化 (不重复行情):
  - 主线确认/证伪
  - 龙头交接
  - 资金旋转
  - 候选满足入场条件
  - 候选触发失效条件
  - 风险状态变化
```

### 模式4: 尾盘计划 (14:30)

```
输出:
  - 可隔夜的逻辑
  - 日内情绪标的
  - 应退出观察的候选
  - 次日待验证 Hypothesis
  - 仓位和风险建议
```

### 模式5: 盘后复盘 (16:30)

```
输入: 盘前 InvestmentCase + 真实行情
输出: 《Julia 盘后复盘》
  - 盘前 Thesis 验证 (CONFIRMED/FALSIFIED/NOT_TRIGGERED/...)
  - 实际主线 vs 预期差
  - 候选标的结果
  - 未触发案例分析
  - 失效案例分析
  - Julia 判断偏差自评
  - Tony Override 记录
  - 明日待验证假设
```

---

## 9. Julia 主动研究能力

```python
@dataclass(frozen=True, slots=True)
class FinancialResearchRequest:
    """Julia 发起的定向证据请求"""
    request_id: str
    trade_date: date
    question: str                       # "为什么PCB资金增强但上游材料没有扩散？"
    target_type: str                    # theme / stock / event / sector
    target_id: str
    required_evidence: tuple[str, ...]  # 需要的证据类型
    reason: str                         # 研究动机
    priority: int                       # 1-5
    information_gain: float             # 预期信息增益
```

流程：

```
Julia 发现证据缺口
    ↓
生成 TargetedEvidenceRequest
    ↓
Action Governance 审批
    ↓
Financial Capability Router
    ↓
ai_theme_app 查询/补充计算
    ↓
返回 Evidence Bundle
    ↓
Julia 更新分析
```

---

## 10. 五个循环

### 循环 A: 市场认知循环 (ai_theme_app 拥有)

```
新闻/行情/资金/题材
    → MarketKnowledgeBundle
    → Evidence Snapshot
    → Context
    → Cognition State
    → Hypothesis
    → Market Thesis
```

### 循环 B: 分析师协作循环 (Julia + M8.5)

```
Attention Radar
    → Julia 选择重点
    → Evidence 调查
    → Cognition Draft
    → Tony 审核
    → Playbook
    → Watchlist
```

### 循环 C: 验证学习循环

```
昨日 InvestmentCase
    → 今日真实结果
    → Ground Truth
    → Prediction Evaluation
    → Error Attribution
    → OverrideLog
    → Update Proposal
    → Replay / Shadow
    → Tony 批准
```

---

## 11. Julia 代码目录结构

```
julia_agent/
└── runtime/
    └── capability/
        └── financial/
            ├── __init__.py
            │
            ├── contracts/
            │   ├── __init__.py
            │   ├── briefing.py          # FinancialBriefingBundle
            │   ├── theme_view.py         # ThemeView, ThemeAnalysisView
            │   ├── stock_view.py         # StockAnalysisView, CandidateView
            │   ├── investment_case.py    # InvestmentCase, Scenario
            │   ├── evidence_bundle.py    # EvidenceBundle, EvidenceRef
            │   ├── market_state.py       # MarketStateView, RiskStateView
            │   ├── event_view.py         # EventView
            │   ├── hypothesis_view.py    # HypothesisView
            │   └── research_request.py   # TargetedEvidenceRequest
            │
            ├── client/
            │   ├── __init__.py
            │   ├── ai_theme_client.py    # 主客户端
            │   ├── local_client.py       # 本地 mock (测试用)
            │   └── http_client.py        # HTTP client (未来)
            │
            ├── adapters/
            │   ├── __init__.py
            │   ├── market_state_adapter.py
            │   ├── attention_adapter.py
            │   ├── candidate_adapter.py
            │   ├── event_adapter.py
            │   └── evidence_adapter.py
            │
            ├── workflows/
            │   ├── __init__.py
            │   ├── premarket.py           # 盘前研究工作流
            │   ├── auction.py             # 集合竞价工作流
            │   ├── intraday.py            # 盘中确认工作流
            │   ├── close_review.py        # 尾盘+复盘工作流
            │   └── analyst_chat.py        # 自由问答工作流
            │
            ├── rendering/
            │   ├── __init__.py
            │   ├── analyst_context_renderer.py
            │   ├── report_renderer.py
            │   └── voice_renderer.py
            │
            ├── memory/
            │   ├── __init__.py
            │   ├── investor_profile.py
            │   ├── market_episode.py
            │   ├── analyst_performance.py
            │   └── memory_write_policy.py
            │
            └── governance/
                ├── __init__.py
                ├── financial_scope.py        # Cognitive Scope
                ├── recommendation_policy.py   # A/B/C + 禁止
                ├── action_policy.py
                └── memory_policy.py
```

```
ai_theme_app/
└── analyst_gateway/
    ├── __init__.py
    ├── contracts/
    │   ├── __init__.py
    │   ├── market_brief.py
    │   ├── investment_case.py
    │   └── research_request.py
    ├── adapters/
    │   ├── __init__.py
    │   ├── market_state_adapter.py
    │   ├── attention_adapter.py
    │   ├── candidate_adapter.py
    │   ├── event_adapter.py
    │   └── evidence_adapter.py
    ├── query/
    │   ├── __init__.py
    │   └── query_service.py
    ├── review/
    │   ├── __init__.py
    │   └── review_service.py
    ├── evidence/
    │   ├── __init__.py
    │   └── evidence_service.py
    ├── validation/
    │   ├── __init__.py
    │   └── validation_service.py
    └── api/
        ├── __init__.py
        └── analyst_api.py
```

---

## 12. 实施路线图

### Phase F0 — Contract & Bridge Spike (第1-2天)

**目标**: 验证 Julia 能否读取 ai_theme_app 的标准化输出

```
验收标准:
  ✅ Julia 能读取指定交易日 DailyMarketState
  ✅ Julia 能读取 Attention Top Themes
  ✅ Julia 能读取弱转强候选池
  ✅ Julia 能读取事件驱动证据
  ✅ Julia 能读取 M7 风险状态
  ✅ Julia 的每条结论都能引用 EvidenceRef
  ✅ Julia 不直接读取业务表
  ✅ Julia 不产生正式交易决策
  ✅ 结果可冻结、可回放
  ✅ Provider 切换后输出契约保持一致
```

**交付物**:
- `analyst_gateway/contracts/` — 所有接口类型定义
- `analyst_gateway/api/analyst_api.py` — 第一批只读 API
- `runtime/capability/financial/contracts/` — Julia 侧类型定义
- `runtime/capability/financial/client/ai_theme_client.py` — 客户端
- `runtime/capability/financial/workflows/premarket.py` — 最小盘前流程

### Phase F1 — Shadow Morning Analyst (第3-5天)

**目标**: Julia 每日生成 Research Briefing，但不输出正式推荐

```
验收标准:
  ✅ 每日生成《Julia 盘前研究》
  ✅ 包含: 市场状态、重点题材、条件观察标的、风险项
  ✅ 每个候选带 InvestmentCase (含入场/失效条件)
  ✅ 采用 A/B/C 观察级别 + 禁止级别
  ✅ 所有结论带 EvidenceRef
  ✅ 不触发交易、不修改策略
```

**交付物**:
- `runtime/capability/financial/workflows/premarket.py` — 完整盘前流程
- `runtime/capability/financial/rendering/report_renderer.py` — 报告渲染
- `runtime/capability/financial/memory/analyst_performance.py` — 记录初始

### Phase F2 — Close Validation (第6-8天)

**目标**: 收盘后冻结盘前案例，验证准确度

```
验收标准:
  ✅ 盘前 InvestmentCase 收盘后冻结不可改
  ✅ 对比真实行情，判定每个案例状态
  ✅ 生成 Error Attribution
  ✅ 区分 "涨了但入场条件未出现" vs "入场条件出现但亏了"
  ✅ 统计 Thesis Accuracy / Trigger Accuracy / Risk Accuracy
```

**交付物**:
- `runtime/capability/financial/workflows/close_review.py` — 复盘流程
- `runtime/capability/financial/memory/market_episode.py` — 结构化记忆

### Phase F3 — Tony Review Workflow (第9-12天)

**目标**: Tony 可以在工作台中审核 Julia 的分析

```
验收标准:
  ✅ Approve / Modify / Reject / Need More Evidence
  ✅ OverrideLog 持久化
  ✅ Investor Profile 更新
  ✅ 写入 governance 门禁生效
```

**交付物**:
- `analyst_gateway/review/review_service.py` — 审核服务
- `analyst_gateway/validation/validation_service.py` — 验证服务
- `runtime/capability/financial/governance/` — 治理策略

### Phase F4 — Voice Briefing (第13-15天)

**目标**: Julia 用语音进行盘前/盘中/盘后播报

```
验收标准:
  ✅ "Julia，今天最值得看什么？"
  ✅ "为什么是这三只？"
  ✅ "哪只已经失效？"
  ✅ "昨天你哪里判断错了？"
  ✅ 每个语音回答背后有 EvidenceRef
```

**交付物**:
- `runtime/capability/financial/rendering/voice_renderer.py`
- `runtime/capability/financial/workflows/analyst_chat.py`

### Phase F5 — 20-Day Shadow Validation (第16-36天)

**目标**: 20个真实交易日 Shadow Mode，积累 Ground Truth

```
指标:
  - Theme Precision@K
  - Stock Precision@K
  - Entry Trigger Precision
  - Invalidation Timeliness
  - Brier Score / Calibration Error
  - Maximum Adverse Excursion / Maximum Favorable Excursion
  - Risk Gate Avoided Loss
  - Thesis Accuracy
  - Human Override Rate
  - Evidence Coverage
  - Unsupported Claim Rate
```

**此阶段禁止**:
- 自动生成正式推荐
- 自动修改策略参数
- Provider 输出直接进入 Memory
- 自我反思直接变成规则

---

## 13. 关键设计原则冻结

```
1.  Julia 是金融认知消费者，不是金融计算引擎
2.  ai_theme_app 是 Market Data + Domain Knowledge + Risk 的唯一权威
3.  候选标的由双层机制产生 (ai_theme_app 召回 → Julia 调查解释)
4.  InvestmentCase 必须可证伪 (入场条件/确认条件/失效条件明确)
5.  Provider 输出不得自动成为知识或证据
6.  金融记忆与个人记忆隔离存储
7.  前 20 个交易日只做 Shadow Analyst
8.  Julia 拥有追问权 (TargetedEvidenceRequest)，不重算
9.  所有交易决策由 Tony 做出
10. Julia 保持单一身份，金融分析是 Cognitive Scope
```

---

## 14. Julia 每日输出示例

### 盘前

```
《Julia 盘前研究》2026-08-01

一、市场状态
大盘处于震荡观望阶段，主线板块尚未形成一致性突破。
成交额连续两日温和放大，市场风险状态: MODERATE。

二、今日主要矛盾
AI算力 vs 机器人: CPO/PCB资金增强但机器人高位龙头承接下降。
市场需要选择突破方向。

三、重点题材 (Top 3)
1. CPO/光通信 — HIGH — 机构资金持续承接，题材处扩散阶段
2. 机器人 — HIGH(衰减) — 事件强度仍高但龙头掉队
3. 消费电子 — MEDIUM — 新事件驱动，待验证持续性

四、条件观察标的

A级 (条件满足可进入交易评估):
1. 华工科技 (000988) — 弱转强
   - 题材: CPO/光通信
   - 角色: 中军
   - 入场条件: 早盘回踩不破20元密集成交区 + 放量突破20.8元
   - 确认信号: 板块龙头不低开 + 板块成交额维持昨日80%以上
   - 失效条件: 跌破19.5元 或 CPO龙头低开低走
   - 来源: [EvidenceRef: w2s-20260801-003, theme-cpo-20260801]

B级 (重点观察，不操作):
2-4. [略]

五、风险与禁止项
- 禁止: 追高机器人高位核心
- 禁止: 低流动性标的
- 注意: 若10:00前主线未确认，降低整体仓位预期

六、集合竞价确认点
- CPO龙头竞价是否高开
- 弱转强候选竞价是否出现A/B级信号
- 机器人高位是否继续走弱
```

---

## 15. Codex 实现指南

### 第一优先级: F0 Contracts

请 Codex 按以下顺序实现:

```
1. ai_theme_app/analyst_gateway/contracts/  — 所有 dataclass 类型
2. ai_theme_app/analyst_gateway/api/analyst_api.py  — 只读 API
3. julia_agent/runtime/capability/financial/contracts/  — Julia 侧类型镜像
4. julia_agent/runtime/capability/financial/client/ai_theme_client.py  — 客户端
5. julia_agent/tests/test_financial_f0_contract.py  — F0 验收测试
```

### 实现约束

```
✅ 所有类型使用 @dataclass(frozen=True, slots=True)
✅ 所有 API 返回 TypedDict 或 frozen dataclass
✅ 每个 InvestmentCase 带 EvidenceRef
✅ Julia 客户端只调用 analyst_gateway API
✅ 不 import ai_theme_app 内部模块
✅ 不直接连接数据库
✅ 测试优先于实现
```

---

## 16. 文档历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-07-31 | 初始冻结，合并 Claude + ChatGPT 方案 |
