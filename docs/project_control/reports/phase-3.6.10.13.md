# Phase 3.6.10.13 — Session Resurrection Runtime

## 1. 目标与范围

本阶段目标是实现 Julia Context OS 的 Cold Start 认知状态恢复能力。

核心定义：

```text
Julia 不只是恢复过去的 conversation，而是恢复过去的 Cognitive State。
```

错误路径：

```text
load transcript
    ↓
继续聊天
```

冻结的正确路径：

```text
Historical Experience
    +
Compact State
    +
Session State
    +
Task State
    +
Open Loops
    +
Evidence References
    ↓
Session Resurrection Engine
    ↓
JuliaContext Reconstruction
    ↓
Continue Conversation
```

阶段边界：

- 恢复 SessionState；
- 恢复 TaskState；
- 加载 latest Compact；
- 恢复 preserved/recent tail；
- 恢复 open loops / next actions；
- 恢复 evidence references；
- 构建 provider-independent `JuliaContext`；
- 输出 explainable validation result；
- 不执行 `MemoryRuntime.load_all()`；
- 不直接修改 Persona / Identity / Relationship / MemoryObject。

## 2. 新增模块

新增目录：

```text
runtime/context_os/resurrection/
├── __init__.py
├── resurrection_request.py
├── resurrection_snapshot.py
├── resurrection_loader.py
├── context_reconstructor.py
├── state_restorer.py
├── evidence_restorer.py
├── resurrection_validator.py
└── resurrection_runtime.py
```

## 3. 核心对象

| 对象 | 职责 |
| --- | --- |
| `ResurrectionRequest` | 描述要恢复哪个 Julia 状态：user/session/target_time/task_hint |
| `ResurrectionSnapshot` | 恢复输入集合：SessionState、TaskState、Compact、recent tail、open loops、evidence refs |
| `JuliaContext` | provider-independent 的重建认知上下文 |
| `InMemoryResurrectionSource` | 测试/本地 runtime source adapter |
| `ResurrectionLoader` | 加载 SessionState / TaskState / latest Compact / tail / evidence refs |
| `StateRestorer` | 按 authority 恢复显式 state，TaskState 优先于 Compact text |
| `EvidenceRestorer` | 恢复 evidence refs，不加载全部 memory，并过滤 assistant-generated tail |
| `ContextReconstructor` | 从 snapshot 构建 JuliaContext |
| `ResurrectionValidator` | 输出 restored/sources/missing/confidence/warnings |
| `SessionResurrectionRuntime` | 端到端 resurrection 编排入口 |

## 4. 冻结恢复流程

```text
SessionResurrectionRuntime
    ↓
1. Load Session State
    ↓
2. Load Task State
    ↓
3. Load Latest Compact
    ↓
4. Restore Recent / Preserved Tail
    ↓
5. Restore Open Loops
    ↓
6. Resolve Evidence References
    ↓
7. Validate Context Quality
    ↓
8. Build JuliaContext
```

## 5. 关键原则

### 5.1 不恢复全部 Memory

PASS。

Resurrection Runtime 不调用：

```text
MemoryRuntime.load_all()
```

冻结原则：

```text
Resurrection
    ↓
Context reconstruction
    ↓
Memory retrieval only if required by Semantic Evidence Layer
```

Memory 仍由 Semantic Evidence Layer 按 query / intent 决定。

### 5.2 Compact 是恢复入口之一，不是唯一来源

PASS。

恢复优先级：

```text
Current explicit state
    >
Task State
    >
Session State
    >
Compact Summary
    >
Recent Tail
    >
Semantic Evidence
```

实现上：

- `TaskState.objective` 优先决定 `JuliaContext.current_task`；
- `SessionState.project_context` 优先决定 project / phase；
- Compact 提供 decisions / open_loops / next_actions 的 source-grounded 补充；
- Recent tail 提供最新连续性；
- Evidence refs 只作为引用恢复，不做全量 memory load。

### 5.3 Resurrection 可解释

PASS。

`ResurrectionResult.to_dict()` 输出：

```json
{
  "restored": true,
  "sources": ["session_state", "task_state", "ctx_compact_x", "msg_203"],
  "missing": [],
  "confidence": 0.94
}
```

用于调试：为什么 Julia 认为当前处于某项目、某阶段、某任务。

### 5.4 Evidence Integrity

PASS。

Recent tail 加载时排除 assistant-generated response，避免错误 assistant response 参与冷启动恢复。

### 5.5 Provider Independence

PASS。

同一个 `ResurrectionSnapshot` 重建出的 `JuliaContext` 不依赖 DeepSeek / Claude / GPT provider。

## 6. 验收测试

新增测试文件：

```text
tests/test_phase361013_session_resurrection_runtime.py
```

覆盖用例：

| TC-ID | 验收点 | 结果 |
| --- | --- | --- |
| `TC-361013-001` | Cold Start Recovery 恢复项目、阶段、任务 | PASS |
| `TC-361013-002` | Task Continuity 恢复下一步，不重新规划 | PASS |
| `TC-361013-003` | Open Loop Recovery 合并 task/compact/tail open loops | PASS |
| `TC-361013-004` | Evidence Integrity 过滤错误 assistant response | PASS |
| `TC-361013-005` | Provider Independence 同 snapshot 重建一致 | PASS |

## 7. 验证命令与结果

命令：

```bash
python3 -m unittest -v tests.test_phase361013_session_resurrection_runtime tests.test_phase361012_structured_compact_runtime_v2 tests.test_phase361011_context_budget_manager_v2 tests.test_phase36104_structured_compact_runtime
```

结果：

```text
Ran 19 tests in 0.007s
OK
```

覆盖：

- Phase 3.6.10.13 Session Resurrection Runtime：5/5 PASS
- Phase 3.6.10.12 Structured Compact Runtime v2：5/5 PASS
- Phase 3.6.10.11 Context Budget Manager v2：4/4 PASS
- Phase 3.6.10.4 Structured Compact Runtime v1：5/5 PASS

## 8. 变更文件清单

| 文件路径 | 变更类型 | 摘要 |
| --- | --- | --- |
| `runtime/context_os/resurrection/resurrection_request.py` | 新增 | ResurrectionRequest |
| `runtime/context_os/resurrection/resurrection_snapshot.py` | 新增 | ResurrectionSnapshot / JuliaContext |
| `runtime/context_os/resurrection/resurrection_loader.py` | 新增 | Source adapter 与 loader |
| `runtime/context_os/resurrection/context_reconstructor.py` | 新增 | JuliaContext reconstruction |
| `runtime/context_os/resurrection/state_restorer.py` | 新增 | Session/Task state restore |
| `runtime/context_os/resurrection/evidence_restorer.py` | 新增 | Evidence refs restore |
| `runtime/context_os/resurrection/resurrection_validator.py` | 新增 | Validation result |
| `runtime/context_os/resurrection/resurrection_runtime.py` | 新增 | End-to-end runtime |
| `runtime/context_os/resurrection/__init__.py` | 新增 | resurrection API exports |
| `tests/test_phase361013_session_resurrection_runtime.py` | 新增 | 阶段验收测试 |
| `docs/project_control/reports/phase-3.6.10.13.md` | 新增 | 阶段报告 |

## 9. 风险与限制

| 风险 | 状态 | 说明 |
| --- | --- | --- |
| 当前 resurrection source 为 in-memory adapter | Accepted | 后续可接 SQLite / durable store |
| Tail preservation 目前按 active non-assistant records | Accepted | 后续可接 explicit preserved_tail index |
| Evidence refs 只恢复引用，不主动检索 | Intentional | 符合“不恢复全部 Memory”原则 |
| Context quality validator 仍为基础 confidence gate | Pending | 可在 3.6.10.16 benchmark 阶段增强 |

## 10. 阶段结论

Phase 3.6.10.13 当前达到本地验收标准：

```text
Cold Start Recovery implemented
Session State restore implemented
Task State restore implemented
Latest Compact restore implemented
Recent Tail restore implemented
Open Loop restore implemented
Evidence Reference restore implemented
JuliaContext Reconstruction implemented
Explainable validation implemented
Provider Independence verified
No MemoryRuntime.load_all path introduced
```

建议状态：

```text
READY FOR REVIEW
```

## 11. 下一阶段建议

```text
3.6.10.14 Context Invariant Protection
3.6.10.15 Multi-level Compact Strategy
3.6.10.16 Production Context OS Benchmark
3.7 Autonomous Cognitive Action Runtime
```

本阶段完成后，Julia Context OS 从“长期记忆系统”升级为“长期认知状态恢复系统”。


---

## 12. 验收决策

**Decision:** APPROVED WITH NOTES  
**Status:** APPROVED / FROZEN  
**Accepted At:** 2026-07-29 Asia/Shanghai  
**Freeze Note:** Architecture Accepted, Production Hardening Pending

Phase 3.6.10.13 — Session Resurrection Runtime 已验收通过并冻结。

## 13. 核心验收结论

| 验收项 | 结论 |
| --- | --- |
| Resurrection 定位 | PASS |
| Memory Boundary | PASS |
| State Restoration 分层 | PASS |
| Explainable Recovery | PASS |
| Provider Independence | PASS |
| Production Hardening | Pending |

### 13.1 Resurrection 定位正确

冻结判断：Resurrection 不是恢复聊天记录，而是恢复 Cognitive State。

当前链路：

```text
Cold Start
    ↓
Session State Restore
Task State Restore
Compact Restore
Recent Tail Restore
Open Loop Restore
Evidence Restore
    ↓
JuliaContext Reconstruction
    ↓
Provider
```

该实现没有退化为：

```text
load transcript
    ↓
continue chat
```

### 13.2 Memory Boundary 保持正确

冻结约束：不引入 `MemoryRuntime.load_all()`。

原因：如果 Resurrection 直接 load all memory，会导致：

- 历史噪声重新进入 Context；
- 已 decay memory 重新激活；
- assistant hallucination memory 被重新污染；
- Context OS 和 Memory Runtime 边界崩溃。

冻结链路：

```text
Resurrection
    ↓
Context Reconstruction
    ↓
Semantic Evidence / Memory Retrieval 按需触发
```

### 13.3 State Restoration 分层正确

冻结恢复顺序：

```text
1. Session State
2. Task State
3. Compact State
4. Recent Tail
5. Open Loop
6. Evidence Reference
```

职责边界：

- Session / Task 定义：现在 Julia 在做什么；
- Compact 定义：过去发生了什么重要变化；
- Evidence 定义：需要时去哪里查证。

### 13.4 Explainable Recovery

恢复结果必须可解释。

冻结输出要求：

```json
{
  "restored": true,
  "sources": ["session_state", "task_state", "compact", "tail"],
  "confidence": 0.94
}
```

原则：Julia 不仅知道，还知道为什么知道。

### 13.5 Provider Independence

冻结原则：

```text
Julia Runtime
    ↓
Cognitive State
    ↓
Provider Expression
```

禁止退化为：

```text
Provider
    ↓
Julia Identity
```

同一个 `ResurrectionSnapshot` 输入 DeepSeek / Claude / GPT 时，JuliaContext 不应变化。

## 14. Hardening Notes

以下 Notes 非阻塞项，进入后续生产硬化路线。

### NOTE-001 Resurrection Confidence Model

当前 confidence 已存在。

后续建议升级为结构化模型：

```python
ResurrectionConfidence(
    session_state_confidence=0.95,
    task_state_confidence=0.94,
    compact_confidence=0.90,
    evidence_confidence=0.88,
    missing_context_penalty=0.03,
)
```

目标：恢复失败时能判断是 session 丢失、compact 不完整还是 evidence 不足。

### NOTE-002 Resurrection Conflict Resolver

未来需要处理状态冲突，例如：

```text
Session State: Phase 3.6.10.12
Compact:       Phase 3.6.10.13
Task:          Phase 3.6.10.14
```

目标链路：

```text
Resurrection
    ↓
Context Conflict Resolver
    ↓
Canonical State
```

建议复用 Phase 3.6.10.8 Context Conflict Resolver，不重新实现。

### NOTE-003 Resurrection Snapshot Versioning

长期运行必须支持 snapshot schema/version metadata：

```json
{
  "snapshot_schema": "v1",
  "created_at": "...",
  "runtime_version": "..."
}
```

目标：保障 JuliaContext v4 -> v5 等未来升级时旧 session 可恢复。

### NOTE-004 Multi-session Merge

当前阶段聚焦 single session resurrection。

未来需要 Session Federation：

```text
Morning Voice Session
    +
Evening Engineering Session
    +
Weekend Reflection Session
    ↓
Unified Julia State
```

该项不阻塞当前冻结。

### NOTE-005 Resurrection Benchmark

建议增加 Cold Start Benchmark：

```text
昨天：完成 Context OS 3.6.10.12，下一步 Session Resurrection
今天：继续
期望：Julia 直接恢复当前阶段 / 未完成项 / 下一步
```

目标：避免冷启动后重新询问“你想做什么”。

## 15. Context OS 冻结状态

```text
3.6.10.0  Contract Freeze              ✅
3.6.10.1  Conversation Truth Layer     ✅
3.6.10.7.1 Execution Kernel            ✅
3.6.10.7.2 Context Projection          ✅
3.6.10.7.3 Mutation Runtime            ✅
3.6.10.8  Conflict Resolver            ✅
3.6.10.9  Session / Task State         ✅
3.6.10.10 Async Maintenance Worker     ✅
3.6.10.11 Context Budget Manager v2    ✅
3.6.10.12 Structured Compact Runtime   ✅
3.6.10.13 Session Resurrection         ✅
```

## 16. 下一阶段

建议进入：

```text
Phase 3.6.10.14 — Context Invariant Protection Runtime
```

目标：无论 Compact、Worker、LLM、Provider、Migration 如何变化，Julia 的核心认知不被破坏。

重点保护：

- Persona
- Relationship
- Identity
- Governed Memory
- Project Continuity
- Cognitive Ownership

该阶段完成后，Phase 3.6.10 Context OS 将基本形成闭环。
