# Phase Execution Contract — F0 Contract & Bridge Spike

## 1. Phase Identity

- **Phase Name**: Contract & Bridge Spike
- **Phase Code**: F0
- **Parent Milestone**: Julia Financial Analyst Integration / Shadow Analyst Foundation
- **Risk Level**: Medium
- **Status**: Draft → Consistency Checked → Final
- **Source Documents**:
  - `docs/Julia_Financial_Analyst_Integration_Design_v1.0.md` — FROZEN Implementation Contract, 2026-07-31
  - `docs/Julia_Agent_Frontier_Assessment_v0.1.md` — runtime-owned cognition / authority boundary reference
  - `docs/project_control/EXECUTION_GUARDRAILS.md` — referenced guardrail baseline; file not present in current workspace at generation time, must be created or confirmed before dev-orchestrator status sync

## 2. Phase Objective

在 F0 阶段内，以测试先行方式建立 Julia Agent 与 AI Theme App 之间的只读金融能力桥接契约，使 Julia 能通过 `analyst_gateway` 标准 API 读取指定交易日的市场、题材、候选、事件证据与风险状态，并在 Julia 侧通过 Typed Contract 形成可冻结、可回放、Provider 无关的 `FinancialBriefingBundle`；全阶段不得直连数据库、不得 import `ai_theme_app` 内部业务模块、不得产生正式交易决策。

## 3. Acceptance Targets

- [ ] **F0-AT-01 DailyMarketState 读取**：Julia 客户端可通过 `analyst_gateway.api.analyst_api.get_market_brief(trade_date, context_type)` 获取指定交易日的市场简报对象，返回对象包含 `trade_date`、`market_state`、`schema_version`。
- [ ] **F0-AT-02 Attention Top Themes 读取**：Julia 可读取 Attention Top Themes；结果中每个 `ThemeView` 至少包含 `theme_id/name/attention_level/evidence_refs`。
- [ ] **F0-AT-03 弱转强候选池读取**：Julia 可读取 W2S candidates；每个 `CandidateView` 至少包含 `stock_code/stock_name/strategy_id/evidence_refs`。
- [ ] **F0-AT-04 事件驱动证据读取**：Julia 可通过 `get_evidence` 或 `get_evidence_for_object` 获取事件驱动证据；返回 `EvidenceBundle` 可追溯到 `EvidenceRef`。
- [ ] **F0-AT-05 M7 风险状态读取**：Julia 可读取 `RiskStateView`，其中包含风险等级、风险标记与证据引用。
- [ ] **F0-AT-06 EvidenceRef 覆盖**：Julia F0 产生的每条分析性结论、候选摘要或案例字段均携带至少一个 `EvidenceRef`；测试中不得出现 unsupported claim。
- [ ] **F0-AT-07 禁止业务表直连**：Julia 侧实现不出现数据库连接、ORM session、SQL 字符串或 ai_theme_app 业务表访问。
- [ ] **F0-AT-08 禁止内部模块 import**：`julia_agent/runtime/capability/financial/client/ai_theme_client.py` 不 import `ai_theme_app` 的非 gateway API 内部模块；允许的依赖边界仅为协议/HTTP/fixture 或 `analyst_gateway.api` 公共 API 适配。
- [ ] **F0-AT-09 不产生正式交易决策**：F0 输出不得包含 `buy/sell/position/order/正式推荐/交易建议` 等正式决策对象；只能输出观察、证据、假设与风险状态。
- [ ] **F0-AT-10 可冻结可回放**：同一 fixture/snapshot 输入重复调用得到等价的 frozen dataclass 结果；结果包含 `source_snapshot_ids`、`producer_versions`、`schema_version`。
- [ ] **F0-AT-11 Provider 契约一致**：Provider 切换不改变 Julia 金融 Contract 的字段结构、EvidenceRef 要求与只读边界；F0 测试使用 deterministic/local fixture 验证。

## 4. Acceptance ↔ Test Mapping

| TC-ID | Acceptance | Required Test / Expected Result |
|---|---|---|
| F0-TC-01 | F0-AT-01 | `test_market_brief_contract_reads_daily_market_state`：返回 `FinancialBriefingBundle` 且 `trade_date` 匹配。 |
| F0-TC-02 | F0-AT-02 | `test_attention_top_themes_have_evidence_refs`：Top Themes 非空且每项有 EvidenceRef。 |
| F0-TC-03 | F0-AT-03 | `test_w2s_candidates_have_strategy_and_evidence`：W2S 候选非空且字段完整。 |
| F0-TC-04 | F0-AT-04 | `test_event_evidence_bundle_is_traceable`：EvidenceBundle 可由 ref 查询且包含 source metadata。 |
| F0-TC-05 | F0-AT-05 | `test_risk_state_view_exposes_m7_risk`：RiskStateView 包含 level/flags/evidence_refs。 |
| F0-TC-06 | F0-AT-06 | `test_all_conclusions_require_evidence_ref`：候选、题材、风险与 brief 结论无空 EvidenceRef。 |
| F0-TC-07 | F0-AT-07 | `test_financial_client_has_no_database_access`：AST/文本扫描禁止 sqlite/postgres/sqlalchemy/psycopg/sql。 |
| F0-TC-08 | F0-AT-08 | `test_financial_client_import_boundary`：AST 扫描禁止 import `ai_theme_app.*` 内部模块。 |
| F0-TC-09 | F0-AT-09 | `test_f0_outputs_no_formal_trade_decision`：Contract 中无正式交易决策/订单对象。 |
| F0-TC-10 | F0-AT-10 | `test_market_brief_is_frozen_and_replayable`：dataclass frozen，重复 fixture 输出等价。 |
| F0-TC-11 | F0-AT-11 | `test_provider_switch_keeps_contract_shape`：local/deterministic provider 输出 schema 一致。 |

## 5. Required Commands

必须从 `julia_agent` 仓库根目录执行：

```bash
.venv/bin/python -m pytest -q tests/test_financial_f0_contract.py
.venv/bin/python -m pytest -q tests/test_financial_f0_contract.py --maxfail=1
.venv/bin/python -m py_compile runtime/capability/financial/client/ai_theme_client.py
```

若仓库已配置 ruff/mypy，则作为附加门禁执行：

```bash
.venv/bin/python -m ruff check runtime/capability/financial tests/test_financial_f0_contract.py
.venv/bin/python -m mypy runtime/capability/financial
```

## 6. Deliverables

### 6.1 ai_theme_app 侧

- `Desktop/ai_theme_app/ai_theme_app/analyst_gateway/contracts/`
  - frozen dataclass / TypedDict 契约定义：`EvidenceRef`、`EvidenceBundle`、`MarketStateView`、`RiskStateView`、`ThemeView`、`CandidateView`、`EventView`、`HypothesisView`、`FinancialBriefingBundle`、`InvestmentCase`、`Scenario`。
  - 验证方式：目录存在；类型可 import；dataclass 均为 `frozen=True, slots=True`。
- `Desktop/ai_theme_app/ai_theme_app/analyst_gateway/api/analyst_api.py`
  - 第一批只读 API：market brief、market thesis、attention radar、risk state、theme/stock analysis、candidate watchlist、W2S、evidence、history/events。
  - 验证方式：测试 fixture 调用成功；无写入 API；无数据库直连暴露给 Julia。

### 6.2 julia_agent 侧

- `runtime/capability/financial/contracts/`
  - Julia 侧类型镜像；字段与 gateway 输出稳定对齐；保留 EvidenceRef、snapshot、schema metadata。
  - 验证方式：contract import 成功；schema/version 字段存在；tuple/frozen 结构不可变。
- `runtime/capability/financial/client/ai_theme_client.py`
  - 只读客户端；只依赖公共 gateway API/HTTP/fixture adapter；不 import ai_theme_app 内部业务模块；不连接数据库。
  - 验证方式：AST import boundary 测试通过；数据库禁用扫描通过。
- `tests/test_financial_f0_contract.py`
  - F0 验收测试；必须先写，覆盖 F0-AT-01 至 F0-AT-11。
  - 验证方式：`.venv/bin/python -m pytest -q tests/test_financial_f0_contract.py` 通过。

### 6.3 最小 fixture

- `tests/fixtures/financial_f0/market_brief_YYYYMMDD.json`
  - 包含市场状态、Attention Top Themes、W2S candidates、事件证据、M7 risk、source snapshot、producer versions。
  - 验证方式：测试只读加载，重复执行稳定。

## 7. Interface Contract

### 7.1 Gateway API — F0 只读最小集

```python
from datetime import date

get_market_brief(trade_date: date, context_type: str) -> FinancialBriefingBundle
get_attention_radar(trade_date: date) -> AttentionView
get_risk_state(trade_date: date) -> RiskStateView
get_w2s_candidates(trade_date: date) -> tuple[CandidateView, ...]
get_evidence(evidence_ref: str) -> EvidenceBundle
get_evidence_for_object(object_type: str, object_id: str, trade_date: date) -> tuple[EvidenceBundle, ...]
```

### 7.2 Mandatory Type Rules

- 所有 Contract 类型：`@dataclass(frozen=True, slots=True)`。
- Collection 字段使用 `tuple[...]` / `Tuple[...]`，避免可变 list。
- 每个支持性结论字段必须可追溯到 `EvidenceRef` 或 `evidence_refs`。
- `InvestmentCase` 在 F0 只允许 `draft` / `shadow` 状态，不允许 `approved` 或正式交易语义。
- `FinancialBriefingBundle` 必须包含：`bundle_id`、`trade_date`、`as_of`、`context_type`、`market_state`、`attention`、`top_themes`、`candidates`、`news_drivers`、`risk_state`、`active_hypotheses`、`source_snapshot_ids`、`producer_versions`、`module_coverage`、`evidence_refs`、`schema_version`。

### 7.3 Julia Client Boundary

- Julia client 调用：`AIThemeFinancialClient.get_market_brief(...)` 等只读方法。
- Julia client 不持有 DB connection / ORM / table name。
- Julia client 不 import ai_theme_app 内部计算模块；仅允许公共 API boundary 或 fixture/local gateway adapter。
- F0 所有输出均标记为 shadow / briefing / hypothesis，不升级为 decision。

## 8. Implementation Task Breakdown

### F0.1 Test Scaffold First

- 路径：`tests/test_financial_f0_contract.py`
- 动作：先创建失败测试，覆盖 11 个 Acceptance Targets。
- 验收：测试初始失败原因是模块缺失或 contract 缺失，而不是语法错误。

### F0.2 Gateway Contract Types

- 路径：`Desktop/ai_theme_app/ai_theme_app/analyst_gateway/contracts/`
- 动作：实现 frozen dataclass 类型与 `__init__.py` 导出。
- 验收：Julia 侧 fixture 可以序列化/反序列化同字段对象。

### F0.3 Gateway Read-Only API

- 路径：`Desktop/ai_theme_app/ai_theme_app/analyst_gateway/api/analyst_api.py`
- 动作：实现 F0 只读函数；初期允许 fixture/local adapter 返回标准对象。
- 验收：无写入函数；无交易决策函数；无直接业务表暴露。

### F0.4 Julia Financial Contract Mirror

- 路径：`runtime/capability/financial/contracts/`
- 动作：实现 Julia 侧镜像 dataclass；保持 schema 字段和 EvidenceRef 字段。
- 验收：所有 dataclass frozen/slots；tuple 字段不可变。

### F0.5 Julia AI Theme Client

- 路径：`runtime/capability/financial/client/ai_theme_client.py`
- 动作：实现只读 client；支持 local fixture/deterministic adapter；不直连数据库。
- 验收：import boundary 测试通过；`get_market_brief` 可返回 `FinancialBriefingBundle`。

### F0.6 F0 Contract Validation

- 路径：`tests/test_financial_f0_contract.py`
- 动作：补齐验收测试与 fixture。
- 验收：Required Commands 全部通过；输出可冻结可回放。

## 9. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---|---:|---|---|---|
| Julia 侧误 import ai_theme_app 内部模块 | 破坏认知隔离与仓库边界 | Medium | AST 扫描出现 `ai_theme_app.*` 非 gateway import | Codex | 用 client protocol / local fixture adapter；测试禁止内部 import。 |
| Contract 字段两侧漂移 | Provider/仓库切换后结果不可回放 | Medium | Julia mirror 与 gateway dataclass 字段不一致 | Codex | 固定 schema_version；字段对齐测试；只允许显式版本升级。 |
| EvidenceRef 覆盖不足 | 产生不可证伪结论 | High | 候选/题材/风险字段 evidence_refs 为空 | Codex | 测试强制每条结论 EvidenceRef 非空。 |
| F0 范围膨胀到写入或交易建议 | 破坏 Shadow Analyst 原则 | Medium | 出现 submit/approve/buy/sell/order 等接口 | Codex | Non-Goals + 文本/AST 扫描 + review gate。 |
| ai_theme_app 真实数据依赖阻塞测试 | F0 不可复现 | Medium | 测试依赖真实 DB 或当天行情 | Codex | 使用 frozen fixture/snapshot；真实接入延后。 |
| 缺失统一 guardrail 文件 | 状态同步和阶段对账不完整 | Low | `docs/project_control/EXECUTION_GUARDRAILS.md` 不存在 | Owner | 在执行前创建/确认该 guardrail，或在 dev-orchestrator 输入中内联本合同第 12 节。 |

## 10. Rollback Plan

### 10.1 代码回滚

- 触发条件：Required Commands 任一失败且 1 次最小修复后仍失败；或 import boundary / DB boundary 被破坏。
- 回滚方式：仅回滚 F0 新增路径：
  - `runtime/capability/financial/`
  - `tests/test_financial_f0_contract.py`
  - `tests/fixtures/financial_f0/`
  - `Desktop/ai_theme_app/ai_theme_app/analyst_gateway/`
- 兼容性说明：F0 为新增桥接层，不应修改既有 Julia runtime 行为。

### 10.2 数据回滚

- 触发条件：fixture/schema 误写入真实业务数据目录或污染现有 Memory OS。
- 回滚方式：删除或恢复 F0 fixture 文件；不得修改真实金融数据库；不得写入 Julia Memory OS 正式区。
- 数据恢复策略：F0 只读，无正式数据迁移；保留测试 fixture 即可。

### 10.3 同步补偿回滚

- 触发条件：项目状态已推进到 In review/done，但测试证据缺失或失败。
- 回滚方式：将状态退回 Doing，并附失败命令与失败日志；重新执行 Required Commands 后再推进。
- 对账口径：阶段末必须按 milestone 全量拉取后本地筛 F0，不得仅用 task-prefix + status 判断完成度。

## 11. Non-Goals

- 不实现 F1 完整《Julia 盘前研究》报告渲染。
- 不实现 F2 收盘冻结、真实行情验证、Error Attribution。
- 不实现 F3 审核写入、OverrideLog、Investor Profile 更新。
- 不实现 F4 语音播报。
- 不执行 F5 20 个真实交易日 Shadow Validation。
- 不连接 ai_theme_app 真实数据库。
- 不新增或修改策略参数、World Model、M7 Risk Gate。
- 不让 Provider 输出自动进入金融知识库或 Julia Memory OS。
- 不生成正式交易建议、订单、仓位指令或自动交易动作。

## 12. State Sync / Reconciliation Baseline

- 实时状态同步顺序：`Doing -> test-evidence -> In review/done -> milestone progress`。
- P0/P1 状态门禁：写入 `In review/done` 时必须传 `--test-files`；`--test-files` 必须在当前 `git diff` 中可见。
- 阶段末对账口径：必须用 `--milestone-id` 全量拉取后本地筛 phase；不得仅用 `--task-prefix + --status` 判断完成度。

## 13. Conflict Resolution

| Conflict Item | Adopted Source | Dropped Source | Reason |
|---|---|---|---|
| 用户消息将金融 v1.0 内容归属到 `Julia_Agent_Frontier_Assessment_v0.1.md`；实际金融 Implementation Contract 位于 `Julia_Financial_Analyst_Integration_Design_v1.0.md` | `docs/Julia_Financial_Analyst_Integration_Design_v1.0.md` | 文件名归属描述 | 实际 grep 与全文读取确认 F0、analyst_gateway、FinancialBriefingBundle、InvestmentCase 均在金融 v1.0 文档中。 |
| F0 交付物是否包含 `premarket.py` | F0 章节交付物包含最小盘前流程；Codex 第一优先级列表未包含 | 暂不列入第一批 5 个强制实现路径 | 用户明确冻结第一批实现顺序为 5 项；F0 Contract 将 `premarket.py` 延后为 F1 或 F0 后续可选，不纳入本批门禁。 |

## 14. Contract Self-Check

- [x] 阶段标识完整。
- [x] Acceptance 条款均为二元可判断。
- [x] Required Commands 可复制执行且无破坏性命令。
- [x] Deliverables 均映射到路径。
- [x] Risk / Rollback / Non-Goals 完整。
- [x] 输出 `.md + .json` 双格式。
- [x] 冲突裁决记录已填写。
- [x] 已引用 `docs/project_control/EXECUTION_GUARDRAILS.md`。
- [x] 已生成一致性报告：`tmp/phase_contract_consistency_F0.json`。
- [x] Acceptance 与 Contract 条款非空。
