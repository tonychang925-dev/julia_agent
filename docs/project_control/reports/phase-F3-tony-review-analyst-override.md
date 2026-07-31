# Phase F3 — Tony Review & Analyst Override Layer Report

## 1. 目标与范围

本阶段基于 `docs/project_control/PHASE_CONTRACT_F3.md` 与 F3 `APPROVED WITH NOTES` 执行 test-first implementation，引入 Human-in-the-loop Analyst Governance，使 Tony 可以对 F2 close validation 结果进行 approve/modify/reject/need-more-evidence 复核，并生成独立 shadow review artifact。

核心链路：

```text
CloseValidationResult
        ↓
TonyReviewInput
        ↓
AnalystReviewRecord / OverrideLog / NeedMoreEvidenceRequest
        ↓
FinancialReviewGovernanceDecision
        ↓
TonyReviewResult
```

范围内：

- 记录 F3 Contract approval notes。
- 新增 F3 failing acceptance tests。
- 新增 F3 review/override/governance/proposal contracts。
- 新增 deterministic review governance gate。
- 新增 deterministic Tony review workflow。
- 验证 F2 result 不被修改、OverrideLog immutable、review_timestamp、proposal-only、EvidenceRef 全覆盖、无交易/无 memory/profile 正式写入。

范围外：

- 不写正式 Memory。
- 不直接更新 Investor Profile。
- 不修改策略、World Model、M7 Risk Gate。
- 不触发交易。
- 不自动执行 Need More Evidence 查询。

## 2. 变更文件清单

| 文件路径 | 变更类型 | 说明 |
|---|---|---|
| `docs/project_control/PHASE_CONTRACT_F3.md` | 新增/修改 | F3 Contract 与 approval notes。 |
| `tests/test_financial_f3_tony_review.py` | 新增 | F3 验收测试，覆盖 12 个 Acceptance Targets。 |
| `runtime/capability/financial/contracts/__init__.py` | 修改 | 新增 F3 review contracts。 |
| `runtime/capability/financial/governance/review_policy.py` | 新增 | deterministic review governance gate。 |
| `runtime/capability/financial/workflows/tony_review.py` | 新增 | deterministic Tony review workflow。 |

## 3. 验证命令与结果

| 命令 | 结果 |
|---|---|
| `.venv/bin/python -m pytest -q tests/test_financial_f3_tony_review.py` | PASS — 12 passed |
| `.venv/bin/python -m pytest -q tests/test_financial_f0_contract.py tests/test_financial_f1_premarket.py tests/test_financial_f2_close_validation.py tests/test_financial_f3_tony_review.py` | PASS — 49 passed |
| `.venv/bin/python -m py_compile runtime/capability/financial/workflows/tony_review.py` | PASS — exit 0 |
| `.venv/bin/python -m py_compile runtime/capability/financial/governance/review_policy.py` | PASS — exit 0 |

附加核查：

- F3 test-first 顺序满足：`4c5b6e1 Add F3 Tony review acceptance tests` 先于实现 commit `540e990`。
- `OverrideLog` frozen 且独立于 F2 evaluation。
- `TonyReviewInput.review_timestamp` 进入 review record / override log。
- `InvestorProfileUpdateProposal` 仅为 proposal。
- `NeedMoreEvidenceRequest` 状态为 draft，不执行真实查询。

## 4. 风险与限制

| 风险/限制 | 当前处理 |
|---|---|
| F3 override 被误认为修改 F2 truth | F3 只生成独立 artifact，不修改 validation/evaluation。 |
| Proposal 被误认为正式 profile 更新 | contract 字段为 `InvestorProfileUpdateProposal`，status=`proposal`。 |
| Governance gate 过于简单 | 当前为 deterministic F3 baseline；后续可扩展 policy version。 |
| NeedMoreEvidence 未接真实 evidence pipeline | 符合 F3 Non-Goals；真实查询后置。 |

## 5. 对账结论

- Branch: `codex/f3/tony-review-analyst-override`
- Base: `phase-f2-complete` / `main@7a0c8ef`
- Gate status: READY FOR REVIEW
- Changed files limited to F3 contract, F3 tests, F3 financial contracts/governance/workflow, and F3 report.

## 6. Review Checklist

### 功能完整性

- [x] 四类 Tony action 支持。
- [x] AnalystReviewRecord 已实现。
- [x] OverrideLog 已实现。
- [x] NeedMoreEvidenceRequest 已实现。
- [x] FinancialReviewGovernanceDecision 已实现。
- [x] InvestorProfileUpdateProposal 已实现。

### 质量门禁

- [x] F3 pytest 通过。
- [x] F0+F1+F2+F3 回归通过。
- [x] py_compile 通过。
- [x] 测试先行提交顺序满足。

### 架构合规

- [x] 不修改 F2 result。
- [x] 不写正式 Memory。
- [x] 不直接更新 Profile。
- [x] 不触发交易。
- [x] NeedMoreEvidence 仅 proposal/draft。

### 待验收

请用户选择：`ACCEPT` / `REWORK` / `REQUEST CHANGES` / `APPROVED WITH NOTES`。

## 7. Approval Decision — APPROVED WITH NOTES

Decision: `APPROVED WITH NOTES`

Approval rationale:

- F3 成功建立 Tony ↔ Julia 的 Human-in-the-loop Governance Layer。
- F0/F1/F2/F3 全链路回归通过，证明 Contract Boundary、Research Layer、Evaluation Layer、Governance Layer 兼容。
- `OverrideLog` 保持独立 immutable artifact，不修改 F2 `CloseValidationResult`。
- `InvestorProfileUpdateProposal` 保持 proposal-only，不直接更新正式 profile。
- `NeedMoreEvidenceRequest` 保持 draft/proposal，不自动执行真实查询。

Merge Notes:

1. **Override 不等于 Correction**：OverrideLog 是 Human Interpretation Layer，不是 AI Error Fix Patch；Julia 与 Tony 的差异可能来自观察周期、证据权重或评价维度不同。
2. **Governance Decision 必须可追溯**：长期保持 `Review Input + EvidenceRefs + Decision + Reviewer + Timestamp` 的完整审计链。
3. **Proposal 不进入 Memory**：F3 artifact 需经未来 F5 Governance Gate 后才可进入 Analyst Memory；不得提前写入 Julia Personality Memory 或正式金融记忆。
4. **为 F4/F5 保留接口**：F3 的 Research + Evaluation + Human Feedback 将作为 F5 Analyst Learning 的输入基础；F4 应只增加交互入口，不增加金融判断能力。

Recommended next phase:

- **F4 — Julia Analyst Interaction Layer**
- Objective: 将 Julia Financial Analyst 从后台能力连接到 Analyst Workbench，为 Tony 提供对话、上下文选择、Evidence 展示与 analyst workflow 入口。
- Core flow: `Analyst Workbench -> Julia Interaction Gateway -> Context Builder -> Julia Runtime -> Financial Capability`。
