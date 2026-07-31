# Phase 3.7.6 — E2E Beta Benchmark Dry-Run Report

Date: 2026-07-29
Decision: ACCEPT
Status: APPROVED / FROZEN
Execution Mode: dry-run
Rerun After: Phase 3.7.6.1 Bridge Action Governance Alignment

## Summary

Phase 3.7.6 E2E Beta dry-run was rerun after the P0 bridge governance misalignment fix.

The previous blocker is resolved:

```text
DirectLLMBridge now routes production-like action traces through:
ActionIntentProposal
  ↓
ActionGovernanceLayer
  ↓
GovernedActionDecision
  ↓
ActionExecutor.execute_governed()
```

Beta dry-run now validates:

- cross-session archive continuity
- evidence-grounded recall with Tony archive provenance
- engineering / emotional cognitive scope routing
- Memory Router isolation
- Context Cache hit/miss with dynamic evidence excluded
- ask/reject blocking before capability execution
- failure reflection without fact formation or memory persistence
- full audit trace across context/provenance/cache/action layers

## Commands Executed

### UT / IT Baseline

```bash
python3 -m unittest -v \
  tests.test_phase3751_context_provenance_runtime \
  tests.test_phase3752_memory_router \
  tests.test_phase3753_context_cache \
  tests.test_phase372_action_policy_governance_layer \
  tests.test_phase373_capability_invocation_lifecycle \
  tests.test_phase374_action_reflection_memory_integration
```

Result:

```text
Ran 52 tests in 7.242s
OK
```

### E2E Alpha/Beta Dry-run Baseline

```bash
python3 -m unittest -v \
  tests.test_e2e_alpha_input_and_routing_fixes \
  tests.test_e2e_alpha_conversation_continuity_guard \
  tests.test_action_e2e_alpha_runtime \
  tests.test_phase361015_context_os_integration_benchmark \
  tests.test_phase369_context_assembly_runtime
```

Result:

```text
Ran 22 tests in 7.756s
OK
```

### CLI Echo Dry-run

```bash
python3 -m runtime.conversation_runtime.cli \
  --text-input \
  --text-input-turns 1 \
  --backend echo \
  --realtime-speech \
  --conversation-tts-mode dry_run \
  --enable-action-loop \
  --trace \
  --text-file /tmp/julia_e2e_beta_turn1.txt
```

Result:

```text
state trace: PASS
input file integrity: PASS
TTS dry-run: PASS
latency: PASS
bridge_first_chunk_ms=6
total_response_ms=13
```

Note:

```text
Echo backend remains useful for CLI state/input/TTS/latency smoke testing,
but Context Governance Beta is validated with DirectLLMBridge + CaptureProvider.
```

### Phase 3.7.6 Beta Targeted

```bash
python3 -m unittest -v tests.test_phase376_e2e_beta_benchmark
```

Result:

```text
Ran 10 tests in 8.043s
OK
```

### Context Governance + Action Boundary Regression

```bash
python3 -m unittest -v \
  tests.test_phase376_e2e_beta_benchmark \
  tests.test_phase3761_bridge_action_governance_alignment \
  tests.test_phase376_action_loop_trace_integration \
  tests.test_phase377_controlled_action_loop_activation \
  tests.test_phase372_action_policy_governance_layer \
  tests.test_phase373_capability_invocation_lifecycle \
  tests.test_phase374_action_reflection_memory_integration \
  tests.test_action_e2e_alpha_runtime \
  tests.test_phase3752_memory_router \
  tests.test_phase3753_context_cache
```

Result:

```text
Ran 72 tests in 33.571s
OK
```

### Full Regression

```bash
python3 -m unittest discover -s tests -v
```

Result:

```text
Ran 481 tests in 119.140s
OK
```

## Beta Test Case Results

| ID | Result | Notes |
| --- | --- | --- |
| TC-376-BETA-001 | PASS | Single-turn dry-run trace includes Context Assembly, cache metadata, and governed action trace |
| TC-376-BETA-002 | PASS | Cross-session archive recall hits Tony source |
| TC-376-BETA-003 | PASS | Recall evidence has archive provenance; no old SSO / identity-token drift detected |
| TC-376-BETA-004 | PASS | Engineering/planning scope allows technical/project memory and blocks intimacy/private classes |
| TC-376-BETA-005 | PASS | Emotional scope routes relationship continuity when emotional mode is active |
| TC-376-BETA-006 | PASS | Same-session cache hit observed; semantic evidence / routes / action governance remain excluded from cache |
| TC-376-BETA-007 | PASS | write/save request → `modify_resource` + `file_write` + `ask`; no execution |
| TC-376-BETA-008 | PASS | identity mutation → explicit `identity_mutation` + governance reject; no execution |
| TC-376-BETA-009 | PASS | capability failure produces `capability_gap`; reflection persisted=false; no fact memory |
| TC-376-BETA-010 | PASS | Trace contains context/provenance/router/cache/action governance audit fields |
| TC-376-BETA-011 | PASS WITH NOTES | Echo CLI latency passes; provider latency not measured in this deterministic dry-run |
| TC-376-BETA-012 | PASS | Full regression 481 OK |

## Resolved Prior Blockers

### BLOCKER-376-001 DirectLLMBridge action loop bypasses governed runtime entry

Resolved by Phase 3.7.6.1.

Current trace requires:

```json
{
  "action_path": "governed",
  "governance_layer": "ActionGovernanceLayer"
}
```

### BLOCKER-376-002 write/save misclassified as create_plan

Resolved.

Validated output:

```json
{
  "intent_type": "modify_resource",
  "required_capability": "file_write",
  "risk_level": "medium",
  "decision": "ask",
  "execution": null
}
```

### BLOCKER-376-003 identity mutation hidden as no_action

Resolved.

Validated output:

```json
{
  "intent_type": "identity_mutation",
  "risk_level": "critical",
  "decision": "reject",
  "execution": null
}
```

## Notes

### NOTE-376-001 Provider E2E remains separate from deterministic Beta gate

DeepSeek / real provider E2E should be executed as an environment-dependent provider validation pass.
It should not replace deterministic `CaptureProvider` governance testing.

### NOTE-376-002 Capability catalog remains a future improvement

Planning and code-inspection can still fail as capability gaps when no tool is registered.
This is acceptable in dry-run because failure reflects as `capability_gap` and is not persisted as fact.

### NOTE-376-003 CLI echo remains smoke-only

Echo validates text input, state transitions, TTS dry-run, and latency.
It does not validate full Context Governance metadata.

## Freeze Note

E2E Beta Governance Alignment Validated.

All Action Requests Enter the Governed Runtime Path.

Protected Mutations Are Blocked Before Capability Execution.

E2E Beta Dry-run Baseline Established.

Julia Runtime now demonstrates a deterministic, production-like, governed end-to-end path across Context OS, Provenance, Memory Router, Context Cache, Action Governance, Capability Invocation, and Action Reflection boundaries. Write/save and identity mutation safety boundaries hold under bridge-level E2E tests.

## Final Decision

Decision: ACCEPT

Status: APPROVED / FROZEN

## Freeze Notes

### NOTE-376-001 Governance Path remains the only action entry

Future Voice Runtime, CLI, Scheduler, Async Worker, Autonomous Loop, External API, and Provider tool-call paths must enter actions through:

```text
ActionIntent
  ↓
ActionGovernanceLayer
  ↓
GovernedActionDecision
  ↓
execute_governed()
```

No runtime component may call Capability directly.

### NOTE-376-002 ask requires Resume Lifecycle

Current ask behavior correctly stops at `execution=None`. Future resume must revalidate intent, capability, policy version, authorization expiry, and target consistency before execution.

### NOTE-376-003 CaptureProvider remains long-term CI harness

CaptureProvider should remain a deterministic provider harness for governance regression, invariant protection, capability routing, reflection boundary, provider migration, and autonomous loop safety.

### NOTE-376-004 Add negative-path coverage later

Future Beta/Autonomous stages should add unknown capability, expired governance decision, mismatched intent_id, replayed authorization, duplicate execution, invariant conflict, timeout, and partial execution failure cases.

Next:

```text
Phase 3.7.7 — Multi-provider Migration Test
```
