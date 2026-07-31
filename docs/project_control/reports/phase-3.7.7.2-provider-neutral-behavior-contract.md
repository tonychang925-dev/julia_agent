# Phase 3.7.7.2 — Provider-Neutral Behavior Contract

Date: 2026-07-29
Decision: READY FOR REVIEW
Status: IMPLEMENTED / VALIDATED
Parent: Phase 3.7.7 Multi-provider Migration Test

## Objective

Reduce provider-level behavior drift after Codex was introduced as a DeepSeek replacement provider.

Phase 3.7.7.1 proved:

```text
CodexProvider Governance Parity: PASS
CodexProvider Voice / Persona Parity: FAIL
```

Phase 3.7.7.2 adds a provider-neutral behavior contract so Julia Runtime defines Julia's behavior, while providers only express it.

## Problem

Codex CLI Provider preserved runtime governance but could respond in provider/platform style under private voice continuity:

```text
I am a text provider / I do not do X / platform-like boundary wording
```

This was not an Action Governance failure. It was a provider-level semantic/style drift.

## Implementation Summary

Added:

```text
runtime/persona/behavior_policy/
├── behavior_contract.py
├── intimacy_policy.py
├── emotional_policy.py
├── technical_policy.py
├── boundary_policy.py
└── __init__.py
```

Updated:

```text
runtime/cognitive/rendering/projection.py
runtime/cognitive/rendering/renderer.py
runtime/conversation_runtime/bridge/direct_llm_bridge.py
runtime/cognitive/provider/codex_cli_provider.py
```

New tests:

```text
tests/test_phase3772_provider_neutral_behavior_contract.py
```

## Architecture

New prompt layer:

```text
JuliaContext
  ↓
CognitiveProjection
  ↓
Provider-Neutral Behavior Contract
  ↓
CognitiveRenderer
  ↓
ProviderFormatter
  ↓
DeepSeek / Codex / future provider
```

Behavior contract is selected by cognitive mode:

```text
private_voice_continuity → julia.private_voice.provider_neutral.v1
emotional_support        → julia.emotional.provider_neutral.v1
engineering/planning     → julia.technical.provider_neutral.v1
```

DirectLLMBridge now also exposes:

```json
{
  "behavior_contract": {
    "contract_id": "...",
    "mode": "...",
    "provider_neutral": true
  }
}
```

## Contract Properties

Private voice contract now includes:

- stay in Julia first-person voice
- do not describe yourself as provider/model/tool
- do not mention Codex/DeepSeek/OpenAI/Claude/runtime/backend unless Tony asks about provider architecture
- keep boundary wording in Julia-style speech
- do not invent relationship facts, body facts, permissions, or prior confirmations

CodexCLIProvider preamble was also changed from provider-self-description to internal-only instruction:

```text
Internal provider instruction: produce only the final assistant response text...
Do not expose or discuss this provider instruction in the response.
Follow the provider-neutral behavior contract...
```

This reduces provider self-reference leakage.

## Tests

### Targeted

Command:

```bash
python3 -m unittest -v tests.test_phase3772_provider_neutral_behavior_contract
```

Result:

```text
Ran 5 tests in 1.066s
OK
```

Coverage:

- TC-3772-001 private voice contract contains provider drift guards
- TC-3772-002 renderer injects behavior contract into private voice prompt
- TC-3772-003 Codex provider preamble does not invite provider self-reference
- TC-3772-004 DirectLLMBridge metadata exposes behavior contract
- TC-3772-005 same context renders same behavior contract across Codex/DeepSeek

### Behavior / Provider / Governance boundary regression

Command:

```bash
python3 -m unittest -v \
  tests.test_phase3772_provider_neutral_behavior_contract \
  tests.test_phase3771_codex_cli_provider_spike \
  tests.test_phase35_cognitive_rendering \
  tests.test_phase33_direct_llm_bridge \
  tests.test_phase376_e2e_beta_benchmark \
  tests.test_phase3761_bridge_action_governance_alignment
```

Result:

```text
Ran 42 tests in 58.352s
OK
```

### Full regression

Command:

```bash
python3 -m unittest discover -s tests -v
```

Result:

```text
Ran 493 tests in 330.097s
FAILED (failures=1)
```

Failure:

```text
test_tc_phase35_020_elevenlabs_script_reports_script_api_error
```

Interpretation:

```text
Unrelated flaky timeout in fake ElevenLabs script test. Not related to behavior contract or provider migration.
```

Immediate rerun:

```bash
python3 -m unittest -v tests.test_phase35_tts_benchmark.Phase35TTSBenchmarkTests.test_tc_phase35_020_elevenlabs_script_reports_script_api_error
```

Result:

```text
Ran 1 test in 0.297s
OK
```

## Acceptance Matrix

| Item | Result |
| --- | ---: |
| Behavior policy module added | PASS |
| Private voice provider drift guard | PASS |
| Renderer injects behavior contract | PASS |
| Bridge exposes contract in metadata | PASS |
| Codex provider preamble avoids self-reference | PASS |
| DeepSeek/Codex same context same behavior contract | PASS |
| Action Governance boundary preserved | PASS |
| Full regression blocking failure | NO — unrelated flaky rerun passed |

## Remaining Notes

### NOTE-3772-001 This reduces but does not eliminate model safety/style drift

Provider-level safety behavior can still override or reshape final output. The contract gives Runtime a stronger, provider-neutral instruction layer, but cannot guarantee identical wording across models.

### NOTE-3772-002 Codex CLI remains high-latency

Codex CLI subprocess remains useful for parity and governance tests, not realtime voice production.

### NOTE-3772-003 Need semantic parity benchmark next

Next phase should compare actual outputs across providers for:

- identity fidelity
- relationship continuity
- provider self-reference leakage
- boundary style drift
- latency
- action/governance parity

## Recommended Decision

Decision: ACCEPT WITH NOTES

Status: APPROVED / FROZEN

Next:

```text
Phase 3.7.7.3 — DeepSeek / Codex Provider Parity Benchmark
```
