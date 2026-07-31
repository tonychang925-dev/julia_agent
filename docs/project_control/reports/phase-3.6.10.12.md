# Phase 3.6.10.12 — Structured Compact Runtime

## 1. 目标与范围

本阶段目标是在 Phase 3.6.10.11 的 Budget + Compact Preparation 之后，补齐真正的 **Structured Compact Runtime 执行层**。

阶段边界：

- 只消费显式 `CompactPreparationCandidate`；
- 只在 Budget Pressure 达到 `high / critical` 后执行；
- 保留最近 tail records，不参与 compact；
- 输出 source-grounded `ExperienceCompactState`；
- 写入 Compact Store；
- 生成 Compact Execution Trace；
- 支持 idempotency，避免重复 compact；
- 不直接 mutation SessionState / TaskState / Persona / Identity / Relationship。

## 2. 架构链路

本阶段冻结目标链路：

```text
Context Budget Manager v2
    ↓
CompactPreparationCandidate
    ↓
StructuredCompactRuntime
    ↓
CompactExecutionRequest
    ↓
StructuredCompactEngine
    ↓
ExperienceCompactState
    ↓
CompactStore
    ↓
CompactExecutionTrace
```

关键原则：

```text
Budget Manager prepares.
Structured Compact Runtime executes.
Mutation Runtime remains authority for state mutation.
```

## 3. 变更文件清单

| 文件路径 | 变更类型 | 摘要 |
| --- | --- | --- |
| `runtime/context_os/compact/compact_runtime.py` | 新增 | Structured Compact Runtime v2 执行请求、结果、trace、idempotency 与 tail preservation gate |
| `runtime/context_os/compact/__init__.py` | 修改 | 导出 v2 runtime API |
| `tests/test_phase361012_structured_compact_runtime_v2.py` | 新增 | Phase 3.6.10.12 阶段验收测试 |
| `docs/project_control/reports/phase-3.6.10.12.md` | 新增 | 阶段报告 |

## 4. 新增核心对象

| 对象 | 职责 |
| --- | --- |
| `CompactExecutionRequest` | 显式 compact 执行请求，绑定 candidate、session、source blocks、preserve tail、idempotency key |
| `CompactExecutionStatus` | `applied / skipped / rejected` |
| `CompactExecutionTrace` | 记录 input records、compacted records、preserved tail、compact id、reason |
| `CompactExecutionResult` | runtime 执行结果，包含 status、compact、trace |
| `StructuredCompactRuntime` | compact 执行编排入口 |

## 5. 验收点

### 5.1 Prepared Candidate Gate

PASS。

Runtime 会拒绝：

- 无 `session_id`；
- 无 source blocks；
- `estimated_reclaim_tokens <= 0`；
- candidate urgency 不是 `high / critical`。

### 5.2 Preserve Tail Strategy

PASS。

`preserve_tail_record_ids` 中的 records 会从 compact source range 中排除：

```text
session records
    ↓
exclude preserve_tail_record_ids
    ↓
compact older records only
```

这保证 Phase 3.6.10.11 的 tail reservation 在 compact 执行阶段仍然生效。

### 5.3 Source-Grounded Compact

PASS。

Compact 输出仍使用既有 `ExperienceCompactState` schema，并保留：

- `source_record_ids`
- `source_evidence_ids`
- `decisions`
- `known_failures`
- `open_loops`
- `next_actions`
- `confidence`

### 5.4 Idempotency

PASS。

相同 `idempotency_key` 重复执行时：

```text
first execution  -> APPLIED
second execution -> SKIPPED
```

并返回第一次 compact 的 `compact_id`。

### 5.5 Authority Boundary

PASS。

Runtime 只写 Compact Store，不修改：

| 对象 | 是否直接修改 |
| --- | --- |
| SessionState | 否 |
| TaskState | 否 |
| Persona | 否 |
| Relationship | 否 |
| Identity | 否 |
| MemoryObject | 否 |

## 6. 验证命令与结果

命令：

```bash
python3 -m unittest -v tests.test_phase361012_structured_compact_runtime_v2 tests.test_phase36104_structured_compact_runtime tests.test_phase361011_context_budget_manager_v2
```

结果：

```text
Ran 14 tests in 0.004s
OK
```

覆盖：

- Phase 3.6.10.12 Structured Compact Runtime v2：5/5 PASS
- Phase 3.6.10.4 Structured Compact Runtime v1：5/5 PASS
- Phase 3.6.10.11 Context Budget Manager v2：4/4 PASS

## 7. 风险与限制

| 风险 | 状态 | 说明 |
| --- | --- | --- |
| 当前 Store 仍为 in-memory | Accepted | 后续可接持久化 CompactStore / SQLite |
| compact source block 到 record 映射仍较简单 | Accepted | 当前支持 message_id 与 source_refs 匹配，后续可接 ProjectionBlock provenance index |
| 未自动把 compact 写回 Context Projection | Pending | 应由后续 Mutation / Projection 集成阶段处理 |
| 未引入 LLM summarizer | Accepted | 当前保持 deterministic rule-based，符合可测试与 source-grounded 要求 |

## 8. 阶段结论

Phase 3.6.10.12 当前达到本地验收标准：

```text
Structured Compact Runtime v2 implemented
Prepared Candidate Gate implemented
Preserve Tail Record exclusion implemented
Source-grounded ExperienceCompactState output verified
Compact Store save verified
Execution Trace implemented
Idempotency implemented
Authority Boundary preserved
```

建议状态：

```text
READY FOR REVIEW
```

建议下一阶段：

```text
Phase 3.6.10.13 — Session Resurrection Runtime
```


---

## 9. 验收决策

**Decision:** APPROVED WITH NOTES  
**Status:** APPROVED / FROZEN  
**Accepted At:** 2026-07-29 Asia/Shanghai  
**Freeze Note:** Architecture Accepted, Production Hardening Pending

Phase 3.6.10.12 — Structured Compact Runtime v2 已验收通过并冻结。

## 10. 验收结论

| 验收项 | 结论 |
| --- | --- |
| Compact Boundary | PASS |
| Prepared Candidate Gate | PASS |
| Preserve Tail Strategy | PASS |
| Authority Boundary | PASS |
| Idempotency | PASS |
| Claude-aligned semantics | PASS |
| Production maturity | Needs future hardening |

### 10.1 Compact Boundary

确认 Compact Runtime 没有将 Context Pressure 直接转化为历史覆盖，而是保持：

```text
Budget Manager v2
    ↓
CompactPreparationCandidate
    ↓
StructuredCompactRuntime
    ↓
CompactExecutionResult
    ↓
Compact Store
```

Compact 被定义为 Context Lifecycle 操作，而不是 Memory 操作。

### 10.2 Prepared Candidate Gate

当前链路保持为：

```text
Budget Pressure
    ↓
Candidate
    ↓
Compact Runtime
```

没有变成：

```text
Budget Pressure
    ↓
Compact Everything
```

该边界避免误压缩重要 conversation arc、relationship continuity 与 evidence source。

### 10.3 Preserve Tail Strategy

冻结原则：

```text
Old Context -> Compact Candidate Region
Recent Tail -> Always Preserve
```

最近用户意图、当前任务状态、未完成 open loop、最近上下文语气必须优先保留，避免 compact 后出现失忆式恢复。

### 10.4 Authority Boundary

Compact Runtime 允许：

- summarize experience
- create source-grounded compact state
- save compact into Compact Store
- emit execution trace

Compact Runtime 不允许：

- 修改 Persona
- 修改 Identity
- 修改 Relationship
- 修改 Governance Class
- 直接创建 MemoryObject
- 直接修改 SessionState / TaskState

冻结分层：

```text
Compact = Context Optimization
Memory = Cognitive Evolution
```

### 10.5 Idempotency

确认 `CompactExecutionRequest + CompactExecutionTrace + Compact Store` 已具备基础重复请求防护。

重复请求语义：

```text
first execution  -> APPLIED
second execution -> SKIPPED
```

## 11. Hardening Notes

以下 Notes 非阻塞项，进入后续生产硬化路线。

### NOTE-001 Compact Quality Evaluation

当前 Compact 主要验证：

- 是否生成
- 是否保存
- 是否保护 tail

后续需要增加 `CompactQuality`：

```python
CompactQuality(
    information_retention=0.92,
    open_loop_retention=1.0,
    decision_retention=0.95,
    identity_leakage=0,
)
```

目标：避免 compact 成功但压缩质量差。

### NOTE-002 Evidence Grounding Score

当前 source-grounded compact 方向正确。

后续需要进一步强制 compact summary 引用：

- `source_message_ids`
- `source_evidence_ids`

示例：

```json
{
  "summary": "Tony and Julia started Cognitive Runtime project",
  "sources": ["msg_203", "memory_91", "diary_chunk_12"]
}
```

目标：防止 compact 自己创造历史。

### NOTE-003 Compact State Machine

当前已有 `CompactExecutionStatus`。

后续建议升级为完整 lifecycle：

```text
PREPARED
    ↓
VALIDATING
    ↓
EXECUTING
    ↓
COMPLETED
    ↓
FAILED
    ↓
ROLLED_BACK
```

### NOTE-004 Compact 与 Resurrection 必须绑定设计

Phase 3.6.10.13 不能只是 load compact summary。

目标链路应为：

```text
Compact Store
    +
Preserved Tail
    +
Session State
    +
Task State
    +
Evidence Index
    ↓
Reconstructed Context
```

否则只能恢复文本，不能恢复认知状态。

### NOTE-005 Multi-level Compact Trigger

未来建议从单一 pressure compact 演进为三级 compact：

```text
Level 1: tail trimming
Level 2: micro compact
Level 3: full structured compact
```

对应 Claude 类系统中的：

```text
snip
microcompact
autocompact
```

### NOTE-006 Async Worker Interface

未来保持：

```text
Async Worker
    ↓
CompactPreparation
    ↓
CompactRuntime
```

当前接口已经预留，后续可与 WorkerTrace / Durable Queue 结合。

## 12. Context OS 冻结状态

```text
3.6.10.0  Contract Freeze                 ✅
3.6.10.1  Conversation Truth Layer        ✅
3.6.10.7.1 Execution Kernel              ✅
3.6.10.7.2 Context Projection            ✅
3.6.10.7.3 Mutation Runtime              ✅
3.6.10.8  Conflict Resolver              ✅
3.6.10.9  Session / Task State           ✅
3.6.10.10 Async Maintenance Worker       ✅
3.6.10.11 Context Budget Manager v2      ✅
3.6.10.12 Structured Compact Runtime v2  ✅
```

## 13. 下一阶段

建议进入：

```text
Phase 3.6.10.13 — Session Resurrection Runtime
```

目标：

```text
Cold Start
    ↓
Session Resurrection
    ↓
JuliaContext Reconstruction
    ↓
Continue Conversation
```

该阶段完成后，Julia Context OS 将具备长期 session 恢复能力。
