# Phase A2.1 — Context OS Core Skeleton Report

## 1. 目标与范围

A2.1 的目标是建立最小 Julia Core Context OS runtime skeleton，证明 Julia Core 可以脱离任何 Domain Provider 独立启动与解析空上下文。

本阶段不是完整 Context OS 迁移，不搬迁 `codex/full-agent-architecture-migration` 中的完整 `runtime/context_os/`。

范围内：

- test-first 新增 A2.1 验收测试；
- 新增 `runtime/core/context_os/` 最小骨架；
- 新增 `runtime/core/providers/` provider interface；
- 定义 `ContextRequest`、`ContextBlock`、`ContextPlanner`、`ContextResolver`；
- 验证无 Financial/Domain/Private dependency；
- 验证无 provider 时 Context OS 仍可启动。

范围外：

- 不接入 Financial Provider；
- 不迁移完整 `runtime/context_os/`；
- 不实现 LLM call；
- 不实现 prompt builder；
- 不实现 Memory retrieval；
- 不读取 private identity / memory content；
- 不接 UI / Voice / Avatar；
- 不修改既有 F0-F4 金融 runtime 行为。

## 2. 变更文件清单

| 文件路径 | 变更类型 | 说明 |
|---|---|---|
| `tests/test_a21_context_os_core_skeleton.py` | 新增 | A2.1 Context OS skeleton acceptance tests。 |
| `runtime/core/__init__.py` | 新增 | Julia Core package marker。 |
| `runtime/core/context_os/__init__.py` | 新增 | Context OS public exports。 |
| `runtime/core/context_os/request.py` | 新增 | `ContextRequest` demand-signal contract。 |
| `runtime/core/context_os/block.py` | 新增 | `ContextBlock` short-lived context candidate contract。 |
| `runtime/core/context_os/planner.py` | 新增 | Minimal domain-independent planner。 |
| `runtime/core/context_os/resolver.py` | 新增 | Provider-boundary resolver。 |
| `runtime/core/providers/__init__.py` | 新增 | Provider interface public export。 |
| `runtime/core/providers/interface.py` | 新增 | `DomainProvider` protocol。 |

## 3. 验证命令与结果

| 命令 | 结果 |
|---|---|
| `.venv/bin/python -m pytest -q tests/test_a21_context_os_core_skeleton.py` | PASS — 6 passed |
| `rg -n "financial|stock|market|theme|ai_theme_app|identity/|memory/" runtime/core/context_os runtime/core/providers` | PASS — no matches |
| `.venv/bin/python -m compileall -q runtime/core` | PASS |
| `.venv/bin/python -m pytest -q tests/test_a21_context_os_core_skeleton.py tests/test_financial_f0_contract.py tests/test_financial_f1_premarket.py tests/test_financial_f2_close_validation.py tests/test_financial_f3_tony_review.py tests/test_financial_f4_analyst_chat.py` | PASS — 64 passed |

## 4. Gate Review

| Gate | Status | Evidence |
|---|---|---|
| No Domain dependency | PASS | boundary scan no matches in `runtime/core/context_os` / `runtime/core/providers`。 |
| No Private Data dependency | PASS | no `identity/` or `memory/` references。 |
| No Memory content dependency | PASS | no memory content access。 |
| Provider boundary preserved | PASS | resolver only uses `DomainProvider` protocol and returns `ContextBlock` candidates。 |
| ContextBlock contract unchanged | PASS | `ContextBlock` remains context candidate, not prompt/answer/memory。 |
| Financial Provider absent startup | PASS | `ContextResolver()` resolves empty tuple with no provider installed。 |

## 5. 风险与限制

| 风险/限制 | 当前处理 |
|---|---|
| Skeleton 功能刻意不足 | 符合 A2.1 目标；后续 A2.x 再迁移 planner/budget/provenance。 |
| 与 evaluation branch 完整 Context OS 尚未合流 | 保持不合流；A2.1 只建立正式 core 边界。 |
| Provider registry 未实现 | 后置 A3 Domain Provider Interface。 |
| Context lifecycle 只有 TTL/expiration 最小语义 | 完整 lifecycle 后置 A2.x。 |

## 6. 对账结论

- Branch: `codex/a2.1/context-os-core-skeleton`
- Baseline: `phase-a2.0-context-os-core-migration-contract-complete`
- Gate status: READY FOR REVIEW
- Commit sequence:
  - `7696b64` — Add A2.1 Context OS core skeleton tests
  - `843214b` — Implement A2.1 Context OS core skeleton

## 7. Review Checklist

- [x] Test-first 顺序满足。
- [x] Core imports without any domain provider。
- [x] `ContextRequest` 创建成功且保持 demand-signal 语义。
- [x] `ContextBlock` 创建成功且不是 Memory/Prompt/Answer。
- [x] Mock Provider 通过 provider interface 返回 block。
- [x] 无 Provider 时 Context OS 仍可启动。
- [x] Boundary scan 通过。
- [x] F0-F4 financial regression 通过。

### 待验收

请用户选择：`ACCEPT` / `REWORK` / `REQUEST CHANGES` / `APPROVED WITH NOTES`。
