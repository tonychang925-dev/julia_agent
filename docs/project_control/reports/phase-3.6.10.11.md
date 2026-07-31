# Phase 3.6.10.11 — Context Budget Manager v2

## 1. 目标与范围

本阶段目标是在既有 Context Budget Manager v1 基础上补齐 Context OS 核心的 **Budget + Compact Intelligence 前置层**。

阶段边界：

- 负责动态预算测量与压力判断；
- 负责 Preserve Tail Strategy，确保最近对话尾部在预算紧张时仍被优先保留；
- 负责生成 Compact Preparation Candidate；
- 不执行 Structured Compact；
- 不绕过 Proposal / Policy / Mutation 权威边界；
- 不改变 Phase 3.6.10.10 已冻结的 Worker ≠ Authority 原则。

## 2. 架构决策

### 2.1 Budget Manager v2 新增对象

新增文件：

```text
runtime/context_os/budget/budget_manager_v2.py
```

新增核心对象：

| 对象 | 职责 |
| --- | --- |
| `BudgetEnvelope` | 描述 hard limit、target budget、effective budget、tail reserve、安全余量 |
| `BudgetPressure` | 描述 measured/projected tokens、utilization、pressure level、是否准备 compact |
| `BudgetPressureLevel` | `low / normal / high / critical` |
| `CompactPreparationCandidate` | compact 准备候选，只提供信号，不执行 compact |
| `BudgetAllocationV2` | v2 分配结果，包含 v1 allocation + envelope + pressure + tail + candidates |
| `BudgetPolicyV2` | v2 策略参数：tail ratio、pressure threshold、reclaim threshold |
| `ContextBudgetManagerV2` | v2 编排入口 |

### 2.2 Preserve Tail Strategy

Budget Manager v2 会识别：

- `block_type == "recent_turns"`
- 或 `metadata.preserve_tail == True`

并保留最新 tail blocks：

```text
recent_turns / preserve_tail
        ↓
priority boost
        ↓
required=True during allocation
        ↓
preserved under tight budget
```

该策略保证 Voice Runtime / Conversation Loop 中最近上下文不会被历史证据或 compact state 挤出。

### 2.3 Budget Pressure Measurement

v2 区分：

- `measured_tokens`：当前 block 实际测量；
- `projected_tokens`：当前测量 + tail reserve；
- `utilization`：当前利用率；
- `projected_utilization`：保留尾部后的预计利用率；
- `pressure level`：`low / normal / high / critical`。

当压力达到 `high` 或 `critical` 时，只触发 compact preparation signal。

### 2.4 Compact Preparation，不执行 Compact

v2 明确输出：

```json
{
  "compact_preparation_needed": true,
  "compact_executed": false
}
```

这与 Phase 3.6.10.10 NOTE-005 保持一致：

> prepare candidate, not execute compact.

Compact 真正执行仍留给：

```text
Phase 3.6.10.12 — Structured Compact Runtime
```

## 3. 变更文件清单

| 文件路径 | 变更类型 | 摘要 |
| --- | --- | --- |
| `runtime/context_os/budget/budget_manager_v2.py` | 新增 | Budget Manager v2 数据模型、策略与分配入口 |
| `runtime/context_os/budget/__init__.py` | 修改 | 导出 v2 API |
| `tests/test_phase361011_context_budget_manager_v2.py` | 新增 | v2 阶段验收测试 |
| `docs/project_control/reports/phase-3.6.10.11.md` | 新增 | 阶段报告 |

## 4. 验收测试

新增测试文件：

```text
tests/test_phase361011_context_budget_manager_v2.py
```

覆盖用例：

| TC-ID | 验收点 | 结果 |
| --- | --- | --- |
| `TC-361011-001` | tight budget 下 recent tail 被保留 | PASS |
| `TC-361011-002` | over-budget projection 触发 compact preparation pressure | PASS |
| `TC-361011-003` | high pressure 下生成 prepare-only compact candidate | PASS |
| `TC-361011-004` | low pressure 下不生成 compact candidate | PASS |

## 5. 验证命令与结果

### 5.1 pytest 尝试

命令：

```bash
/Users/admin/julia_agent/.venv/bin/python -m pytest -q /Users/admin/julia_agent/tests/test_phase361011_context_budget_manager_v2.py /Users/admin/julia_agent/tests/test_phase36103_context_budget_manager.py
```

结果：

```text
/Users/admin/julia_agent/.venv/bin/python: No such file or directory
```

说明：项目目录未发现 `.venv/bin/python`。

### 5.2 python3 pytest 尝试

命令：

```bash
python3 -m pytest -q /Users/admin/julia_agent/tests/test_phase361011_context_budget_manager_v2.py /Users/admin/julia_agent/tests/test_phase36103_context_budget_manager.py
```

结果：

```text
No module named pytest
```

说明：当前 Python 环境未安装 pytest。

### 5.3 unittest 验证

命令：

```bash
python3 -m unittest -v tests.test_phase361011_context_budget_manager_v2 tests.test_phase36103_context_budget_manager
```

结果：

```text
Ran 8 tests in 0.002s
OK
```

通过测试：

- Phase 3.6.10.11 v2 测试：4/4 PASS
- Phase 3.6.10.3 v1 回归测试：4/4 PASS


### 5.4 Compact Runtime 回归验证

命令：

```bash
python3 -m unittest -v tests.test_phase36104_structured_compact_runtime tests.test_phase361011_context_budget_manager_v2 tests.test_phase36103_context_budget_manager
```

结果：

```text
Ran 13 tests in 0.005s
OK
```

覆盖范围：

- Phase 3.6.10.4 Structured Compact Runtime：5/5 PASS
- Phase 3.6.10.11 Context Budget Manager v2：4/4 PASS
- Phase 3.6.10.3 Context Budget Manager v1：4/4 PASS

## 6. 架构合规性

### 6.1 Authority Boundary

PASS。

Budget Manager v2 只负责：

```text
measure
allocate
prepare candidate
trace
```

不负责：

```text
mutation
state write
compact execution
worker authority
```

### 6.2 Async / Compact 顺序

PASS。

当前链路保持为：

```text
Context Blocks
   ↓
Budget Manager v2
   ↓
BudgetAllocationV2
   ↓
CompactPreparationCandidate
   ↓
Future Structured Compact Runtime
```

没有提前进入：

```text
Budget Manager
   ↓
execute compact
```

### 6.3 向后兼容

PASS。

v1 API 保持不变：

- `BudgetAllocation`
- `BudgetPolicy`
- `ContextBudgetManager`
- `ContextBlock`
- `estimate_tokens`

并通过 v1 回归测试验证。

## 7. 风险与限制

| 风险 | 状态 | 说明 |
| --- | --- | --- |
| Token estimator 仍为粗估 | Accepted | 当前仍沿用 deterministic rough estimator，后续可接入真实 tokenizer |
| Tail reserve 参数需要生产调优 | Accepted | 默认 `preserve_tail_ratio=0.18`，后续可按 Voice Runtime latency / quality 数据调整 |
| Compact candidate 未接 WorkerTrace | Pending | 可在 Phase 3.6.10.12/13 与 NOTE-003 Worker Observability 合并处理 |
| 未接 durable queue | Pending | 属于 Phase 3.6.10.10 NOTE-001 hardening |

## 8. 阶段结论

Phase 3.6.10.11 当前达到本地验收标准：

```text
Context Budget Manager v2 implemented
Preserve Tail Strategy implemented
Budget Pressure Measurement implemented
Compact Preparation Candidate implemented
Compact execution intentionally not implemented
v1 backward compatibility verified
Structured Compact Runtime compatibility verified
```

建议状态：

```text
READY FOR REVIEW
```

建议下一阶段：

```text
Phase 3.6.10.12 — Structured Compact Runtime
```


---

## 9. 验收决策

**Decision:** ACCEPT  
**Status:** APPROVED / FROZEN  
**Accepted At:** 2026-07-29 Asia/Shanghai

Phase 3.6.10.11 — Context Budget Manager v2 已验收通过并冻结。

冻结内容：

- Budget Pressure Measurement
- Budget Envelope
- Preserve Tail Strategy
- Compact Preparation Candidate
- Prepare-only Compact Signal
- v1 Budget Manager backward compatibility
- Structured Compact Runtime compatibility

后续路线：

```text
Phase 3.6.10.12 — Structured Compact Runtime
        ↓
Phase 3.6.10.13 — Session Resurrection Runtime
```
