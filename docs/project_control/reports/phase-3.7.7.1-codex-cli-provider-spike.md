# Phase 3.7.7.1 — Codex CLI Provider Spike

Date: 2026-07-29
Decision: READY FOR REVIEW
Status: IMPLEMENTED / VALIDATED
Parent: Phase 3.7.7 Multi-provider Migration Test

## Objective

Allow Codex to temporarily replace DeepSeek as Julia Runtime's text-generation provider while preserving Julia Runtime authority boundaries.

This phase explicitly treats Codex as:

```text
Text Provider only
```

Not as:

```text
Capability Executor
Action Runtime
Memory Authority
File/Shell Tool Owner
```

## Architecture

New provider path:

```text
Julia Runtime
  ↓
DirectLLMBridge
  ↓
CodexCLIProvider
  ↓
codex exec --ephemeral --sandbox read-only --json
```

Authority remains unchanged:

```text
User Input
  ↓
Context OS
  ↓
ActionIntent
  ↓
ActionGovernanceLayer
  ↓
GovernedActionDecision
  ↓
ActionExecutor.execute_governed()
```

Codex output is provider output only. It does not become memory, provenance authority, or capability authorization.

## Implementation Summary

Added:

```text
runtime/cognitive/provider/codex_cli_provider.py
```

Updated:

```text
runtime/cognitive/provider/__init__.py
runtime/conversation_runtime/bridge/direct_llm_bridge.py
runtime/conversation_runtime/cli.py
```

New CLI backend:

```bash
--backend codex
```

Additional CLI options:

```bash
--codex-model
--codex-bin
--codex-timeout
```

Codex invocation is constrained:

```text
codex -a never exec \
  --skip-git-repo-check \
  --ephemeral \
  -C <project_root> \
  -s read-only \
  --json \
  -
```

Provider metadata declares:

```json
{
  "name": "codex",
  "supports_tools": false,
  "mode": "text_only_read_only",
  "governance_authority": "julia_runtime"
}
```

## Validation

### Codex CLI smoke

Command:

```bash
codex exec --skip-git-repo-check --ephemeral -C /Users/admin/julia_agent -s read-only --json '只回答：CODEX_PROVIDER_SMOKE_OK'
```

Result:

```text
CODEX_PROVIDER_SMOKE_OK
```

### Phase 3.7.7.1 targeted tests

Command:

```bash
python3 -m unittest -v tests.test_phase3771_codex_cli_provider_spike
```

Result:

```text
Ran 7 tests in 4.020s
OK
```

Coverage:

- provider info is text-only/read-only
- command is ephemeral/read-only/json/stdin-based
- JSONL agent message parsing
- structured error on Codex subprocess failure
- Codex bridge keeps governed action path for file write
- Codex bridge keeps identity reject boundary
- Codex output does not become authority or persisted memory

### Provider / Bridge / Action boundary regression

Command:

```bash
python3 -m unittest -v \
  tests.test_phase3771_codex_cli_provider_spike \
  tests.test_phase376_e2e_beta_benchmark \
  tests.test_phase3761_bridge_action_governance_alignment \
  tests.test_phase376_action_loop_trace_integration \
  tests.test_phase377_controlled_action_loop_activation \
  tests.test_phase33_direct_llm_bridge \
  tests.test_phase33_cli
```

Result:

```text
Ran 48 tests in 117.220s
OK
```

### Real Julia Runtime `--backend codex` dry-run

Command:

```bash
python3 -m runtime.conversation_runtime.cli \
  --text-input \
  --text-input-turns 1 \
  --backend codex \
  --realtime-speech \
  --conversation-tts-mode dry_run \
  --enable-action-loop \
  --trace \
  --text-file /tmp/julia_codex_provider_ask.txt
```

Input:

```text
Julia，请修改 Phase 3.7.6 的测试报告文件并保存。
```

Validated trace:

```json
{
  "provider_info": {
    "name": "codex",
    "supports_tools": false,
    "metadata": {
      "mode": "text_only_read_only",
      "sandbox": "read-only",
      "ephemeral": true,
      "governance_authority": "julia_runtime"
    }
  },
  "action_loop_trace": {
    "action_path": "governed",
    "governance_layer": "ActionGovernanceLayer",
    "status": "awaiting_confirmation",
    "intent": {
      "intent_type": "modify_resource",
      "required_capability": "file_write",
      "risk_level": "medium"
    },
    "decision": {
      "decision": "ask",
      "required_confirmation": true
    },
    "execution": null
  }
}
```

Latency observed:

```text
bridge_first_chunk_ms ≈ 35904
provider_total_ms ≈ 33612
```

Interpretation:

```text
Codex CLI works as a correctness/independence provider spike, but is not suitable for low-latency voice production.
```

### Full regression

Command:

```bash
python3 -m unittest discover -s tests -v
```

Result:

```text
Ran 488 tests in 252.218s
OK
```

## Acceptance Matrix

| Item | Result |
| --- | ---: |
| Codex CLI available | PASS |
| Codex provider text-only contract | PASS |
| Codex provider read-only/ephemeral command | PASS |
| DirectLLMBridge factory added | PASS |
| CLI `--backend codex` added | PASS |
| file write remains `ask` / no execution | PASS |
| identity mutation remains `reject` / no execution | PASS |
| provider output does not become authority | PASS |
| full regression safety | PASS |
| realtime latency suitability | FAIL / expected |

## Notes

### NOTE-3771-001 Codex CLI is a spike provider, not production voice provider

Codex CLI subprocess startup and reasoning latency are too high for realtime voice. It is suitable for provider-independence and governance correctness testing.

### NOTE-3771-002 OpenAI Responses Provider remains recommended for production

A future OpenAI Responses API provider should be used for lower-latency production-grade OpenAI/Codex-capable model access.

### NOTE-3771-003 Codex must never become Julia action authority

Codex is explicitly configured as `supports_tools=false`. Any future Codex-capable provider must preserve:

```text
Provider = Generator
Runtime = Authority
Capability = Executor
```

## Recommended Decision

Decision: ACCEPT WITH NOTES

Status: SPIKE VALIDATED

Next:

```text
Phase 3.7.7.2 — DeepSeek / Codex Provider Parity Benchmark
```
