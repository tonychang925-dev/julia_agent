# Phase 3.7.1 — Action Intent Layer

## 1. 目标与范围

本阶段是从 Cognitive Runtime 进入 Controlled Agency 的第一步。

核心定义：

```text
Julia 可以形成“下一步做什么”的 ActionIntent，
但 ActionIntent 不是命令、不是工具调用、不是执行授权。
```

阶段边界：

- 从 Context OS 重建的 `JuliaContext` 中推导行动意图；
- 保留 evidence / source trace；
- 保持 provider independence；
- 接入 Invariant Guard；
- 不执行 capability；
- 不调用 shell / API / tool；
- 不修改 runtime state；
- 不进入 Autonomous Agent Loop。

冻结原则：

```text
Cognitive State
    ↓
Action Intent
    ↓
Policy Governance
    ↓
Capability Runtime
```

本阶段只实现第一层：Action Intent。

## 2. 变更文件清单

| 文件路径 | 变更类型 | 摘要 |
| --- | --- | --- |
| `runtime/action/action_intent_layer.py` | 新增 | Context OS JuliaContext -> ActionIntentProposal |
| `runtime/action/__init__.py` | 修改 | 导出 ActionIntentLayer / ActionIntentProposal / ActionIntentTrace |
| `tests/test_phase371_action_intent_layer_context_os.py` | 新增 | Context OS Action Intent Layer 验收测试 |
| `docs/project_control/reports/phase-3.7.1.md` | 新增 | 阶段报告 |

## 3. 新增核心对象

| 对象 | 职责 |
| --- | --- |
| `ActionIntentTrace` | 记录 context sources / evidence refs / open loops / reason |
| `ActionIntentProposal` | 包装 ActionIntent，明确 `executable=False` |
| `ActionIntentLayer` | 从 Context OS `JuliaContext` 推导 ActionIntent |

## 4. 架构链路

```text
Session Resurrection
    ↓
JuliaContext Reconstruction
    ↓
Invariant Guard
    ↓
ActionIntentLayer
    ↓
ActionIntentProposal
    ↓
Action Policy Governance
```

关键边界：

```text
ActionIntentLayer != ActionExecutor
ActionIntent != Command
ActionIntentProposal.executable == False
```

## 5. 验收点

### 5.1 Restored Context -> ActionIntent

PASS。

从 Context OS `JuliaContext` 中读取：

- current_task；
- open_loops；
- next_actions；
- evidence_refs；
- sources。

生成 ActionIntent，但不执行。

### 5.2 Traceability

PASS。

`ActionIntentTrace` 保留：

- `context_sources`
- `evidence_refs`
- `open_loops`
- `reason`

用于解释 Julia 为什么认为应该进行某个 action。

### 5.3 Provider Independence

PASS。

同一个 `JuliaContext` 在 DeepSeek / Claude / GPT provider metadata 下生成相同 intent。

### 5.4 No Actionable Context -> No Intent

PASS。

当没有 current_task / next_actions / open_loops 时，不生成 action intent。

### 5.5 Intent 不是命令

PASS。

ActionIntent 不包含 shell command，也不包含 provider/runtime metadata。

### 5.6 Invariant Guard 接入

PASS。

ActionIntentLayer 在 pre-turn 阶段接入 InvariantGuard，防止 identity drift context 进入 action intent 推导。

## 6. 验证命令与结果

### 6.1 Phase 3.7.1 + Context OS Benchmark

命令：

```bash
python3 -m unittest -v tests.test_phase371_action_intent_layer_context_os tests.test_phase37_action_intent tests.test_phase361015_context_os_integration_benchmark
```

结果：

```text
Ran 19 tests in 0.103s
OK
```

### 6.2 Phase 3.7.1 + Governance / Capability / Context OS Regression

命令：

```bash
python3 -m unittest -v \
  tests.test_phase371_action_intent_layer_context_os \
  tests.test_phase37_action_intent \
  tests.test_phase372_action_governance \
  tests.test_phase373_capability_invocation_lifecycle \
  tests.test_phase361015_context_os_integration_benchmark
```

结果：

```text
Ran 34 tests in 0.123s
OK
```

覆盖：

- Phase 3.7.1 Context OS Action Intent Layer：6/6 PASS
- Legacy Phase 3.7.1 Action Intent：6/6 PASS
- Phase 3.7.2 Action Governance：8/8 PASS
- Phase 3.7.3 Capability Invocation Lifecycle：7/7 PASS
- Phase 3.6.10.15 Context OS Integration Benchmark：7/7 PASS

## 7. 架构合规性

### 7.1 Controlled Agency 起点正确

PASS。

本阶段只形成 intent，不执行 action。

```text
Julia can decide what to consider doing next.
Julia cannot execute from this layer.
```

### 7.2 Runtime Authority 保持

PASS。

ActionIntentLayer 使用 Context OS JuliaContext，而不是 provider response 直接生成 action。

```text
Runtime Cognitive State -> Intent
Provider Output         -> Not Authority
```

### 7.3 与后续阶段兼容

PASS。

输出 `ActionIntent` 仍兼容已有：

- `ActionPolicy`
- `ActionExecutor`
- Capability Runtime

## 8. 风险与限制

| 风险 | 状态 | 说明 |
| --- | --- | --- |
| 当前 intent 推导为 deterministic signal matching | Accepted | 本阶段先冻结边界，不引入 LLM planner |
| Medium-risk implementation intent 仍需 Governance | Intentional | 由 3.7.2 Action Policy Governance 决定 ask/allow/reject |
| 未接真实 autonomous loop | Intentional | Autonomous Loop 留到 3.7.5 |
| InvariantGuard 当前只 pre-turn check context | Accepted | 后续 action policy 可加入 post-intent invariant check |

## 9. 阶段结论

Phase 3.7.1 当前达到本地验收标准：

```text
Context OS Action Intent Layer implemented
ActionIntentTrace implemented
ActionIntentProposal implemented
Provider Independence verified
No-command boundary verified
No-execution boundary verified
Invariant pre-turn guard integrated
Governance/capability regressions verified
Context OS benchmark regression verified
```

建议状态：

```text
READY FOR REVIEW
```

## 10. 下一阶段建议

```text
Phase 3.7.2 — Action Policy Governance
```

目标：将 ActionIntent 进入 policy decision，明确：

```text
allow / ask / reject
```

并继续保持：

```text
ActionIntent != Execution
PolicyDecision != Execution
```


---

## 11. 验收决策

**Decision:** APPROVED WITH NOTES  
**Status:** APPROVED / FROZEN  
**Accepted At:** 2026-07-29 Asia/Shanghai  
**Freeze Note:** Action Intent Architecture Accepted, Execution Authority Boundary Preserved, Capability Execution Deferred to Governance Layer.

Phase 3.7.1 — Action Intent Layer 已验收通过并冻结。

## 12. 核心验收结论

| 验收项 | 结论 |
| --- | --- |
| ActionIntentLayer / Proposal / Trace | PASS |
| Context OS JuliaContext -> ActionIntent | PASS |
| source refs / evidence refs / open loops trace | PASS |
| `ActionIntentProposal.executable == False` | PASS |
| 不执行 capability / shell / tool / API | PASS |
| Execution Authority Boundary | PASS |
| Regression Tests | PASS |

测试覆盖冻结：

```text
Phase 3.7.1 Context OS Action Intent Layer：6/6 PASS
Legacy Phase 3.7.1 Action Intent：6/6 PASS
Phase 3.7.2 Action Governance：8/8 PASS
Phase 3.7.3 Capability Invocation Lifecycle：7/7 PASS
Phase 3.6.10.15 Context OS Integration Benchmark：7/7 PASS

Ran 34 tests
OK
```

## 13. 验收评价

### 13.1 最大优点：没有提前进入 Agent Loop

冻结判断：本阶段保持正确方向，没有把 LLM output 直接转成 tool call 或 execution。

禁止架构：

```text
LLM
    ↓
Tool Call
    ↓
Execute
```

当前冻结架构：

```text
Context OS
    ↓
Cognitive Reasoning
    ↓
Action Intent
    ↓
Action Governance
    ↓
Capability Runtime
    ↓
Execution
```

这保持了此前冻结原则：

```text
LLM = proposes
Runtime = authorizes
Capability = executes
Reflection = learns
```

## 14. Hardening Notes

以下 Notes 非阻塞项，进入后续 Action Runtime hardening。

### NOTE-371-001 Action Intent Confidence Calibration

当前 ActionIntentProposal 已经解决“想做什么”。

下一步需要更细粒度解释“为什么相信应该做这个”。

建议增加：

```python
IntentConfidence(
    context_alignment=0.95,
    evidence_support=0.90,
    user_explicitness=0.98,
    risk_estimation=0.85,
)
```

示例输出：

```json
{
  "intent_type": "inspect_repository",
  "confidence": 0.93,
  "evidence": ["explicit_user_request", "technical_context"]
}
```

### NOTE-371-002 Action Intent 与 Conflict Resolver 双向连接

未来建议链路：

```text
Context OS
    ↓
Action Intent
    ↓
Action Conflict Resolver
    ↓
Action Policy
```

场景：

```text
用户：删除这个文件
Context: production repository protected
```

此类冲突应在进入 capability 前裁决。

### NOTE-371-003 增加完整 Action Trace

当前已有 `ActionIntentTrace`。

未来应扩展为完整链：

```text
Intent Trace
    ↓
Policy Decision Trace
    ↓
Capability Execution Trace
    ↓
Reflection Trace
```

目标：Phase 3.7.5 Autonomous Cognitive Loop 可审计 Julia 为什么决定做某件事。

## 15. 当前 Julia 架构状态

```text
Cognitive Runtime        ✅
Context OS               ✅
Memory Governance        ✅
Context Authority        ✅
Action Intention         ✅
```

## 16. 下一阶段

建议进入：

```text
Phase 3.7.2 — Action Policy Governance
```

重点不是执行工具，而是建立行动边界：

```text
ActionIntent
    ↓
Risk Evaluation
    ↓
Permission Policy
    ↓
allow / require_confirmation / reject
```

保持节奏：先建立 Julia 的行动边界，再给她行动能力。
