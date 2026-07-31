# Phase 3.7.2 — Action Governance Runtime Report

Date: 2026-07-27
Status: APPROVED / FROZEN
Scope: ActionIntent governance only; no capability execution

## Objective

Establish Julia Runtime's authority boundary for actions. ActionIntent can now be evaluated by Runtime-owned policy into:

```text
allow / ask / reject
```

This phase does not execute tools or capabilities.

## Implemented Modules

```text
runtime/action/action_decision.py
runtime/action/action_policy.py
runtime/action/__init__.py
```

## Core Objects

### ActionDecision

```python
@dataclass(frozen=True)
class ActionDecision:
    decision: str
    intent_type: str
    risk_level: str
    allowed_capability: str | None
    reason: str
    confidence: float
    evidence: list[str]
    required_confirmation: bool = False
    execution_id: str | None = None
```

### ActionPolicy

Policy behavior:

| Condition | Decision |
|---|---|
| low risk + known capability | allow |
| medium risk | ask |
| unknown capability | ask |
| high/critical risk | reject |
| prohibited capability | reject |
| low confidence | reject |
| no intent | reject |

Known capabilities v1:

```text
code_inspection
planning
diagnostics
read_context
```

Ask capabilities v1:

```text
code_modification
file_write
external_api
```

Prohibited capabilities v1:

```text
destructive_operation
credential_access
external_send
production_mutation
```

## Acceptance Results

| TC | Description | Status |
|---|---|---|
| TC-PHASE372-001 | low risk known capability allowed | PASS |
| TC-PHASE372-002 | medium risk requires confirmation | PASS |
| TC-PHASE372-003 | high risk rejected | PASS |
| TC-PHASE372-004 | low confidence rejected | PASS |
| TC-PHASE372-005 | unknown capability requires confirmation | PASS |
| TC-PHASE372-006 | runtime isolation | PASS |
| TC-PHASE372-007 | decision is not execution | PASS |
| TC-PHASE372-008 | explainability fields required | PASS |

## Verification

Targeted command:

```bash
python3 -m unittest tests.test_phase372_action_governance
```

Result:

```text
Ran 8 tests in 0.001s
OK
```

Full regression:

```bash
python3 -m unittest discover -s tests
```

Result:

```text
Ran 241 tests in 10.620s
OK
```

## Runtime Isolation

ActionDecision is verified not to contain:

```text
provider
backend
deepseek
model
latency
tts
stt
session_id
turn_id
```

## Execution Boundary

Even when decision is `allow`, Phase 3.7.2 does not execute anything.

```text
execution_id = None
```

Capability invocation is deferred to Phase 3.7.3.

## Final Decision

Decision: APPROVED WITH NOTES

Status: APPROVED / FROZEN

Freeze Note: Action Governance Boundary Established. Execution Authority Remains Runtime Controlled. Capability Invocation Requires Explicit Governance Approval.

Phase 3.7.2 is complete.

Julia can now decide whether an intended action is allowed, needs confirmation, or should be rejected, while preserving Runtime authority over actions.

Next phase:

```text
Phase 3.7.3 — Capability Invocation Lifecycle
```
