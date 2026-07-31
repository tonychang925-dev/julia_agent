# Phase F2 — Market Feedback & Analyst Review Layer / Close Validation Report

## 1. 目标与范围

本阶段基于 `docs/project_control/PHASE_CONTRACT_F2.md` 与 F2 `APPROVED WITH NOTES` 执行 test-first implementation，让 Julia Financial Analyst 从“生成 shadow 研究报告”进入“评价 shadow 研究报告”的 Analyst Feedback Loop。

核心链路：

```text
PremarketResearchReport
        ↓
MarketTruthSnapshot
        ↓
InvestmentCaseEvaluation
        ↓
ErrorAttribution
        ↓
CloseValidationSummary
```

范围内：

- 记录 F2 Contract approval notes。
- 新增 F2 failing acceptance tests。
- 新增 F2 truth/evaluation contracts。
- 新增 deterministic close validation workflow。
- 验证 F1 report 不被修改、NOT_TRIGGERED/FALSIFIED 区分、Error Attribution、Accuracy metrics、EvidenceRef 全覆盖、Replay identity 保留。

范围外：

- 不连接真实市场数据库。
- 不由 LLM 生成 Market Truth。
- 不写入正式 Memory 或金融知识库。
- 不修改策略参数、World Model、M7 Risk Gate。
- 不产生正式交易建议、订单或仓位指令。

## 2. 变更文件清单

| 文件路径 | 变更类型 | 说明 |
|---|---|---|
| `docs/project_control/PHASE_CONTRACT_F2.md` | 新增/修改 | F2 Contract 与 approval notes。 |
| `tests/test_financial_f2_close_validation.py` | 新增 | F2 验收测试，覆盖 12 个 Acceptance Targets。 |
| `runtime/capability/financial/contracts/__init__.py` | 修改 | 新增 `CandidateTruth`、`MarketTruthSnapshot`、`ErrorAttribution`、`InvestmentCaseEvaluation`、`CloseValidationSummary`、`CloseValidationResult`。 |
| `runtime/capability/financial/workflows/close_review.py` | 新增 | deterministic F2 close validation workflow。 |

## 3. 验证命令与结果

| 命令 | 结果 |
|---|---|
| `.venv/bin/python -m pytest -q tests/test_financial_f2_close_validation.py` | PASS — 12 passed |
| `.venv/bin/python -m pytest -q tests/test_financial_f0_contract.py tests/test_financial_f1_premarket.py tests/test_financial_f2_close_validation.py` | PASS — 37 passed |
| `.venv/bin/python -m py_compile runtime/capability/financial/workflows/close_review.py` | PASS — exit 0 |

附加核查：

- F2 test-first 顺序满足：`9ccf561 Add F2 close validation acceptance tests` 先于实现 commit `510fc87`。
- F1 report 保持 frozen，不被 F2 修改。
- `NOT_TRIGGERED` 与 `FALSIFIED` 已有显式测试区分。
- `ErrorAttribution` 结构化包含 category、dimensions、explanation、EvidenceRef。
- `CloseValidationResult.evaluator_version="deterministic_f2_v1"`。
- Accuracy metrics 从 evaluations 推导，保留 per-case evaluation。

## 4. 风险与限制

| 风险/限制 | 当前处理 |
|---|---|
| F2 truth snapshot 仍为测试 fixture | 符合 F2 notes；真实 truth producer 应作为 `F2.5 Market Truth Adapter Spike`。 |
| Error Attribution 可能被未来误写入 Memory | 当前仅输出 shadow artifact；未实现任何 memory write。 |
| Accuracy metrics 规则未来会变化 | 已增加 `evaluator_version`，并保留 case evaluations 以便重算。 |
| F2 可能被误解为学习系统 | 当前不学习、不写 memory、不改策略；F5 才进入 Shadow Learning。 |

## 5. 对账结论

- Branch: `codex/f2/market-feedback-analyst-review`
- Base: `phase-f1-complete` / `main@1dab09d`
- Gate status: READY FOR REVIEW
- Changed files limited to F2 contract, F2 tests, F2 financial contracts/workflow, and F2 report.

## 6. Review Checklist

### 功能完整性

- [x] MarketTruthSnapshot contract 已实现。
- [x] InvestmentCaseEvaluation 已实现。
- [x] ErrorAttribution 已实现。
- [x] CloseValidationSummary 已实现。
- [x] CloseValidationResult 已实现。
- [x] NOT_TRIGGERED / FALSIFIED 区分已测试。

### 质量门禁

- [x] F2 pytest 通过。
- [x] F0+F1+F2 回归通过。
- [x] py_compile 通过。
- [x] 测试先行提交顺序满足。

### 架构合规

- [x] 不修改 F1 原报告。
- [x] 不连接真实数据库。
- [x] 不由 LLM 生成 truth。
- [x] 不触发交易。
- [x] 不修改策略/World Model/M7 Risk Gate。
- [x] 不写正式 Memory。

### 待验收

请用户选择：`ACCEPT` / `REWORK` / `REQUEST CHANGES` / `APPROVED WITH NOTES`。

## 7. Approval Decision — APPROVED WITH NOTES

Decision: `APPROVED WITH NOTES`

Approval rationale:

- F2 成功引入 Analyst Feedback Loop：`Research -> Truth -> Evaluation -> Error Attribution -> Summary`。
- F2 保持 shadow-only、read/evaluate-only，不交易、不改策略、不写正式 Memory。
- F0/F1/F2 回归通过，证明 Contract Boundary、Report Layer、Evaluation Layer 兼容。
- `NOT_TRIGGERED` / `FALSIFIED` 区分已实现，避免将“上涨=正确、下跌=错误”作为低级评价规则。
- `evaluator_version="deterministic_f2_v1"` 已建立评价逻辑版本化基础。

Merge Notes:

1. **Error Attribution 继续保持结构化**：必须保留 `category`、`dimensions`、`explanation`、`evidence_refs`，不得退化为简单自然语言“判断错误”。
2. **CloseValidationSummary 不应只存最终分数**：必须保留 `evaluations -> metric calculator -> accuracy` 的可重算链路，避免未来指标公式变化导致历史不可解释。
3. **F2 仍然禁止进入 Learning Layer**：F2 是 Evaluation Layer，不提前写入 Analyst Performance Memory，不训练模型，不更新策略。
4. **MarketTruthSnapshot 后续需要独立 Producer**：真实接入应走 `MarketTruthProducer -> MarketTruthSnapshot -> F2 Validator`，不得让 F2 自己查询行情或数据库。
5. **F2 已具备 F5 输入形态**：Research + Truth + Evaluation + Error 将成为 F5 20-day Shadow Validation 与 Analyst Performance Model 的输入基础。

Recommended next phase:

- **F3 — Tony Review & Analyst Override Layer**
- Objective: 在 F2 close validation 后引入 Tony Review 与 OverrideLog，让 Tony 能纠正 Julia 的评价、补充人类判断，并形成受治理的 analyst feedback artifact。
- Core flow: `CloseValidationResult -> Tony Review -> OverrideLog -> Analyst Preference Update Proposal`。
