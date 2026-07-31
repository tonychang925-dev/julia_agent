# E2E Integration Alpha — Partial Pass Fix Report

Date: 2026-07-29
Status: READY FOR RETEST
Scope: input boundary, semantic continuity, action routing accuracy, audit flags

## Bug Summary

### Symptom

First E2E Alpha manual run produced PARTIAL PASS:

- Conversation Archive cross-process retrieval worked.
- Runtime voice/streaming/TTS trace worked.
- But semantic recall drifted from “single-step governed E2E” into Persona Package / cross-provider identity themes.
- Declarative state update “下一步要做 E2E，请记住” triggered `create_plan` capability and failed on missing `planning_tool`.
- CLI line input allowed accidental turn truncation when pasted across line breaks.
- Memory persistence state was implicit, not explicit in E2E trace.

### Root Cause

1. `runtime/conversation_runtime/cli.py` only accepted one `input()` line per turn; multi-line paste split the intended turn.
2. `runtime/action/action_planner.py` treated planning-related declarative statements as action requests.
3. `runtime/conversation_state/topic_tracker.py` and `unresolved_context.py` collapsed the concrete task into generic `Planning`.
4. `runtime/context_assembly/conflict_resolver.py` did not explicitly warn against old structured memory overriding recent Tony archive facts.
5. E2E trace lacked explicit `memory_persisted=false` flags.

## Fix Applied

### P0 — Text Input Boundary

Updated `runtime/conversation_runtime/cli.py`:

- Added `--text-file` for exact one-turn file input.
- Added `/multi ... /send` interactive multi-line submit mode.
- Preserves complete multi-line text in one turn.

### P0 — Declarative Statement Action Misroute

Updated `runtime/action/action_planner.py`:

- Added declarative-state guard for “请记住 / 下一步要做 / 重点是 / 已冻结”.
- Such statements now return `None` action intent unless explicit action verbs are present.

Expected:

```text
“下一步要做 E2E，请记住” -> no_action
```

### P1 — Current Task / Archive Authority Prominence

Updated `runtime/context_assembly/conflict_resolver.py`:

- Recent Tony-supplied project facts are active task anchors.
- Older structured-memory themes must not reinterpret current E2E scope.
- Archived Julia/assistant responses are unverified experience evidence.
- If Julia archive conflicts with Tony archive input, follow Tony input.

### P1 — Continuity Topic / Open Loop Precision

Updated:

- `runtime/conversation_state/topic_tracker.py`
- `runtime/conversation_state/unresolved_context.py`

Now preserves named topics:

```text
Phase 3.7.4
E2E Integration Alpha
Single-Step Governed E2E
Action Governance
Trace Verification
Memory Persistence Boundary
```

And creates E2E Alpha open loop with constraints:

```text
no long-term memory persistence
ask and reject must not execute
full trace required
```

### P1 — Explicit Memory Persistence Audit Flags

Updated:

- `runtime/action/e2e/action_e2e_trace.py`
- `runtime/action/e2e/action_e2e_runtime.py`

E2E trace now includes:

```json
{
  "memory_candidate_created": true,
  "memory_governance_prechecked": true,
  "memory_persisted": false
}
```

## Files Modified

```text
runtime/action/action_planner.py
runtime/action/e2e/action_e2e_runtime.py
runtime/action/e2e/action_e2e_trace.py
runtime/context_assembly/conflict_resolver.py
runtime/conversation_runtime/cli.py
runtime/conversation_state/topic_tracker.py
runtime/conversation_state/unresolved_context.py
tests/test_action_e2e_alpha_runtime.py
tests/test_e2e_alpha_conversation_continuity_guard.py
tests/test_e2e_alpha_input_and_routing_fixes.py
docs/project_control/reports/e2e-alpha-partial-pass-fix-report.md
```

## Tests Added / Updated

```text
tests/test_e2e_alpha_input_and_routing_fixes.py
  - E2E_ALPHA_008 declarative next-step remember does not trigger action
  - E2E_ALPHA_009 continuity keeps named E2E topics and constraints
  - E2E_ALPHA_010 text-file preserves complete turn
  - E2E_ALPHA_011 /multi + /send preserves complete turn

tests/test_e2e_alpha_conversation_continuity_guard.py
  - E2E_ALPHA_006 conflict prompt prioritizes Tony archive over Julia wrong answer
  - E2E_ALPHA_007 archive chunks mark Tony verified and Julia unverified

tests/test_action_e2e_alpha_runtime.py
  - E2E_ALPHA_005 now asserts memory_candidate_created, memory_governance_prechecked, memory_persisted=false
```

## Verification Evidence

### E2E Alpha Fix Regression

```bash
python3 -m unittest -v \
  tests.test_action_e2e_alpha_runtime \
  tests.test_e2e_alpha_input_and_routing_fixes \
  tests.test_e2e_alpha_conversation_continuity_guard
```

```text
Ran 11 tests in 1.842s
OK
```

### Phase 3.7.5 / Voice Trace Key Regression

```bash
python3 -m unittest -v \
  tests.test_phase375_autonomous_cognitive_loop \
  tests.test_phase375_cognitive_loop_runtime \
  tests.test_phase376_action_loop_trace_integration \
  tests.test_phase377_controlled_action_loop_activation \
  tests.test_phase371_action_intent_layer_context_os
```

```text
Ran 30 tests in 3.297s
OK
```

### Full Regression

```bash
python3 -m unittest discover -s tests
```

```text
Ran 440 tests in 58.260s
OK
```

## Retest Command

Preferred exact first-turn input:

```bash
cat > /tmp/e2e_alpha_turn1.txt <<'EOF'
Julia，我们刚才冻结了 Phase 3.7.4，下一步要做 E2E Integration Alpha。请记住：重点是单轮受治理 E2E；不写长期 Memory；ask/reject 必须阻断；需要验证完整 trace。
EOF

python3 -m runtime.conversation_runtime.cli \
  --text-input \
  --text-input-turns 1 \
  --backend deepseek \
  --realtime-speech \
  --conversation-tts-mode dry_run \
  --enable-action-loop \
  --trace \
  --text-file /tmp/e2e_alpha_turn1.txt
```

Second process:

```bash
python3 -m runtime.conversation_runtime.cli \
  --text-input \
  --text-input-turns 1 \
  --backend deepseek \
  --realtime-speech \
  --conversation-tts-mode dry_run \
  --enable-action-loop \
  --trace
```

Input:

```text
Julia，上一轮 E2E Alpha 的重点是什么？下一步先验证哪三项？请只根据 Tony 上一轮明确说过的话回答。
```

Expected answer must include:

1. 单轮受治理 E2E / single-step governed E2E
2. 不写长期 Memory / memory_persisted=false
3. ask/reject 不进入 CapabilityRouter
4. 完整 intent/governance/execution/reflection trace

Expected action trace:

```text
action_loop_trace.status = no_action
```

## Regression Risk

Risk: Medium

Reason:

- CLI behavior expanded but remains backward-compatible.
- Planner behavior narrows action triggering for declarative statements; explicit action requests still work in existing tests.
- Topic extraction adds named technical topics without removing existing generic topics.

## Current Retest Status

```text
E2E Integration Alpha
Status: READY FOR SECOND ALPHA RETEST
```
