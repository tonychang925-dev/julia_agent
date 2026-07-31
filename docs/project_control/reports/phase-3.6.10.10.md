# Phase 3.6.10.10 — Async Context Maintenance Worker

## 1. 目标与范围
实现 Julia Context OS 的异步后台认知维护层。Worker 不直接修改 Memory / SessionState / TaskState，而是生成 StateProposal，经 ProposalPolicy / ProposalValidator 校验后，再交由治理后的 MutationRuntime 执行。

## 2. 变更文件清单
| 文件路径 | 变更类型 | 说明 |
| --- | --- | --- |
| runtime/context_os/proposal/state_proposal.py | 新增 | StateProposal / ProposalType，支持转为受控 ContextMutation |
| runtime/context_os/proposal/proposal_policy.py | 新增 | ProposalDecision / ProposalPolicy，保护 persona / relationship / identity |
| runtime/context_os/proposal/proposal_validator.py | 新增 | ProposalValidationResult / ProposalValidator，区分 mutation_ready 与 candidate_only |
| runtime/context_os/proposal/__init__.py | 新增 | Proposal 包导出 |
| runtime/context_os/worker/worker_event.py | 新增 | WorkerEvent 与 turn_completed 事件工厂 |
| runtime/context_os/worker/worker_queue.py | 新增 | 非阻塞内存事件队列 |
| runtime/context_os/worker/memory_maintenance.py | 新增 | MemoryCandidate 分析 Worker |
| runtime/context_os/worker/session_maintenance.py | 新增 | SessionStateProposal 分析 Worker |
| runtime/context_os/worker/task_maintenance.py | 新增 | TaskStateProposal / open_loop resolved 分析 Worker |
| runtime/context_os/worker/compact_preparation.py | 新增 | CompactCandidate 准备 Worker |
| runtime/context_os/worker/maintenance_job.py | 新增 | 聚合 Memory / Session / Task / Compact / Evidence 分析 |
| runtime/context_os/worker/worker_runtime.py | 新增 | AsyncContextMaintenanceRuntime 与 crash isolation |
| runtime/context_os/worker/__init__.py | 新增 | Worker 包导出 |
| runtime/context_os/__init__.py | 修改 | 顶层导出 Proposal / Worker 对象 |
| tests/test_phase361010_async_context_maintenance_worker.py | 新增 | TC-361010-001~006 验收测试 |

## 3. 验证命令与结果
```bash
python3 -m unittest tests/test_phase361010_async_context_maintenance_worker.py
# Ran 6 tests — OK
```

```bash
python3 -m unittest tests/test_phase36109_session_task_state_runtime.py tests/test_phase361010_async_context_maintenance_worker.py
# Ran 12 tests — OK
```

```bash
python3 -m compileall -q runtime/context_os tests/test_phase361010_async_context_maintenance_worker.py
# OK
```

## 4. 验收用例映射
| TC | 结果 | 覆盖点 |
| --- | --- | --- |
| TC-361010-001 Async Isolation | PASS | enqueue 不执行维护，Conversation/Voice Loop 可继续 |
| TC-361010-002 Memory Proposal | PASS | 生成 MemoryCandidate，candidate_only，不可直接 mutation |
| TC-361010-003 Session Proposal | PASS | 检测长期架构状态并生成 SessionStateProposal |
| TC-361010-004 Task Evolution | PASS | 检测 open_loop resolved 与 next_action |
| TC-361010-005 Authority Protection | PASS | persona / relationship 受保护字段被拒绝 |
| TC-361010-006 Crash Recovery | PASS | Worker 崩溃只记录 errors，不影响主状态流 |

## 5. 风险与限制
- 当前 WorkerQueue 为内存队列，后续如需跨进程恢复可扩展持久化队列。
- 维护 Worker 使用轻量规则分析，后续可接入更强 Reflection/Embedding，但必须继续保持 Proposal Boundary。
- CompactCandidate 已准备，但 Structured Compact Runtime 的完整预算联动应放到后续 Phase。

## 6. 结论
Phase 3.6.10.10 已完成：Julia Context OS 现在具备 Async Context Maintenance Worker + Async Proposal Layer，保持 LLM=Interpreter、Worker=Analyst、Runtime Policy=Authority 的状态权威边界。

---

## 7. 验收决策

**Decision:** APPROVED WITH NOTES  
**Status:** Architecture Accepted, Production Hardening Pending

Phase 3.6.10.10 — Async Context Maintenance Worker 达到阶段验收标准，可以冻结为当前架构基线。

### 7.1 验收结论

| 验收项 | 结论 | 说明 |
| --- | --- | --- |
| Async Architecture | PASS | Conversation Loop → Event Queue → Async Worker → StateProposal → Policy / Validator → Mutation Runtime 链路成立 |
| Authority Boundary | PASS | Worker 只生成 Proposal，不直接修改 Runtime State |
| Async Isolation | PASS | Voice / Conversation Loop 不等待后台认知维护完成 |
| Proposal Layer | PASS | `runtime/context_os/proposal/` 成为 Cognitive Change Control Plane |
| Claude Context OS Alignment | PASS | Experience → Interpretation → Proposal → Policy → Mutation → Future Context 闭环成立 |

### 7.2 冻结边界

Worker 权限边界冻结如下：

| 对象 | Worker 权限 |
| --- | --- |
| MemoryObject | 不直接修改 |
| SessionState | 不直接修改 |
| TaskState | 不直接修改 |
| Persona | 禁止修改 |
| Relationship | 禁止修改 |
| Identity | 禁止修改 |

权威路径冻结为：

```text
LLM
 ↓
Worker
 ↓
Proposal
 ↓
Policy / Validator
 ↓
Mutation Runtime
 ↓
State Update
```

## 8. Approved Notes / Production Hardening Pending

### NOTE-001 Worker Queue Persistence
当前 Event Queue 为内存队列。生产级需要支持 Julia Runtime crash 后恢复 pending worker event。

建议后续引入：

```text
worker_events.jsonl
```

或 SQLite-backed durable queue。

### NOTE-002 Proposal Lifecycle
当前 `StateProposal` 已存在，但后续需要补全生命周期：

```text
CREATED → VALIDATING → APPROVED → APPLIED → REJECTED → EXPIRED
```

否则未来大量 proposal 会缺少审计轨迹。

### NOTE-003 Worker Observability
建议增加 `WorkerExecutionTrace`，用于追踪后台认知维护活动。

示例：

```json
{
  "job": "memory_maintenance",
  "input_turns": ["turn_1001", "turn_1002"],
  "proposal_count": 3,
  "approved": 1,
  "rejected": 2
}
```

### NOTE-004 Conflict Resolver Integration
后续建议将链路升级为：

```text
Worker
 ↓
Proposal
 ↓
Conflict Resolver
 ↓
Policy
 ↓
Mutation
```

原因：异步产生的信息可能与当前 Session / Task State 冲突，需要裁决后才能进入 Policy / Mutation。

### NOTE-005 Compact Preparation 不应提前 Compact
当前 `compact_preparation.py` 只生成 CompactCandidate，方向正确。必须保持 prepare candidate，而不是 execute compact。

真正 Compact 应等待以下能力完成后再进入：

- Context Budget Manager v2
- Token Measurement
- Preserve Tail Strategy
- Structured Compact Runtime

## 9. Context OS 冻结状态

| Phase | Module | Status |
| --- | --- | --- |
| 3.6.10.0 | Context OS Contract | Frozen |
| 3.6.10.1 | Conversation Truth Layer | Frozen |
| 3.6.10.7.1 | Execution Kernel | Frozen |
| 3.6.10.7.2 | Context Projection | Frozen |
| 3.6.10.7.3 | Mutation Runtime | Frozen |
| 3.6.10.8 | Conflict Resolver | Frozen |
| 3.6.10.9 | Session / Task State | Frozen |
| 3.6.10.10 | Async Context Maintenance | Approved with Notes |

## 10. 后续路线

冻结后的建议路线：

```text
Phase 3.6.10.11 — Context Budget Manager v2
        ↓
Phase 3.6.10.12 — Structured Compact Runtime
        ↓
Phase 3.6.10.13 — Session Resurrection Runtime
```

进入下一阶段的核心问题：

> 在有限 Context Window 内，如何动态决定“保留什么”。

也就是正式进入 Context OS 的 Budget + Compact Intelligence 层。
