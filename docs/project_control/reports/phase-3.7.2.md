# Phase 3.7.2 — Action Policy Governance

## 1. 目标与范围

本阶段建立 Julia Controlled Agency 的行动边界层。

核心定义：

```text
ActionIntent
    ↓
Risk Evaluation
    ↓
Permission Policy
    ↓
allow / require_confirmation / reject
```

阶段边界：

- 接收 ActionIntent；
- 评估 risk；
- 接入 InvariantGuard；
- 输出 governed decision；
- 生成 explainable policy trace；
- 不执行 capability；
- 不调用 tool / shell / API；
- 不进入 Agent Loop。

冻结原则：

```text
ActionIntent != Execution
PolicyDecision != Execution
GovernedActionDecision.executable == False
```

## 2. 变更文件清单

| 文件路径 | 变更类型 | 摘要 |
| --- | --- | --- |
| `runtime/action/action_governance.py` | 新增 | ActionRiskEvaluator / ActionGovernanceLayer / GovernedActionDecision |
| `runtime/action/__init__.py` | 修改 | 导出 governance API |
| `tests/test_phase372_action_policy_governance_layer.py` | 新增 | Context OS aware Action Governance 验收测试 |
| `docs/project_control/reports/phase-3.7.2.md` | 新增 | 阶段报告 |

## 3. 新增核心对象

| 对象 | 职责 |
| --- | --- |
| `ActionRiskEvaluation` | risk_level / risk_score / reasons / protected_context |
| `ActionRiskEvaluator` | 评估 destructive / protected / capability / confidence 风险 |
| `ActionPolicyTrace` | intent/capability/risk/invariant/decision/evidence trace |
| `GovernedActionDecision` | ActionDecision + risk + trace，明确 `executable=False` |
| `ActionGovernanceLayer` | ActionIntent -> governed allow/ask/reject |

## 4. 冻结决策语义

| 输入 | 输出 |
| --- | --- |
| low risk + known capability | `allow` |
| medium risk / write capability | `ask` / confirmation required |
| destructive language | `reject` |
| protected identity/persona/relationship mutation | `reject` |
| no intent | `reject` |

## 5. 架构链路

```text
ActionIntentLayer
    ↓
ActionGovernanceLayer
    ↓
ActionRiskEvaluator
    ↓
InvariantGuard
    ↓
ActionPolicy
    ↓
GovernedActionDecision
    ↓
Capability Runtime later
```

本阶段没有 capability invocation。

## 6. 验收点

### 6.1 Low Risk Allow

PASS。

低风险已知 capability 输出 `allow`，但 `executable=False`。

### 6.2 Medium Risk Ask

PASS。

`code_modification` / write capability 输出 `ask` 并要求 confirmation。

### 6.3 High Risk Reject

PASS。

即使 intent 声称 low risk，只要 goal 中出现 destructive language，也会提升为 high risk 并 reject。

### 6.4 Invariant Guard Reject

PASS。

identity / relationship / persona 等 protected context 由 InvariantGuard 拦截。

### 6.5 Explainable Trace

PASS。

`GovernedActionDecision.to_dict()` 包含：

- decision
- risk
- trace
- executable

### 6.6 No Execution Boundary

PASS。

本阶段只返回 policy decision，不生成 CapabilityRequest，不调用 router。

## 7. 验证命令与结果

### 7.1 Targeted Governance Tests

命令：

```bash
python3 -m unittest -v tests.test_phase372_action_policy_governance_layer tests.test_phase372_action_governance tests.test_phase371_action_intent_layer_context_os
```

结果：

```text
Ran 21 tests in 0.067s
OK
```

### 7.2 Full Action / Context Regression

命令：

```bash
python3 -m unittest -v \
  tests.test_phase372_action_policy_governance_layer \
  tests.test_phase372_action_governance \
  tests.test_phase371_action_intent_layer_context_os \
  tests.test_phase37_action_intent \
  tests.test_phase373_capability_invocation_lifecycle \
  tests.test_phase361015_context_os_integration_benchmark
```

结果：

```text
Ran 41 tests in 0.071s
OK
```

覆盖：

- Phase 3.7.2 GovernanceLayer：7/7 PASS
- Legacy Phase 3.7.2 ActionPolicy：8/8 PASS
- Phase 3.7.1 Context OS Action Intent Layer：6/6 PASS
- Legacy Phase 3.7.1 Action Intent：6/6 PASS
- Phase 3.7.3 Capability Invocation Lifecycle：7/7 PASS
- Phase 3.6.10.15 Context OS Integration Benchmark：7/7 PASS

## 8. 架构合规性

### 8.1 Action Boundary

PASS。

```text
Policy decides. It does not execute.
```

### 8.2 Runtime Authority

PASS。

Governance 不信任 intent 自报 risk，会重新评估 destructive / protected / capability / confidence 风险。

### 8.3 Invariant Integration

PASS。

ActionGovernanceLayer 接入 InvariantGuard，防止 action intent 越过 Context OS 核心不变量。

## 9. 风险与限制

| 风险 | 状态 | 说明 |
| --- | --- | --- |
| 当前 risk evaluator 为 deterministic heuristic | Accepted | 本阶段先冻结 governance boundary，后续可升级 policy engine |
| protected target 匹配为最小规则 | Accepted | 已避免 benign `julia_agent` 被 identity invariant 误杀 |
| confirmation 仍为 decision 字段，不含 UI flow | Intentional | 用户确认流程留给 execution/capability 层 |
| 未接 Action Conflict Resolver | Pending | 已在 Phase 3.7.1 NOTE-371-002 记录 |

## 10. 阶段结论

Phase 3.7.2 当前达到本地验收标准：

```text
ActionGovernanceLayer implemented
ActionRiskEvaluator implemented
ActionPolicyTrace implemented
GovernedActionDecision implemented
allow / ask / reject semantics verified
InvariantGuard integration verified
No-execution boundary verified
Legacy ActionPolicy compatibility verified
Capability lifecycle regression verified
Context OS benchmark regression verified
```

冻结状态：

```text
Decision: APPROVED WITH NOTES
Status: APPROVED / FROZEN
Freeze Note: Action Governance Boundary Established.
Execution Authority Remains Runtime Controlled.
Capability Invocation Requires Explicit Governance Approval.
```


## 11. 冻结 Notes

### NOTE-372-001 — Action Risk Model 升级

当前 `ActionIntent -> RiskEvaluator -> allow / ask / reject` 已正确冻结。后续阶段应将规则型 evaluator 升级为可解释评分模型，例如：

```json
{
  "risk_level": "medium",
  "score": 0.63,
  "factors": [
    "external_side_effect",
    "destructive_language",
    "missing_confirmation"
  ]
}
```

目的：为 Phase 3.7.5 Autonomous Cognitive Loop 提供“为什么需要人工确认”的可审计解释，而不是只提供禁止/允许结果。

### NOTE-372-002 — Governance Decision 是 Capability Runtime 唯一入口

冻结边界：

```text
ActionIntent
    ↓
Action Governance
    ↓
Capability Runtime
```

未来不得引入绕过链路：

```text
LLM -> Capability
Reflection -> Tool Execute
```

保持：

```text
LLM = Interpreter
Runtime = Authority
Capability = Executor
```

### NOTE-372-003 — Governance Memory 不得进入 Persona Memory

后续可以引入 Action Governance History，用于记录：

- 某类操作经常需要确认；
- Tony 偏好的授权方式；
- 项目安全规则。

允许分类：

```text
PROJECT_CONSTRAINT
BEHAVIOR_PREFERENCE
ACTION_POLICY_HISTORY
```

禁止写入：

```text
CORE_IDENTITY
RELATIONSHIP_FOUNDATION
```

目的：避免行动经验污染 Julia 身份与关系基础。

### NOTE-372-004 — 下一阶段重点

Phase 3.7.3 — Capability Invocation Lifecycle 应继续冻结以下生命周期：

```text
GovernedActionDecision
        ↓
CapabilityRequest
        ↓
CapabilityValidation
        ↓
Execution
        ↓
ExecutionTrace
        ↓
ActionReflection
```

重点验证：

- Capability 是否只接受 Runtime 授权；
- Execution 是否可审计；
- Failure 是否进入 Reflection；
- Execution result 是否污染 Memory。

## 12. 下一阶段建议

```text
Phase 3.7.3 — Capability Invocation Lifecycle
```

目标：在 governance allow 后，才进入 capability invocation lifecycle。

继续保持：

```text
Action Governance Decision is mandatory before Capability Invocation.
```

```text
Intent -> Governance -> Capability Permission -> Execution -> Reflection
```
