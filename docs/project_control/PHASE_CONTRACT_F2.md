# Phase Execution Contract — F2 Market Feedback & Analyst Review Layer / Close Validation

## 1. Phase Identity

- **Phase Name**: Market Feedback & Analyst Review Layer / Close Validation
- **Phase Code**: F2
- **Parent Milestone**: Julia Financial Analyst Integration / Shadow Analyst Foundation
- **Risk Level**: High
- **Baseline Dependency**: F1 complete at `phase-f1-complete` / `1dab09d`
- **Source Documents**:
  - `docs/Julia_Financial_Analyst_Integration_Design_v1.0.md` — FROZEN Implementation Contract, Phase F2
  - `docs/project_control/PHASE_CONTRACT_F1.md` — F1 report object and replay baseline
  - `docs/project_control/reports/phase-F1-market-intelligence-read-layer.md` — F1 APPROVED WITH NOTES
  - `docs/project_control/EXECUTION_GUARDRAILS.md` — referenced guardrail baseline; file still pending in repo

## 2. Phase Objective

在 F2 阶段内，基于 F1 的 `PremarketResearchReport`、`InvestmentCase`、`input_hash`、`source_snapshot_ids` 与 EvidenceRef 链路，建立收盘后 Close Validation / Market Feedback 流程：冻结盘前案例，对比 Market Truth Snapshot，判定每个案例的验证状态，生成 Error Attribution，并统计 Thesis Accuracy、Trigger Accuracy、Risk Accuracy；全阶段仍保持 Shadow Analyst，不产生正式交易决策、不修改策略、不写入正式金融知识库。

## 3. Acceptance Targets

- [ ] **F2-AT-01 盘前报告冻结**：F2 输入的 `PremarketResearchReport` 在 close validation 中必须保持不可变；输出不得修改原报告或原 `InvestmentCase`。
- [ ] **F2-AT-02 Market Truth Snapshot**：F2 必须定义 frozen `MarketTruthSnapshot`，包含真实收盘状态、候选真实结果、风险真实状态、source snapshot identity 与 EvidenceRef。
- [ ] **F2-AT-03 案例状态判定**：每个 F1 `InvestmentCase` 必须生成一个 `InvestmentCaseEvaluation`，状态限定为 `CONFIRMED/PARTIALLY_CONFIRMED/FALSIFIED/NOT_TRIGGERED/EXPIRED/INVALIDATED_BY_RISK/INSUFFICIENT_DATA`。
- [ ] **F2-AT-04 区分未触发与触发亏损**：测试必须覆盖并区分“涨了但入场条件未出现”=`NOT_TRIGGERED` 与“入场条件出现但结果不利”=`FALSIFIED`。
- [ ] **F2-AT-05 Error Attribution**：每个非完全确认案例必须生成 `ErrorAttribution`，包含原因类别、解释、EvidenceRef。
- [ ] **F2-AT-06 指标统计**：F2 必须输出 `CloseValidationSummary`，包含 `thesis_accuracy`、`trigger_accuracy`、`risk_accuracy`。
- [ ] **F2-AT-07 EvidenceRef 全覆盖**：Market Truth、Evaluation、Error Attribution、Summary 均必须携带 EvidenceRef。
- [ ] **F2-AT-08 Replay Identity 保留**：输出必须保留 F1 `input_hash`、`source_bundle_id`、`source_snapshot_ids`，并增加 truth snapshot identity。
- [ ] **F2-AT-09 不触发交易**：F2 不创建订单、不调用交易接口、不产生正式 buy/sell/position 指令。
- [ ] **F2-AT-10 不修改策略或记忆**：F2 不修改策略参数、World Model、M7 Risk Gate，不写入正式 Memory/Knowledge Base；仅生成 shadow evaluation artifact。
- [ ] **F2-AT-11 可冻结可回放**：同一 F1 report + 同一 truth snapshot 重复验证输出等价。
- [ ] **F2-AT-12 F0/F1 回归兼容**：F2 新增类型与流程不得破坏 F0/F1 既有测试。

## 4. Acceptance ↔ Test Mapping

| TC-ID | Acceptance | Required Test / Expected Result |
|---|---|---|
| F2-TC-01 | F2-AT-01 | `test_close_validation_does_not_mutate_premarket_report`：原 report 与 case 保持 frozen/equal。 |
| F2-TC-02 | F2-AT-02 | `test_market_truth_snapshot_contract_is_frozen_and_evidence_backed`：truth snapshot frozen 且证据非空。 |
| F2-TC-03 | F2-AT-03 | `test_each_investment_case_gets_valid_evaluation_status`：每个 case 有合法 evaluation status。 |
| F2-TC-04 | F2-AT-04 | `test_close_validation_distinguishes_not_triggered_from_falsified`：覆盖 NOT_TRIGGERED vs FALSIFIED。 |
| F2-TC-05 | F2-AT-05 | `test_error_attribution_required_for_non_confirmed_cases`：非 confirmed case 有 attribution。 |
| F2-TC-06 | F2-AT-06 | `test_close_validation_summary_metrics_are_reported`：三项 accuracy 指标存在且 0..1。 |
| F2-TC-07 | F2-AT-07 | `test_close_validation_outputs_have_evidence_refs`：truth/evaluation/attribution/summary 证据非空。 |
| F2-TC-08 | F2-AT-08 | `test_close_validation_preserves_replay_identity`：保留 F1 input_hash/source ids 与 truth snapshot id。 |
| F2-TC-09 | F2-AT-09 | `test_f2_does_not_emit_trade_decisions_or_orders`：输出无交易动作词。 |
| F2-TC-10 | F2-AT-10 | `test_f2_does_not_modify_strategy_memory_or_world_model`：AST/文本审计无写入。 |
| F2-TC-11 | F2-AT-11 | `test_close_validation_is_replayable_from_same_inputs`：重复验证输出等价。 |
| F2-TC-12 | F2-AT-12 | `test_f0_f1_f2_regression_suite_passes`：Required regression command 通过。 |

## 5. Required Commands

必须从 `julia_agent` 仓库根目录执行：

```bash
.venv/bin/python -m pytest -q tests/test_financial_f2_close_validation.py
.venv/bin/python -m pytest -q tests/test_financial_f0_contract.py tests/test_financial_f1_premarket.py tests/test_financial_f2_close_validation.py
.venv/bin/python -m py_compile runtime/capability/financial/workflows/close_review.py
```

若仓库已配置 ruff/mypy，则作为附加门禁执行：

```bash
.venv/bin/python -m ruff check runtime/capability/financial tests/test_financial_f2_close_validation.py
.venv/bin/python -m mypy runtime/capability/financial
```

## 6. Deliverables

- `runtime/capability/financial/workflows/close_review.py`
  - Close validation workflow；输入 `PremarketResearchReport` 与 `MarketTruthSnapshot`，输出 `CloseValidationResult`。
  - 验证方式：F2 pytest 通过；可回放；不修改输入对象。
- `runtime/capability/financial/contracts/`
  - 新增 `MarketTruthSnapshot`、`CandidateTruth`、`InvestmentCaseEvaluation`、`ErrorAttribution`、`CloseValidationSummary`、`CloseValidationResult` 或等价 frozen dataclass。
  - 验证方式：所有新增 contract frozen/slots；EvidenceRef 字段存在。
- `tests/test_financial_f2_close_validation.py`
  - F2 验收测试，覆盖 F2-AT-01 至 F2-AT-12。
  - 验证方式：Required Commands 通过。
- `tests/fixtures/financial_f2/`
  - 若需要，新增冻结 truth snapshot fixture；不得依赖真实当天行情或真实数据库。
  - 验证方式：fixture 可公开提交，不含密钥/私人信息。

## 7. Interface Contract

### 7.1 F2 Workflow API

```python
run_close_validation(
    report: PremarketResearchReport,
    truth: MarketTruthSnapshot,
    *,
    generated_by: str = "julia_financial_shadow",
    model_version: str = "deterministic_f2",
) -> CloseValidationResult
```

### 7.2 Required Status Enum

```text
CONFIRMED
PARTIALLY_CONFIRMED
FALSIFIED
NOT_TRIGGERED
EXPIRED
INVALIDATED_BY_RISK
INSUFFICIENT_DATA
```

### 7.3 Required Distinction

- `NOT_TRIGGERED`: 观察对象结果可能上涨，但 F1 入场条件未出现或未能验证。
- `FALSIFIED`: F1 入场/确认条件出现，但后续真实结果与 thesis 不一致或结果不利。

### 7.4 Output Contract Requirements

- `CloseValidationResult` 必须为 frozen dataclass。
- 必须保留：
  - `premarket_report_id`
  - `premarket_input_hash`
  - `source_bundle_id`
  - `source_snapshot_ids`
  - `truth_snapshot_id`
  - `evaluations`
  - `summary`
  - `evidence_refs`
  - `status="shadow"`
  - `schema_version`

## 8. Implementation Task Breakdown

### F2.1 Test First

- 路径：`tests/test_financial_f2_close_validation.py`
- 动作：先创建失败测试，覆盖 12 个 Acceptance Targets。
- 验收：测试初始失败原因是缺少 F2 close validation contract/workflow，而不是语法错误。

### F2.2 F2 Evaluation Contracts

- 路径：`runtime/capability/financial/contracts/`
- 动作：新增 truth/evaluation/attribution/summary/result frozen dataclass。
- 验收：F0/F1 测试仍通过。

### F2.3 Close Validation Workflow

- 路径：`runtime/capability/financial/workflows/close_review.py`
- 动作：实现 deterministic validation；不修改输入 report；生成 per-case evaluation 与 summary。
- 验收：F2 Required Commands 通过。

### F2.4 Boundary Audit

- 路径：`tests/test_financial_f2_close_validation.py`
- 动作：AST/文本扫描确保无交易接口、策略修改、Memory 正式写入、数据库直连。
- 验收：无 forbidden token/import。

## 9. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---|---:|---|---|---|
| F2 evaluation 被误认为策略优化 | 高 | Medium | 输出包含策略修改或交易建议 | Codex | status=shadow；测试禁止交易/策略写入。 |
| 未触发与触发亏损混淆 | 高 | Medium | NOT_TRIGGERED/FALSIFIED 无测试区分 | Codex | F2-TC-04 强制覆盖两类情形。 |
| F1 report 被修改导致 replay 失效 | 高 | Low | close validation 修改 report/cases | Codex | frozen dataclass + equality 测试。 |
| Truth snapshot 依赖真实数据库 | Medium | Medium | 测试读取真实行情/DB | Codex | 冻结 fixture；真实接入另设 F2.5/F1.5 spike。 |
| Error Attribution 无证据 | High | Medium | attribution 缺 EvidenceRef | Codex | F2-TC-05/F2-TC-07 强制非空证据。 |

## 10. Rollback Plan

### 10.1 代码回滚

- 触发条件：F0/F1 回归测试失败；F2 Required Commands 失败且最小修复后仍失败；shadow/只读边界破坏。
- 回滚方式：回滚 F2 新增路径：
  - `runtime/capability/financial/workflows/close_review.py`
  - F2 新增 contract 类型
  - `tests/test_financial_f2_close_validation.py`
  - `tests/fixtures/financial_f2/`
- 兼容性说明：不得破坏 `phase-f1-complete` tag 对应 baseline。

### 10.2 数据回滚

- 触发条件：误写入 memory/data/正式知识库或策略配置。
- 回滚方式：删除误写入文件；恢复到 `phase-f1-complete`；不得迁移真实数据库。
- 数据恢复策略：F2 设计为 read/evaluate/shadow artifact，无正式数据迁移。

### 10.3 同步补偿回滚

- 触发条件：阶段状态已推进但测试证据缺失或失败。
- 回滚方式：状态退回 Doing，附失败命令、日志、变更文件清单；重新执行 Required Commands 后再推进。

## 11. Non-Goals

- 不实现 F3 Tony 审核写入、OverrideLog、Investor Profile 更新。
- 不实现 F4 语音播报。
- 不执行 F5 20 个真实交易日 Shadow Validation。
- 不连接真实市场数据库。
- 不修改策略参数、World Model、M7 Risk Gate。
- 不让 evaluation 自动进入正式 Memory 或金融知识库。
- 不生成正式交易建议、订单、仓位指令或自动交易动作。
- 不重写 F1 `PremarketResearchReport` 对象设计。

## 12. State Sync / Reconciliation Baseline

- 实时状态同步顺序：`Doing -> test-evidence -> In review/done -> milestone progress`。
- P0/P1 状态门禁：写入 `In review/done` 时必须传 `--test-files`；`--test-files` 必须在当前 `git diff` 中可见。
- 阶段末对账口径：必须用 `--milestone-id` 全量拉取后本地筛 phase；不得仅用 `--task-prefix + --status` 判断完成度。

## 13. Conflict Resolution

| Conflict Item | Adopted Source | Dropped Source | Reason |
|---|---|---|---|
| 源文档命名 F2 — Close Validation；用户建议 F2 — Market Feedback & Analyst Review Layer | 合并命名：`Market Feedback & Analyst Review Layer / Close Validation` | 单一命名 | 用户命名强调反馈评价层，源文档强调收盘验证；二者语义一致。 |
| F2 是否写入 memory/analyst performance | F2 仅生成 shadow evaluation artifact | 自动写入正式 Memory | F1/F2 notes 明确 Provider/Julia 输出不得自动入正式记忆；memory learning 后置。 |

## 14. Contract Self-Check

- [x] 阶段标识完整。
- [x] Acceptance 条款全部可二元判定。
- [x] Required Commands 可复制执行且无破坏性命令。
- [x] Deliverables 全部映射到路径。
- [x] Risk / Rollback / Non-Goals 完整。
- [x] 已继承 F1 APPROVED WITH NOTES 治理备注。
- [x] 已明确 F2 不产生正式交易决策、不写正式 Memory。
