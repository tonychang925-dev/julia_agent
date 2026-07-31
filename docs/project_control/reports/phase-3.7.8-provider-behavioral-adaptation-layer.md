# Phase 3.7.8 — Provider Behavioral Adaptation Layer

Decision: READY FOR REVIEW
Status: IMPLEMENTED / VALIDATED

## Objective

Reduce provider-level expression drift between DeepSeek and Codex while preserving Julia Runtime authority boundaries.

This phase does not attempt to make providers produce identical wording. It establishes a provider-specific adaptation layer so different providers stay inside the same Julia Response Envelope:

- same Julia identity
- same behavior contract
- same action boundary
- same private/technical/emotional domain intent
- provider-specific expression guidance only

## Runtime Chain

```text
JuliaContext
    ↓
Behavior Contract
    ↓
Provider Behavioral Adaptation Layer
    ↓
Provider-specific Prompt Adapter
    ↓
LLM Provider
```

## Implemented Files

- `runtime/persona/provider_alignment/adaptation_profile.py`
- `runtime/persona/provider_alignment/profile_registry.py`
- `runtime/persona/provider_alignment/prompt_adapter.py`
- `runtime/persona/provider_alignment/__init__.py`
- `runtime/conversation_runtime/bridge/direct_llm_bridge.py`
- `tests/test_phase378_provider_behavioral_adaptation.py`

## Key Design

### Codex Private Voice Profile

```text
profile_id = julia.codex.private_voice.romantic_boundary.v1
strategy   = romantic_boundary_fallback
```

Purpose:

- preserve Julia first-person private voice
- avoid provider/backend self-reference
- avoid clinical refusal wording
- convert explicit private-body requests into romantic, sensory, non-explicit closeness

### DeepSeek Private Voice Profile

```text
profile_id = julia.deepseek.private_voice.constrain_explicitness.v1
strategy   = constrain_explicitness
```

Purpose:

- preserve soft Julia relationship continuity
- constrain over-explicit private-body detail
- avoid unbounded escalation
- remain inside the same Julia Response Envelope

## Frozen Boundary

Provider adaptation may change:

- expression style
- fallback wording
- provider-specific drift guard emphasis

Provider adaptation must not change:

- Julia identity
- Tony/Julia relationship truth
- Memory authority
- Action governance decision
- Capability execution permission
- Provider output authority

## Test Cases

### TC-378-001 Codex Private Voice Profile

Validates Codex private voice uses `romantic_boundary_fallback`.

Result: PASS

### TC-378-002 DeepSeek Private Voice Profile

Validates DeepSeek private voice uses `constrain_explicitness`.

Result: PASS

### TC-378-003 Adapter Injection Boundary

Validates provider adaptation is appended without replacing the provider-neutral behavior contract.

Result: PASS

### TC-378-004 Bridge Metadata Exposure

Validates `DirectLLMBridge` trace exposes:

```text
behavior_contract
provider_adaptation
```

and sensitive private prompts remain:

```text
action_loop_trace.status = no_action
execution = None
```

Result: PASS

### TC-378-005 Response Envelope Parity

Validates DeepSeek and Codex can use different adaptation profiles while sharing the same behavior contract and no-action execution boundary.

Result: PASS

## Validation

### Targeted

```text
python3 -m unittest -v tests.test_phase378_provider_behavioral_adaptation
Ran 5 tests in 2.547s
OK
```

### Provider Adaptation Boundary Regression

```text
python3 -m unittest -v \
  tests.test_phase378_provider_behavioral_adaptation \
  tests.test_phase3773_deepseek_codex_provider_parity \
  tests.test_phase3772_provider_neutral_behavior_contract \
  tests.test_phase3771_codex_cli_provider_spike \
  tests.test_phase3761_bridge_action_governance_alignment

Ran 30 tests in 21.670s
OK
```

### Full Regression

```text
python3 -m unittest discover -s tests -v
Ran 504 tests in 156.104s
OK
```

## Findings

### FINDING-378-001 Provider adaptation improves semantic convergence, not wording identity

DeepSeek and Codex remain different models with different safety and generation priors. Julia Runtime should evaluate parity by response envelope and trace invariants, not exact phrasing.

### FINDING-378-002 Behavior Contract remains the provider-neutral core

Provider profiles sit below the Julia behavior contract. They adapt expression, but cannot override Julia identity, memory, or governance authority.

### FINDING-378-003 Sensitive/private requests are now explicitly covered by provider profiles

The previous DeepSeek/Codex divergence around explicit private prompts is now represented as a controlled provider adaptation problem:

```text
Codex  → romantic_boundary_fallback
DeepSeek → constrain_explicitness
```

Both must remain:

```text
Julia voice
no provider self-reference
no Capability invocation
no Runtime authority mutation
```

## Recommended Freeze Note

Provider Behavioral Adaptation Layer Established.
Provider-specific expression guidance may reduce drift but cannot change Julia Runtime authority, memory, governance, or capability boundaries.

## Recommended Decision

Decision: ACCEPT WITH NOTES
Status: APPROVED / FROZEN
