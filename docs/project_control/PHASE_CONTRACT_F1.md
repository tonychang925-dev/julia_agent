# Phase Execution Contract — F1 Market Intelligence Read Layer / Shadow Morning Analyst

## 1. Phase Identity

- **Phase Name**: Market Intelligence Read Layer / Shadow Morning Analyst
- **Phase Code**: F1
- **Parent Milestone**: Julia Financial Analyst Integration / Shadow Analyst Foundation
- **Risk Level**: Medium-High
- **Baseline Dependency**: F0 complete at `phase-f0-complete` / `f5517a7`
- **Source Documents**:
  - `docs/Julia_Financial_Analyst_Integration_Design_v1.0.md` — FROZEN Implementation Contract, Phase F1
  - `docs/project_control/PHASE_CONTRACT_F0.md` — F0 boundary and EvidenceRef baseline
  - `docs/project_control/reports/phase-F0-financial-analyst-contract.md` — APPROVED WITH NOTES
  - `docs/project_control/EXECUTION_GUARDRAILS.md` — referenced guardrail baseline; file still pending in repo

## 2. Phase Objective

在 F1 阶段内，基于 F0 只读 Typed Contract，让 Julia 从“接口存在”进入“每日盘前观察市场”的 Shadow Morning Analyst 模式：Julia 能读取真实或冻结的 Market Intelligence 输入，生成《Julia 盘前研究》结构化报告，包含市场状态、重点题材、条件观察标的、风险项与 EvidenceRef；每个候选必须形成可证伪的 draft/shadow `InvestmentCase`，但不得输出正式推荐、不得触发交易、不得修改策略或写入正式金融记忆。

## 3. Acceptance Targets

- [ ] **F1-AT-01 每日盘前研究生成**：给定指定交易日 `FinancialBriefingBundle`，Julia 可生成一份《Julia 盘前研究》对象或 Markdown 报告，且包含 `trade_date`、`as_of`、`schema_version`。
- [ ] **F1-AT-02 市场状态覆盖**：报告必须包含市场状态摘要，且该摘要引用 `MarketStateView.evidence_refs`。
- [ ] **F1-AT-03 重点题材覆盖**：报告必须包含 Top 3-5 重点题材；每个题材保留 `theme_id/name/attention_level/lifecycle_stage/evidence_refs`。
- [ ] **F1-AT-04 条件观察标的覆盖**：报告必须包含条件观察标的列表；每个候选保留 `stock_code/stock_name/strategy_id/observation_level/evidence_refs`。
- [ ] **F1-AT-05 每个候选带 InvestmentCase**：每个候选必须生成 draft/shadow `InvestmentCase`，并包含入场条件、确认条件、失效条件、风险标记和 EvidenceRef。
- [ ] **F1-AT-06 A/B/C + 禁止级别**：候选观察级别只能是 `A/B/C/FORBIDDEN`；禁止级别不得进入可交易表达。
- [ ] **F1-AT-07 风险项覆盖**：报告必须包含 M7 Risk State 与禁止项；风险结论必须携带 EvidenceRef。
- [ ] **F1-AT-08 所有结论带 EvidenceRef**：市场、题材、候选、InvestmentCase、风险、集合竞价确认点均不得出现 unsupported claim。
- [ ] **F1-AT-09 不触发交易**：F1 不创建订单、不调用交易接口、不产生正式 buy/sell/position 指令。
- [ ] **F1-AT-10 不修改策略**：F1 不修改策略参数、World Model、M7 Risk Gate 或 ai_theme_app 业务配置。
- [ ] **F1-AT-11 Provider 输出不入正式记忆**：F1 生成内容仅为 shadow/draft；不得自动写入 Julia Memory OS 正式区或金融知识库。
- [ ] **F1-AT-12 可冻结可回放**：相同输入 snapshot 重复生成的盘前研究在 contract shape 与 EvidenceRef 链路上等价。

## 4. Acceptance ↔ Test Mapping

| TC-ID | Acceptance | Required Test / Expected Result |
|---|---|---|
| F1-TC-01 | F1-AT-01 | `test_premarket_workflow_generates_daily_research_briefing`：输出 `PremarketResearchReport` 或 Markdown，交易日匹配。 |
| F1-TC-02 | F1-AT-02 | `test_premarket_report_includes_market_state_with_evidence`：市场状态存在且 EvidenceRef 非空。 |
| F1-TC-03 | F1-AT-03 | `test_premarket_report_includes_top_themes_with_evidence`：Top themes 3-5 个或 fixture 可用上限，每项证据非空。 |
| F1-TC-04 | F1-AT-04 | `test_premarket_report_includes_conditional_watchlist`：候选列表字段完整。 |
| F1-TC-05 | F1-AT-05 | `test_each_candidate_has_falsifiable_investment_case`：每个 case 有 entry/confirmation/invalidation/risk/evidence。 |
| F1-TC-06 | F1-AT-06 | `test_observation_levels_are_governed`：级别集合限定为 A/B/C/FORBIDDEN。 |
| F1-TC-07 | F1-AT-07 | `test_premarket_report_includes_risk_and_forbidden_items`：风险与禁止项携带 EvidenceRef。 |
| F1-TC-08 | F1-AT-08 | `test_premarket_report_has_no_unsupported_claims`：所有 conclusion 节点 EvidenceRef 非空。 |
| F1-TC-09 | F1-AT-09 | `test_f1_does_not_emit_trade_decisions_or_orders`：输出中无订单/正式交易对象。 |
| F1-TC-10 | F1-AT-10 | `test_f1_does_not_modify_strategy_or_world_model`：AST/fixture 审计无写入策略配置。 |
| F1-TC-11 | F1-AT-11 | `test_f1_outputs_shadow_draft_only`：报告与 InvestmentCase 状态为 draft/shadow。 |
| F1-TC-12 | F1-AT-12 | `test_premarket_report_is_replayable_from_same_snapshot`：重复输入输出 contract shape 等价。 |

## 5. Required Commands

必须从 `julia_agent` 仓库根目录执行：

```bash
.venv/bin/python -m pytest -q tests/test_financial_f1_premarket.py
.venv/bin/python -m pytest -q tests/test_financial_f0_contract.py tests/test_financial_f1_premarket.py
.venv/bin/python -m py_compile runtime/capability/financial/workflows/premarket.py
.venv/bin/python -m py_compile runtime/capability/financial/rendering/report_renderer.py
```

若仓库已配置 ruff/mypy，则作为附加门禁执行：

```bash
.venv/bin/python -m ruff check runtime/capability/financial tests/test_financial_f1_premarket.py
.venv/bin/python -m mypy runtime/capability/financial
```

## 6. Deliverables

- `runtime/capability/financial/workflows/premarket.py`
  - 完整盘前研究 workflow；输入 `FinancialBriefingBundle`，输出结构化 `PremarketResearchReport`。
  - 验证方式：F1 pytest 通过；重复 fixture 输出可回放。
- `runtime/capability/financial/rendering/report_renderer.py`
  - 报告渲染器；将结构化报告渲染为《Julia 盘前研究》Markdown。
  - 验证方式：Markdown 包含市场状态、重点题材、条件观察、风险、集合竞价确认点与 EvidenceRef。
- `runtime/capability/financial/contracts/`
  - 在 F0 contract 基础上补充 F1 所需 `PremarketResearchReport`、`ReportSection`、`ConclusionWithEvidence` 或等价 frozen dataclass。
  - 验证方式：所有新增 contract frozen/slots；schema/version 字段存在。
- `tests/test_financial_f1_premarket.py`
  - F1 验收测试，覆盖 F1-AT-01 至 F1-AT-12。
  - 验证方式：Required Commands 通过。
- `tests/fixtures/financial_f1/`
  - 若需要，新增冻结盘前 fixture；不得依赖真实当天行情或真实数据库。
  - 验证方式：fixture 不含密钥/私人信息，可公开提交。

## 7. Interface Contract

### 7.1 F1 Workflow API

```python
run_premarket_research(
    bundle: FinancialBriefingBundle,
    *,
    generated_by: str = "julia_financial_shadow",
    model_version: str = "deterministic_f1",
) -> PremarketResearchReport
```

### 7.2 F1 Report Contract Requirements

- `PremarketResearchReport` 必须为 `@dataclass(frozen=True, slots=True)`。
- 必须包含：
  - `report_id`
  - `trade_date`
  - `as_of`
  - `market_summary`
  - `top_themes`
  - `conditional_watchlist`
  - `investment_cases`
  - `risk_items`
  - `auction_confirmation_points`
  - `evidence_refs`
  - `source_bundle_id`
  - `source_snapshot_ids`
  - `status`
  - `schema_version`
- `status` 只能是 `draft` 或 `shadow`。
- `InvestmentCase.status` 在 F1 只能是 `draft` 或 `shadow`。
- 每个 conclusion 节点必须含 EvidenceRef。

### 7.3 Rendering Contract

```python
render_premarket_report(report: PremarketResearchReport) -> str
```

Markdown 必须包含：

- 标题：《Julia 盘前研究》YYYY-MM-DD
- 市场状态
- 今日主要矛盾 / 市场假设
- 重点题材
- 条件观察标的
- 风险与禁止项
- 集合竞价确认点
- EvidenceRef 展示或脚注

## 8. Implementation Task Breakdown

### F1.1 Test First

- 路径：`tests/test_financial_f1_premarket.py`
- 动作：先创建失败测试，覆盖 12 个 Acceptance Targets。
- 验收：测试初始失败原因是缺少 F1 workflow/report contract，而不是语法错误。

### F1.2 F1 Report Contracts

- 路径：`runtime/capability/financial/contracts/`
- 动作：新增或扩展盘前报告 contract 类型；保留 F0 类型向后兼容。
- 验收：F0 测试仍通过；新增 contract frozen/slots。

### F1.3 Premarket Workflow

- 路径：`runtime/capability/financial/workflows/premarket.py`
- 动作：从 `FinancialBriefingBundle` 组装盘前研究报告；生成 draft/shadow InvestmentCase。
- 验收：每个候选有可证伪条件与 EvidenceRef；无交易动作。

### F1.4 Report Renderer

- 路径：`runtime/capability/financial/rendering/report_renderer.py`
- 动作：渲染 Markdown《Julia 盘前研究》；EvidenceRef 可见。
- 验收：报告结构符合五模式中的“盘前研究”。

### F1.5 Boundary Audit

- 路径：`tests/test_financial_f1_premarket.py`
- 动作：AST/文本扫描确保无交易接口、策略修改、Memory 正式写入、数据库直连。
- 验收：Required Commands 全部通过。

## 9. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---|---:|---|---|---|
| F1 输出被误认为正式推荐 | 高 | Medium | Markdown 出现 buy/sell/order/正式推荐 | Codex | 输出状态固定 shadow/draft；测试禁止正式交易语义。 |
| InvestmentCase 条件不可证伪 | 高 | Medium | 缺少 entry/confirmation/invalidation | Codex | F1-TC-05 强制每个 case 条件非空。 |
| EvidenceRef 链路断裂 | 高 | Medium | conclusion 缺证据 | Codex | F1-TC-08 全节点证据覆盖。 |
| 功能膨胀到 F2/F3/F4 | Medium | Medium | 出现收盘验证、审核写入、语音播报 | Codex | Non-Goals 明确阻断。 |
| 真实数据依赖导致测试不可复现 | Medium | Medium | 测试依赖当天行情/数据库 | Codex | 使用冻结 fixture；真实市场接入单独分支。 |
| Provider 输出进入正式记忆 | 高 | Low | F1 workflow 写入 memory/ 或 knowledge base | Codex | F1-TC-11 与 AST 审计禁止正式写入。 |

## 10. Rollback Plan

### 10.1 代码回滚

- 触发条件：F0 回归测试失败；F1 Required Commands 失败且最小修复后仍失败；只读/交易边界破坏。
- 回滚方式：回滚 F1 新增路径：
  - `runtime/capability/financial/workflows/premarket.py`
  - `runtime/capability/financial/rendering/report_renderer.py`
  - F1 新增 contract 类型
  - `tests/test_financial_f1_premarket.py`
  - `tests/fixtures/financial_f1/`
- 兼容性说明：不得回滚 F0 public baseline，除非 F1 修改破坏 F0 contract。

### 10.2 数据回滚

- 触发条件：F1 误写入 memory/data/tmp 以外正式区或污染金融知识库。
- 回滚方式：删除误写入文件；恢复到 F0 tag `phase-f0-complete`；不得迁移真实数据库。
- 数据恢复策略：F1 设计为 read/render/shadow，无正式数据迁移。

### 10.3 同步补偿回滚

- 触发条件：阶段状态已推进但测试证据缺失或失败。
- 回滚方式：状态退回 Doing，附失败命令、日志、变更文件清单；重新执行 Required Commands 后再推进。

## 11. Non-Goals

- 不实现 F2 收盘冻结、真实行情验证、Error Attribution。
- 不实现 F3 Tony 审核写入、OverrideLog、Investor Profile 更新。
- 不实现 F4 语音播报。
- 不执行 F5 20 个真实交易日 Shadow Validation。
- 不连接 ai_theme_app 真实数据库。
- 不修改策略参数、World Model、M7 Risk Gate。
- 不让 Provider 输出自动进入正式 Memory 或金融知识库。
- 不生成正式交易建议、订单、仓位指令或自动交易动作。
- 不迁移 `identity/` 真实内容、`memory/`、`data/`、`audio/`、legacy runtime 全量目录。

## 12. State Sync / Reconciliation Baseline

- 实时状态同步顺序：`Doing -> test-evidence -> In review/done -> milestone progress`。
- P0/P1 状态门禁：写入 `In review/done` 时必须传 `--test-files`；`--test-files` 必须在当前 `git diff` 中可见。
- 阶段末对账口径：必须用 `--milestone-id` 全量拉取后本地筛 phase；不得仅用 `--task-prefix + --status` 判断完成度。

## 13. Conflict Resolution

| Conflict Item | Adopted Source | Dropped Source | Reason |
|---|---|---|---|
| 用户建议将下一阶段命名为 F1 — Market Intelligence Read Layer；源文档命名为 F1 — Shadow Morning Analyst | 合并命名：`Market Intelligence Read Layer / Shadow Morning Analyst` | 单一命名 | 用户命名强调“真实市场读取层”，源文档强调“盘前研究输出”；两者语义互补且不冲突。 |
| F1 是否接入真实 ai_theme_app 数据库 | F0/F1 只读 gateway/fixture contract | 直接数据库接入 | F0 approval notes 明确保持 gateway 只读边界；真实数据库直连仍禁止。 |

## 14. Contract Self-Check

- [x] 阶段标识完整。
- [x] Acceptance 条款全部可二元判定。
- [x] Required Commands 可复制执行且无破坏性命令。
- [x] Deliverables 全部映射到路径。
- [x] Risk / Rollback / Non-Goals 完整。
- [x] 已引用 `docs/project_control/EXECUTION_GUARDRAILS.md`。
- [x] 已继承 F0 APPROVED WITH NOTES 治理备注。
- [x] 已明确 F1 不产生正式交易决策。

## 15. Approval Decision — APPROVED WITH NOTES

Decision: `APPROVED WITH NOTES`

Approval rationale:

- F1 正确从 F0 金融能力边界扩展到 Shadow Morning Analyst 工作流。
- F1 仍保持市场认知读取与研究报告生成层，不进入交易系统。
- F1 明确生成 `PremarketResearchReport` 与 Markdown《Julia 盘前研究》，但不产生正式推荐、不触发交易、不写入正式金融记忆。

Required Notes before/during implementation:

1. **F1 Workflow 必须保持 deterministic**：`run_premarket_research(bundle, generated_by="julia_financial_shadow", model_version="deterministic_f1")` 必须是 `Input Bundle -> Deterministic Transformation -> Research Report`，不得依赖在线 LLM、实时新闻搜索或随机采样。
2. **InvestmentCase 不允许出现交易动作词**：禁止 `buy/sell/open_position/close_position/order/execute`；允许 `observe/monitor/validate/confirm/invalidate`。
3. **Renderer 不应生成荐股语言**：禁止“今日推荐股票”等表达；允许“今日条件观察标的”。
4. **增加 Snapshot Identity**：F1 报告应在 `source_bundle_id`、`source_snapshot_ids` 基础上增加 `input_hash`，用于 replay、回测、错误归因和模型比较。
5. **F1 不连接真实市场**：F1 使用冻结 fixture，不依赖真实当天行情或真实数据库；真实接入应作为后续 `F1.5 Real Data Adapter Spike` 单独处理。

Implementation order:

1. `tests/test_financial_f1_premarket.py` — 12 个失败测试先行。
2. `PremarketResearchReport` / `ReportSection` / `ConclusionWithEvidence` contracts。
3. `runtime/capability/financial/workflows/premarket.py`。
4. `runtime/capability/financial/rendering/report_renderer.py`。
5. Boundary audit：无交易、无 memory 正式写入、无数据库、无策略修改。
