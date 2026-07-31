# Phase 3.6.7.1 — Voice First Response Optimization Report

Date: 2026-07-27
Status: PASS
Scope: Voice delivery latency hardening after real v4 latency run

## Trigger

Real v4 latency run showed that `VoiceLatencyPolicy` was active, but some turns still missed TTFV because the first complete spoken sentence arrived too late.

Observed issue:

- `context_build_ms`: 7–17ms, healthy
- `provider_first_token_ms`: 1119–2448ms, provider-bound
- `tts_start_ms`: missed on turns where the model delayed punctuation / complete sentence formation
- one TTS hard split produced an unnatural boundary: `Claude、` / `GPT 和 DeepSeek...`

## Changes

### 1. Stricter VoiceLatencyPolicy Defaults

Updated:

```text
runtime/conversation_runtime/voice_latency_policy.py
runtime/conversation_runtime/bridge/direct_llm_bridge.py
runtime/conversation_runtime/cli.py
```

Defaults changed:

```text
voice_max_tokens: 160 → 120
first_sentence_chars: 14 → 10
max_sentences: 4 → 3
```

Policy now explicitly asks the provider to start with a complete, self-contained first sentence and end it with `。` before details.

### 2. TTS Hard Split Improvement

Updated:

```text
tts/chunking.py
```

Removed `、` from preferred hard-split soft marks so TTS will avoid splitting entity lists like:

```text
Claude、GPT 和 DeepSeek
```

Expected behavior is to prefer an earlier clause boundary such as `清楚，`.

### 3. EchoProvider Streaming Contract Preservation

Updated:

```text
runtime/cognitive/provider/echo_provider.py
```

EchoProvider now preserves exact response text in streaming contract tests instead of applying TTS sanitizer splitting. This keeps provider-contract tests separate from TTS voice rendering behavior.

## Tests Added / Updated

Updated:

```text
tests/test_phase367_voice_latency_optimization.py
```

New coverage:

- default voice token budget is 120
- TTS hard split prefers clause boundary over enumeration mark

## Verification

Targeted tests:

```bash
python3 -m unittest tests/test_phase33_cognitive_context.py tests/test_phase367_voice_latency_optimization.py
```

Result:

```text
Ran 11 tests in 0.093s
OK
```

Full regression:

```bash
python3 -m unittest discover -s tests
```

Result:

```text
Ran 231 tests in 10.027s
OK
```

## Current Expectation

Next real voice run should show:

- shorter first complete sentence
- lower risk of `tts_start_ms` misses caused by delayed punctuation
- fewer long responses
- cleaner TTS segmentation around provider/model names

This does not fully eliminate DeepSeek HTTP / first-token variability. If provider first-token remains above 2000ms, the next target is Provider Warm Path.

## Recommended Re-test

```bash
touch /tmp/tts_enabled
./julia-conversation --backend deepseek --real-voice --real-voice-turns 4 \
  --realtime-speech --conversation-tts-engine elevenlabs-stream --trace \
  --auto-stop-ms 900 --max-duration-ms 5000 --stt-timeout 8 \
  --stt-retries 0 --stt-empty-limit 2 \
  2>&1 | tee tmp/julia_birth_v5_latency_120.log
```

Note: `--voice-max-tokens` no longer needs to be passed for 120; it is now the default.
