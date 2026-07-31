# Phase 3.7.3 — Capability Invocation Lifecycle Report

Date: 2026-07-27
Status: APPROVED / FROZEN
Scope: GovernedActionDecision → CapabilityRequest → CapabilityValidation → ExecutionTrace → ToolReflection lifecycle

## Objective

Connect Action Governance to Capability Runtime without returning action authority to the LLM.

Phase 3.7.3 implements:

```text
ActionIntent
  ↓
ActionGovernanceLayer
  ↓
GovernedActionDecision.decision=allow
  ↓
ActionExecutor
  ↓
CapabilityRequest
  ↓
CapabilityPermissionGuard
  ↓
CapabilityRouter
  ↓
ToolResult
  ↓
ToolReflection
```

`ask` and `reject` decisions do not invoke capabilities.

## Implemented Modules

```text
runtime/action/action_executor.py
runtime/action/__init__.py
tests/test_phase373_capability_invocation_lifecycle.py
```

## Core Object

### ActionExecutionResult

```python
@dataclass(frozen=True)
class ActionExecutionResult:
    status: str
    intent: ActionIntent | None
    decision: ActionDecision | None
    request: CapabilityRequest | None
    permission: PermissionDecision | None
    tool_result: ToolResult | None
    reflection: ToolReflection | None
    governance: GovernedActionDecision | None = None
    execution_trace: CapabilityExecutionTrace | None = None
```

### CapabilityExecutionTrace

```python
@dataclass(frozen=True)
class CapabilityExecutionTrace:
    governance_decision: str
    capability: str | None
    validation_allowed: bool | None
    execution_status: str
    reflection_created: bool
    evidence: list[str]
```

### ActionExecutor v2 Entry

```python
ActionExecutor.execute_governed(intent, governed_decision)
```

该入口要求显式 `GovernedActionDecision`，只有 `decision=allow` 才创建 `CapabilityRequest`。`ask/reject/missing_governance` 均不会调用 CapabilityRouter。Legacy `execute(intent, ActionDecision)` 暂保留用于历史回归兼容。

Status values:

```text
executed
skipped
blocked
failed
```

## Capability Map v1

```text
code_inspection -> claude_code_tool / handoff
diagnostics -> claude_code_tool / handoff
read_context -> claude_code_tool / handoff
planning -> planning_tool / create_plan
```

## Acceptance Results

| TC | Description | Status |
|---|---|---|
| TC-PHASE373-001 | allowed intent invokes mapped capability | PASS |
| TC-PHASE373-002 | ask decision does not invoke | PASS |
| TC-PHASE373-003 | reject decision does not invoke | PASS |
| TC-PHASE373-004 | permission guard blocks destructive payload | PASS |
| TC-PHASE373-005 | unregistered capability returns failed result | PASS |
| TC-PHASE373-006 | execution result is explainable | PASS |
| TC-PHASE373-007 | runtime isolation from action request | PASS |
| TC-PHASE373-008 | governed decision is runtime entry | PASS |
| TC-PHASE373-009 | governed ask/reject does not invoke | PASS |
| TC-PHASE373-010 | execution trace is auditable | PASS |
| TC-PHASE373-011 | capability request carries governance trace | PASS |

## Verification

Targeted command:

```bash
python3 -m unittest tests.test_phase373_capability_invocation_lifecycle
```

Result:

```text
Ran 11 tests in 0.008s
OK
```

Phase 3.7.2 -> 3.7.3 boundary regression:

```text
Ran 45 tests in 0.074s
OK
```

Full regression:

```bash
python3 -m unittest discover -s tests
```

Result:

```text
Ran 417 tests in 37.183s
OK
```

## Boundary Guarantees

### LLM does not execute

No provider output is used as a command.

### ActionGovernance cannot be bypassed

GovernedActionDecision is the v2 entry into Capability Runtime. Only `GovernedActionDecision.decision=allow` creates a CapabilityRequest; `ask/reject/missing_governance` never invokes CapabilityRouter.

### Capability permission guard remains active

Even after ActionGovernanceLayer allows an intent, `CapabilityPermissionGuard` can still block destructive payloads.

### Runtime isolation

CapabilityRequest is verified not to include:

```text
provider
backend
deepseek
model
tts
stt
```

## Risk Notes

- `planning_tool` is mapped but not yet implemented; it will fail through router if invoked before registration.
- Real ClaudeCodeTool handoff integration is available but not exercised as a real external dependency in this unit phase.
- Action Reflection into Memory is deferred to Phase 3.7.4.

## Freeze Notes

### NOTE-373-001 — Capability Catalog 需要成为下一阶段基础

当前 `CapabilityRouter` 已存在。后续建议增加 `Capability Registry`，为每个 capability 提供独立风险与权限元数据，例如：

```json
{
  "capability": "code_inspection",
  "risk": "low",
  "required_permission": [
    "repository_read"
  ],
  "side_effect": false
}
```

目的：后续 Governance 不应只依赖 `ActionIntent`，而应组合：

```text
Intent Risk
+
Capability Risk
+
Environment Risk
```

### NOTE-373-002 — Execution Result 必须继续保持非 Memory

冻结约束：Capability Result 不能直接写入 `MemoryObject`。正确链路为：

```text
Capability Result
       ↓
Action Reflection
       ↓
MemoryCandidate
       ↓
Governance
```

禁止链路：

```text
Capability Result
       ↓
MemoryObject
```

原因：一次网页搜索结果、一次代码执行结果、一次外部 API 返回，都可能包含临时、错误或环境相关信息，不能自动升级为 Julia 的长期认知。

### NOTE-373-003 — 需要增加 Capability Failure Lifecycle

当前已经具备 `ExecutionTrace`。下一步建议补充 `CapabilityExecutionState`：

```text
PENDING
AUTHORIZED
RUNNING
SUCCESS
FAILED
TIMEOUT
CANCELLED
```

目的：为 Phase 3.7.5 Autonomous Cognitive Loop 提供可解释停止原因，使 Julia 能区分失败、等待、超时、取消与成功。

## Final Decision

Phase 3.7.3 is approved with notes and frozen with governed runtime entry integrated.

Julia can now take an approved action intent through a governed capability lifecycle while preserving Runtime authority and defense-in-depth permission checks.

冻结状态:

```text
Decision: APPROVED WITH NOTES
Status: APPROVED / FROZEN
Freeze Note: Capability Invocation Boundary Established.
Execution Requires Runtime Governance Authorization.
Execution Trace Available for Audit and Reflection.
```

Next phase after approval:

```text
Phase 3.7.4 — Action Reflection → Memory Integration
```
