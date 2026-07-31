# Phase Execution Contract — F3 Tony Review & Analyst Override Layer

## 1. Phase Identity

- **Phase Name**: Tony Review & Analyst Override Layer
- **Phase Code**: F3
- **Parent Milestone**: Julia Financial Analyst Integration / Human Feedback Foundation
- **Risk Level**: High
- **Baseline Dependency**: F2 complete at `phase-f2-complete` / `7a0c8ef`
- **Source Documents**:
  - `docs/Julia_Financial_Analyst_Integration_Design_v1.0.md` — FROZEN Implementation Contract, Phase F3
  - `docs/project_control/PHASE_CONTRACT_F2.md` — Close Validation / Evaluation baseline
  - `docs/project_control/reports/phase-F2-market-feedback-analyst-review.md` — F2 APPROVED WITH NOTES
  - `docs/project_control/EXECUTION_GUARDRAILS.md` — referenced guardrail baseline; file still pending in repo

## 2. Phase Objective

在 F3 阶段内，基于 F2 的 `CloseValidationResult`，建立 Tony Review 与 Analyst Override 工作流：Tony 可以对 Julia 的 case evaluation 进行 `Approve / Modify / Reject / Need More Evidence` 审核，生成受治理的 `OverrideLog` 与 `AnalystReviewRecord`，并形成 `InvestorProfileUpdateProposal` 或 `AnalystPreferenceUpdateProposal`；全阶段仍保持治理门禁，不直接写正式 Memory、不自动修改策略、不触发交易、不绕过 human review。

## 3. Acceptance Targets

- [ ] **F3-AT-01 Review Action 支持**：F3 必须支持 `APPROVE/MODIFY/REJECT/NEED_MORE_EVIDENCE` 四类 Tony review action。
- [ ] **F3-AT-02 Review Record Contract**：F3 必须定义 frozen `AnalystReviewRecord`，引用 F2 `validation_id`、case/evaluation id、Tony action、reason、EvidenceRef。
- [ ] **F3-AT-03 OverrideLog 生成**：当 Tony action 为 `MODIFY` 或 `REJECT` 时，必须生成 `OverrideLog`，记录原 evaluation、Tony override、reason、EvidenceRef、reviewer identity。
- [ ] **F3-AT-04 Need More Evidence 请求**：当 action 为 `NEED_MORE_EVIDENCE` 时，必须生成 `TargetedEvidenceRequest` 或等价 research request proposal，状态为 `draft/shadow`。
- [ ] **F3-AT-05 Governance Gate 生效**：所有 review/override/profile proposal 必须通过 `FinancialReviewGovernanceDecision`，状态限定为 allow/review_required/reject。
- [ ] **F3-AT-06 Investor/Profile Update Proposal**：F3 只能生成 `InvestorProfileUpdateProposal` / `AnalystPreferenceUpdateProposal`，不得直接修改正式 profile 或 memory。
- [ ] **F3-AT-07 EvidenceRef 全覆盖**：ReviewRecord、OverrideLog、EvidenceRequest、ProfileUpdateProposal、GovernanceDecision 均必须携带 EvidenceRef 或 source ids。
- [ ] **F3-AT-08 F2 结果不可修改**：F3 不得修改 `CloseValidationResult`、`InvestmentCaseEvaluation` 或 F1 report，只能生成独立 review artifact。
- [ ] **F3-AT-09 不触发交易**：F3 不创建订单、不调用交易接口、不产生正式 buy/sell/position 指令。
- [ ] **F3-AT-10 不自动学习/写 Memory**：F3 不写入正式 Memory/Knowledge Base；所有学习相关输出均为 proposal。
- [ ] **F3-AT-11 可冻结可回放**：相同 validation result + review input 重复生成的 review artifact 等价。
- [ ] **F3-AT-12 F0/F1/F2 回归兼容**：F3 新增类型与流程不得破坏 F0/F1/F2 既有测试。

## 4. Acceptance ↔ Test Mapping

| TC-ID | Acceptance | Required Test / Expected Result |
|---|---|---|
| F3-TC-01 | F3-AT-01 | `test_review_workflow_supports_four_tony_actions`：四类 action 均可生成 review record。 |
| F3-TC-02 | F3-AT-02 | `test_analyst_review_record_contract_is_frozen_and_traceable`：review record frozen 且引用 validation/evaluation。 |
| F3-TC-03 | F3-AT-03 | `test_modify_or_reject_generates_override_log`：MODIFY/REJECT 生成 OverrideLog。 |
| F3-TC-04 | F3-AT-04 | `test_need_more_evidence_generates_research_request_proposal`：NEED_MORE_EVIDENCE 生成 draft request。 |
| F3-TC-05 | F3-AT-05 | `test_financial_review_governance_gate_decides_review_artifacts`：治理决策生效。 |
| F3-TC-06 | F3-AT-06 | `test_profile_updates_are_proposals_only`：只生成 proposal，不写正式 profile。 |
| F3-TC-07 | F3-AT-07 | `test_review_artifacts_have_evidence_refs`：所有 artifact evidence 非空。 |
| F3-TC-08 | F3-AT-08 | `test_review_workflow_does_not_mutate_close_validation_result`：F2 result frozen/equal。 |
| F3-TC-09 | F3-AT-09 | `test_f3_does_not_emit_trade_decisions_or_orders`：输出无交易动作词。 |
| F3-TC-10 | F3-AT-10 | `test_f3_does_not_write_memory_or_knowledge_base`：AST/文本审计无正式写入。 |
| F3-TC-11 | F3-AT-11 | `test_review_workflow_is_replayable_from_same_inputs`：重复输入输出等价。 |
| F3-TC-12 | F3-AT-12 | `test_f0_f1_f2_f3_regression_suite_passes`：Required regression command 通过。 |

## 5. Required Commands

必须从 `julia_agent` 仓库根目录执行：

```bash
.venv/bin/python -m pytest -q tests/test_financial_f3_tony_review.py
.venv/bin/python -m pytest -q tests/test_financial_f0_contract.py tests/test_financial_f1_premarket.py tests/test_financial_f2_close_validation.py tests/test_financial_f3_tony_review.py
.venv/bin/python -m py_compile runtime/capability/financial/workflows/tony_review.py
.venv/bin/python -m py_compile runtime/capability/financial/governance/review_policy.py
```

若仓库已配置 ruff/mypy，则作为附加门禁执行：

```bash
.venv/bin/python -m ruff check runtime/capability/financial tests/test_financial_f3_tony_review.py
.venv/bin/python -m mypy runtime/capability/financial
```

## 6. Deliverables

- `runtime/capability/financial/workflows/tony_review.py`
  - Tony review workflow；输入 `CloseValidationResult` 与 review input，输出 `TonyReviewResult`。
- `runtime/capability/financial/governance/review_policy.py`
  - Review governance gate；决定 allow/review_required/reject。
- `runtime/capability/financial/contracts/`
  - 新增 `AnalystReviewRecord`、`OverrideLog`、`TonyReviewResult`、`FinancialReviewGovernanceDecision`、`InvestorProfileUpdateProposal` 或等价 frozen dataclass。
- `tests/test_financial_f3_tony_review.py`
  - F3 验收测试，覆盖 F3-AT-01 至 F3-AT-12。

## 7. Interface Contract

### 7.1 F3 Workflow API

```python
run_tony_review(
    validation: CloseValidationResult,
    review_input: TonyReviewInput,
    *,
    reviewer_id: str = "tony",
    generated_by: str = "julia_financial_shadow",
    model_version: str = "deterministic_f3",
) -> TonyReviewResult
```

### 7.2 Review Actions

```text
APPROVE
MODIFY
REJECT
NEED_MORE_EVIDENCE
```

### 7.3 Governance Decision

```text
allow
review_required
reject
```

### 7.4 Output Contract Requirements

- 所有 F3 contracts 必须为 frozen dataclass。
- `TonyReviewResult.status` 只能是 `draft` 或 `shadow`。
- Profile/Preference updates 只能是 proposal，不得直接更新正式配置。
- OverrideLog 必须引用原 evaluation id，不得覆盖原 evaluation。

## 8. Implementation Task Breakdown

### F3.1 Test First

- 路径：`tests/test_financial_f3_tony_review.py`
- 动作：先创建失败测试，覆盖 12 个 Acceptance Targets。
- 验收：测试初始失败原因是缺少 F3 review contract/workflow，而不是语法错误。

### F3.2 F3 Review Contracts

- 路径：`runtime/capability/financial/contracts/`
- 动作：新增 review/override/governance/proposal frozen dataclass。
- 验收：F0/F1/F2 测试仍通过。

### F3.3 Review Governance Policy

- 路径：`runtime/capability/financial/governance/review_policy.py`
- 动作：实现 deterministic governance gate。
- 验收：四类 action 的 governance decision 可测试。

### F3.4 Tony Review Workflow

- 路径：`runtime/capability/financial/workflows/tony_review.py`
- 动作：从 validation + review input 生成 independent review artifact。
- 验收：F3 Required Commands 通过。

## 9. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Owner | Mitigation |
|---|---|---:|---|---|---|
| Tony override 被直接写入策略或 Memory | 高 | Medium | 出现 profile/memory 直接写入 | Codex | proposal-only；AST/文本扫描。 |
| F3 修改 F2 evaluation 导致审计链断裂 | 高 | Low | validation/evaluation 被回写 | Codex | frozen + equality 测试。 |
| Review action 与交易动作混淆 | 高 | Low | 输出 buy/sell/order | Codex | 交易动作词测试禁止。 |
| Need More Evidence 直接触发真实查询 | Medium | Medium | workflow 调用真实 adapter/database | Codex | 只生成 draft request，不执行。 |
| Governance gate 形同虚设 | Medium | Medium | 所有 action 无条件 allow | Codex | 测试 review_required/reject 分支。 |

## 10. Rollback Plan

### 10.1 代码回滚

- 触发条件：F0/F1/F2 回归测试失败；F3 Required Commands 失败且最小修复后仍失败；proposal-only/governance 边界破坏。
- 回滚方式：回滚 F3 新增路径：
  - `runtime/capability/financial/workflows/tony_review.py`
  - `runtime/capability/financial/governance/review_policy.py`
  - F3 新增 contract 类型
  - `tests/test_financial_f3_tony_review.py`
- 兼容性说明：不得破坏 `phase-f2-complete` tag 对应 baseline。

### 10.2 数据回滚

- 触发条件：误写入 memory/data/正式 profile/knowledge base。
- 回滚方式：删除误写入文件；恢复到 `phase-f2-complete`；不得迁移真实数据库。

### 10.3 同步补偿回滚

- 触发条件：阶段状态已推进但测试证据缺失或失败。
- 回滚方式：状态退回 Doing，附失败命令、日志、变更文件清单；重新执行 Required Commands 后再推进。

## 11. Non-Goals

- 不实现 F4 语音播报。
- 不执行 F5 20 个真实交易日 Shadow Validation。
- 不连接真实市场数据库。
- 不自动修改 Investor Profile、Strategy、World Model、M7 Risk Gate。
- 不写正式 Memory 或金融知识库。
- 不生成正式交易建议、订单、仓位指令或自动交易动作。
- 不让 Need More Evidence 自动触发真实查询；只生成 request proposal。

## 12. State Sync / Reconciliation Baseline

- 实时状态同步顺序：`Doing -> test-evidence -> In review/done -> milestone progress`。
- P0/P1 状态门禁：写入 `In review/done` 时必须传 `--test-files`；`--test-files` 必须在当前 `git diff` 中可见。
- 阶段末对账口径：必须用 `--milestone-id` 全量拉取后本地筛 phase；不得仅用 `--task-prefix + --status` 判断完成度。

## 13. Conflict Resolution

| Conflict Item | Adopted Source | Dropped Source | Reason |
|---|---|---|---|
| 源文档要求 `OverrideLog 持久化`，当前公开仓库仍禁止正式 Memory/DB 写入 | F3 生成可持久化的 shadow `OverrideLog` artifact，正式持久化 adapter 后置 | 直接写入 DB/Memory | F0-F2 governance 已冻结：不直连数据库、不写正式 Memory；F3 先建立 contract/workflow。 |
| 源文档要求 `Investor Profile 更新` | F3 生成 `InvestorProfileUpdateProposal` | 直接更新正式 profile | F3 是 Human Feedback Layer，不是自动学习层。 |

## 14. Contract Self-Check

- [x] 阶段标识完整。
- [x] Acceptance 条款全部可二元判定。
- [x] Required Commands 可复制执行且无破坏性命令。
- [x] Deliverables 全部映射到路径。
- [x] Risk / Rollback / Non-Goals 完整。
- [x] 已继承 F2 APPROVED WITH NOTES 治理备注。
- [x] 已明确 F3 不产生正式交易、不写正式 Memory、不直接更新 profile。
