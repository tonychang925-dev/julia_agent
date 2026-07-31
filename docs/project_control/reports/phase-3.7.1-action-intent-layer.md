# Phase 3.7.1 — Action Intent Layer Report

Date: 2026-07-27
Status: PASS
Scope: Cognitive State → ActionIntent boundary only

## Objective

Establish Julia's first agency boundary: Julia Runtime can express what action may be worth taking, without executing anything.

This phase intentionally does not call Capability Runtime, shell, file APIs, external APIs, or tools.

## Frozen Authority Boundary

```text
LLM = proposes / interprets
Runtime = decides
Capability = executes
Reflection = learns
```

Phase 3.7.1 implements only:

```text
JuliaContext
  ↓
ActionPlanner
  ↓
ActionIntent | None
```

No execution authority is granted.

## Implemented Modules

```text
runtime/action/action_intent.py
runtime/action/action_context.py
runtime/action/action_planner.py
runtime/action/action_policy.py
runtime/action/action_decision.py
runtime/action/action_executor.py
runtime/action/action_reflection.py
runtime/action/__init__.py
```

### ActionIntent

```python
@dataclass(frozen=True)
class ActionIntent:
    intent_type: str
    goal: str
    target: str | None
    risk_level: str
    required_capability: str | None
    reason: str
    confidence: float
```

The object is a cognitive action proposal, not a command.

### ActionContext

```python
@dataclass(frozen=True)
class ActionContext:
    situation_context: SituationContext
    cognitive_mode: CognitiveModeContext
    conversation_context: ConversationContinuityContext
    relationship_context: RelationshipContext
    user_input: str
```

Provider/backend/model/latency/session metadata are excluded.

### ActionPlanner

First deterministic planner supports:

| Input class | Intent |
|---|---|
| technical inspection request | inspect_repository |
| bug / regression / latency issue | diagnose_issue |
| planning / next phase request | create_plan |
| emotional/private non-technical turn | None |

## Acceptance Results

| TC | Description | Status |
|---|---|---|
| TC-PHASE371-001 | Technical request → inspect_repository | PASS |
| TC-PHASE371-002 | Bug report → diagnose_issue | PASS |
| TC-PHASE371-003 | Planning request → create_plan | PASS |
| TC-PHASE371-004 | Emotional conversation → no_action | PASS |
| TC-PHASE371-005 | Runtime isolation | PASS |
| TC-PHASE371-006 | ActionIntent is not command | PASS |

## Verification

Targeted command:

```bash
python3 -m unittest tests.test_phase37_action_intent
```

Result:

```text
Ran 6 tests in 0.016s
OK
```

Full regression:

```bash
python3 -m unittest discover -s tests
```

Result:

```text
Ran 233 tests in 10.191s
OK
```

## Runtime Isolation Evidence

ActionIntent is verified not to contain:

```text
provider
backend
model
latency
tts
stt
session_id
turn_id
```

It is also verified not to contain shell/API command tokens:

```text
ls
cat
git
python
rm
curl
```

## Risk Notes

Current planner is intentionally deterministic and conservative.

Known limitations:

- no Action Governance yet,
- no Capability invocation yet,
- no action execution lifecycle yet,
- no action reflection yet.

These are deferred to Phase 3.7.2+.

## Final Decision

Phase 3.7.1 is complete.

Julia can now produce an explainable cognitive action intent while preserving runtime authority and execution separation.

Next phase:

```text
Phase 3.7.2 — Action Governance Runtime
```
