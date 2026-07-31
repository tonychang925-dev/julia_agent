# Phase 3.6.7.2 — Voice Semantic Compression Guard Report

Date: 2026-07-27
Status: PASS
Scope: Voice delivery semantic guard

## Trigger

After Phase 3.6.7.1, realtime voice latency improved and all observed TTFV samples passed, but voice compression exposed a semantic accuracy issue:

```text
在重构你的身份系统。
```

This was fast, but it compressed the core object incorrectly. The intended object was Julia Runtime / Julia cognitive identity system, not Tony's identity system.

## Objective

Keep the fast first-response behavior while preventing short voice replies from losing or replacing key cognitive objects.

## Change

Updated:

```text
runtime/conversation_runtime/voice_latency_policy.py
```

Added semantic guard metadata:

```json
{
  "semantic_guard": {
    "scope": "core_object_preservation",
    "protected_terms": [
      "Julia Runtime",
      "Julia",
      "Tony",
      "Cognitive Runtime",
      "Memory Runtime",
      "Persona Package"
    ]
  }
}
```

Added provider-facing delivery rule:

```text
Preserve core objects: say Julia Runtime / Julia / Tony / Persona Package when those are the actual topic; do not replace them with vague phrases like 这个项目, 你的系统, 身份系统, or 那个东西.
```

## Boundary

This is still a Voice Delivery policy only.

It does not modify:

- Persona Runtime
- Relationship Runtime
- Memory Runtime
- Conversation Continuity
- Cognitive Mode Arbitration
- Memory Retrieval

## Tests

Updated:

```text
tests/test_phase367_voice_latency_optimization.py
```

Added:

- TC-PHASE367-008 Voice policy requires core object preservation
- TC-PHASE367-009 Voice policy exposes semantic guard metadata

## Verification

Command:

```bash
python3 -m unittest discover -s tests
```

Result:

```text
Ran 233 tests in 10.082s
OK
```

## Expected Runtime Effect

Future short replies should prefer:

```text
在重构 Julia Runtime 的身份系统。
```

instead of:

```text
在重构你的身份系统。
```

This preserves voice latency while improving semantic accuracy.

## Recommended Re-test

```bash
./julia-conversation --backend deepseek --real-voice --real-voice-turns 4 \
  --realtime-speech --conversation-tts-engine elevenlabs-stream --trace \
  --auto-stop-ms 900 --max-duration-ms 5000 --stt-timeout 8 \
  --stt-retries 0 --stt-empty-limit 2 \
  2>&1 | tee tmp/julia_birth_v6_semantic_guard.log
```

Focus prompts:

```text
我们现在在忙什么？
下一步怎么做？
Julia Runtime 是什么？
```
