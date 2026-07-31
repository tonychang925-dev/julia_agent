# Phase 3.7.5 — Autonomous Cognitive Loop Runtime Report

Date: 2026-07-29
Status: READY FOR REVIEW
Scope: bounded, governed, auditable Cognitive Loop Runtime; not unbounded tool autonomy

## 1. 目标与范围

Phase 3.7.5 将已冻结模块串成一个受控、可终止、可审计的完整行动循环：

```text
JuliaContext
    ↓
Cognitive Reasoning
    ↓
ActionIntentProposal
    ↓
ActionGovernanceLayer
    ↓
GovernedActionDecision
    ↓
ActionExecutor
    ↓
CapabilityExecutionTrace
    ↓
ActionReflectionReview
    ↓
MemoryCandidate / StateProposal
    ↓
Governance
    ↓
Context Mutation
    ↓
Next JuliaContext
```

本阶段的 “Autonomous” 定义为 Runtime 治理下的有限认知行动循环，不是让 Provider/LLM 无限循环调用工具。

## 2. 冻结边界

### 2.1 每轮一个受治理动作

第一版只允许：

```text
one Intent
↓
one Governance
↓
one Capability
↓
one Reflection
↓
one Continuation Decision
```

不支持模型一次生成长工具链。

### 2.2 Runtime 决定是否继续

Provider 只能影响 ActionPlanner 的输入，不决定 loop continuation。

```text
Action Outcome
    ↓
LoopContinuationPolicy
    ↓
CONTINUE / COMPLETE / ASK_USER / PAUSE / ABORT
```

### 2.3 硬终止条件

默认冻结参数：

```text
max_steps = 5
max_failures = 2
max_consecutive_same_intent = 2
max_total_risk_score = 2.0
```

终止触发：

- user confirmation required
- capability failure
- invariant violation
- governance reject
- context quality below threshold
- step limit
- duplicate intent guard
- risk limit

### 2.4 防止自我强化错误

冻结约束：

```text
Execution failure ≠ world fact
```

失败只能产生：

```text
capability_gap
temporary_execution_failure
insufficient_evidence
```

不得直接产生：

```text
semantic_memory
project_fact
relationship_fact
```

## 3. 变更文件清单

| 文件路径 | 变更类型 | 摘要 |
| --- | --- | --- |
| `runtime/action/loop/__init__.py` | 新增 | loop v2 API 导出 |
| `runtime/action/loop/cognitive_loop.py` | 新增 | CognitiveLoopRuntime / CognitiveLoopResult |
| `runtime/action/loop/loop_context.py` | 新增 | Context Mutation adapter boundary |
| `runtime/action/loop/loop_state.py` | 新增 | CognitiveLoopState 与硬限制状态 |
| `runtime/action/loop/continuation_policy.py` | 新增 | Runtime continuation / termination policy |
| `runtime/action/loop/termination_reason.py` | 新增 | 终止原因枚举 |
| `runtime/action/loop/loop_trace.py` | 新增 | LoopStepTrace / CognitiveLoopTrace |
| `runtime/action/__init__.py` | 修改 | 导出 CognitiveLoopRuntime v2 对象 |
| `tests/test_phase375_cognitive_loop_runtime.py` | 新增 | Phase 3.7.5 v2 验收测试 |
| `docs/project_control/reports/phase-3.7.5-autonomous-cognitive-loop.md` | 修改 | 阶段报告更新 |

## 4. 新增核心对象

### CognitiveLoopState

```python
@dataclass(frozen=True)
class CognitiveLoopState:
    loop_id: str
    status: str
    current_step: int
    max_steps: int
    completed_actions: list[str]
    failed_actions: list[str]
    pending_confirmation: bool
    termination_reason: str | None
```

### LoopStepTrace

```python
@dataclass(frozen=True)
class LoopStepTrace:
    step: int
    intent_id: str | None
    governance_decision: str
    capability: str | None
    execution_status: str
    reflection_status: str
    continuation_decision: str
```

### LoopContinuationPolicy

Allowed decisions:

```text
CONTINUE
COMPLETE
ASK_USER
PAUSE
ABORT
```

Priority:

```text
Invariant violation -> ABORT
Governance reject -> ABORT
Governance ask -> ASK_USER
Execution failure -> PAUSE / CONTINUE according to limits
Goal satisfied -> COMPLETE
Step limit reached -> PAUSE
```

### CognitiveLoopRuntime

`CognitiveLoopRuntime.run(context)` 串联：

```text
ActionPlanner
ActionGovernanceLayer
ActionExecutor.execute_governed
ActionReflectionEngine.reflect_with_governance
LoopContinuationPolicy
ContextMutationAdapter
```

## 5. 3.7.5 路线冻结

当前路线正式冻结为：

```text
Phase 3.7.5.1 Loop State + Trace
Phase 3.7.5.2 Continuation / Termination Policy
Phase 3.7.5.3 Governed Single-Step Loop
Phase 3.7.5.4 Multi-Step Read-Only Loop
Phase 3.7.5.5 Loop Safety & Self-Reinforcement Guard
Phase 3.7.5.6 Autonomous Loop Integration Benchmark
```

## 6. 验收结果

| TC | Description | Status |
|---|---|---|
| TC-375-001 | Single Governed Loop | PASS |
| TC-375-002 | Ask Stops Loop | PASS |
| TC-375-003 | Reject Stops Loop | PASS |
| TC-375-004 | Step Limit | PASS |
| TC-375-005 | Failure Does Not Become Fact | PASS |
| TC-375-006 | Duplicate Intent Guard | PASS |
| TC-375-007 | Full Auditability | PASS |
| TC-375-008 | Context OS Integration | PASS |

Legacy Phase 3.7.5 single-cycle API remains compatible for Phase 3.7.6 / 3.7.7.

## 7. 验证命令与结果

### 7.1 Phase 3.7.5 v2 Targeted

```bash
python3 -m unittest -v tests.test_phase375_cognitive_loop_runtime
```

```text
Ran 8 tests in 0.054s
OK
```

### 7.2 Phase 3.7.5 Legacy + Trace Activation Compatibility

```bash
python3 -m unittest -v \
  tests.test_phase375_autonomous_cognitive_loop \
  tests.test_phase375_cognitive_loop_runtime \
  tests.test_phase376_action_loop_trace_integration \
  tests.test_phase377_controlled_action_loop_activation
```

```text
Ran 24 tests in 3.350s
OK
```

### 7.3 Phase 3.7.2 -> 3.7.5 Boundary Regression

```bash
python3 -m unittest -v \
  tests.test_phase372_action_policy_governance_layer \
  tests.test_phase373_capability_invocation_lifecycle \
  tests.test_phase374_action_reflection_memory_integration \
  tests.test_phase375_autonomous_cognitive_loop \
  tests.test_phase375_cognitive_loop_runtime \
  tests.test_phase361015_context_os_integration_benchmark
```

```text
Ran 50 tests in 0.101s
OK
```

### 7.4 Full Regression

```bash
python3 -m unittest discover -s tests
```

```text
Ran 429 tests in 46.535s
OK
```

## 8. 架构合规性

### Runtime Authority

PASS。Continuation decision 由 `LoopContinuationPolicy` 产生，Provider 不决定继续。

### Governance Boundary

PASS。Capability 只能从 `GovernedActionDecision` 进入 `ActionExecutor.execute_governed()`。

### Single Action Per Step

PASS。每个 loop step 只处理一个 ActionIntent。

### Auditability

PASS。每步均包含：

```text
intent_trace
governance_trace
execution_trace
reflection_trace
continuation_trace
```

### Memory Safety

PASS。Execution failure 不升级为 semantic/project/relationship fact；只形成 gap/failure evidence 与 candidate。

### Context OS Integration Boundary

PASS。每步结束均通过 `ContextMutationAdapter` 边界，真实 Context OS mutation 可在该接口接入；测试路径使用 identity adapter 保持安全。

## 9. 风险与限制

| 风险 | 状态 | 说明 |
| --- | --- | --- |
| ContextMutationAdapter 当前为 identity 默认实现 | Accepted | 真实 Context OS mutation 留给集成阶段接入 |
| Multi-step loop 默认会在 success 后 COMPLETE | Intentional | 第一版防止无意义继续；测试可注入 policy 验证多步只读循环 |
| failure confidence 尚未评分 | Pending | 对应 NOTE-374-001 / 后续 ReflectionConfidence |
| Capability Registry 尚未接入 continuation | Pending | 对应 NOTE-373-001 |

## 10. 阶段结论

Phase 3.7.5 当前达到本地验收标准：

```text
Loop State + Trace implemented
Continuation / Termination Policy implemented
Governed Single-Step Loop implemented
Multi-Step Read-Only Loop boundary verified
Loop Safety & Self-Reinforcement Guard verified
Autonomous Loop Integration Benchmark passed
Legacy autonomous loop path preserved
```

建议状态：

```text
READY FOR REVIEW
```

## 11. 下一阶段建议

建议进入 Phase 3.7.6 / 3.7.7 后续收口时，逐步将 conversation action loop trace 从 legacy `AutonomousCognitiveLoop` 迁移到 v2 `CognitiveLoopRuntime`，并保持默认关闭、显式启用、只读优先。
