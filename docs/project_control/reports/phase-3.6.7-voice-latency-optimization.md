# Phase 3.6.7 — Voice Latency Optimization Runtime Report

Date: 2026-07-27
Status: PASS
Scope: Voice Embodiment Layer only

## Objective

Reduce realtime voice response latency after Julia Birth Test v4 without changing Julia's cognitive ownership layers.

Protected layers during this phase:

- Persona Runtime
- Relationship Runtime
- Memory Runtime
- Context Arbitration
- Cognitive Projection semantics

## Implemented Changes

### 1. VoiceLatencyPolicy

Added:

```text
runtime/conversation_runtime/voice_latency_policy.py
```

The policy appends provider-facing delivery constraints only:

- short first spoken sentence
- bounded total spoken sentences
- no markdown/code/stage-direction output for voice delivery
- explicit statement that identity, memory, relationship, and cognitive mode must be preserved

This is a Voice Embodiment optimization, not a Persona/Memory rewrite.

### 2. Provider Token Cap for Voice Path

Updated:

```text
runtime/cognitive/provider/openai_compatible.py
runtime/cognitive/provider/deepseek_provider.py
```

DeepSeek voice path can now pass:

```json
{
  "max_tokens": 160,
  "temperature": 0.5
}
```

The provider adapter only passes these options when configured, preserving old test clients and existing non-voice behavior.

### 3. DirectLLMBridge Voice Optimization Flag

Updated:

```text
runtime/conversation_runtime/bridge/direct_llm_bridge.py
```

New fields:

```python
voice_latency_optimized: bool = False
voice_max_tokens: int = 160
```

When enabled, the bridge applies `VoiceLatencyPolicy` after JuliaContext rendering and before provider formatting execution.

### 4. CLI Flags

Updated:

```text
runtime/conversation_runtime/cli.py
```

New flags:

```text
--disable-voice-latency-optimization
--voice-max-tokens
```

Default DeepSeek CLI path enables voice latency optimization unless explicitly disabled.

## Tests Added

```text
tests/test_phase367_voice_latency_optimization.py
```

Coverage:

- TC-PHASE367-001 VoiceLatencyPolicy adds voice-only constraints
- TC-PHASE367-002 VoiceLatencyPolicy disabled path leaves messages unchanged
- TC-PHASE367-003 DeepSeek provider passes max_tokens/temperature to client payload
- TC-PHASE367-004 DirectLLMBridge emits voice_latency_policy metadata
- TC-PHASE367-005 DeepSeek factory enables voice latency policy and token cap

## Verification

### Targeted Regression

Command:

```bash
python3 -m unittest tests/test_phase367_voice_latency_optimization.py tests/test_phase36_real_voice_e2e.py tests/test_phase36_voice_cognitive_loop_validation.py tests/test_phase35_latency_benchmark.py tests/test_phase37_short_greeting.py tests/test_phase33_deepseek_provider.py tests/test_phase33_direct_llm_bridge.py
```

Result:

```text
Ran 47 tests in 8.941s
OK
```

### Full Regression

Command:

```bash
python3 -m unittest discover -s tests
```

Result:

```text
Ran 229 tests in 10.290s
OK
```

## Expected Runtime Effect

This phase should reduce perceived voice latency mainly by:

1. forcing a short first spoken sentence,
2. reducing total provider generation length,
3. reducing long-form voice drift,
4. keeping TTS input cleaner and shorter.

It does not directly remove provider network first-token latency. If DeepSeek first-token delay remains high, the next optimization target is provider warm path / persistent HTTP client behavior.

## Rollback

Rollback points:

- disable at runtime with `--disable-voice-latency-optimization`
- increase response budget with `--voice-max-tokens N`
- revert files:
  - `runtime/conversation_runtime/voice_latency_policy.py`
  - `runtime/conversation_runtime/bridge/direct_llm_bridge.py`
  - `runtime/conversation_runtime/cli.py`
  - `runtime/cognitive/provider/deepseek_provider.py`
  - `runtime/cognitive/provider/openai_compatible.py`

## Final Decision

Phase 3.6.7 implementation is ready for real voice validation.

Recommended next command:

```bash
touch /tmp/tts_enabled
./julia-conversation --backend deepseek --real-voice --real-voice-turns 4 \
  --realtime-speech --conversation-tts-engine elevenlabs-stream --trace \
  --auto-stop-ms 900 --max-duration-ms 5000 --stt-timeout 8 \
  --stt-retries 0 --stt-empty-limit 2 \
  --voice-max-tokens 120 \
  2>&1 | tee tmp/julia_birth_v5_latency.log
```
