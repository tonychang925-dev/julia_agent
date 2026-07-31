# Claude Reference Voice Benchmark Cases

## CV-B005 — Voice Experience

Objective: measure end-to-end reference client voice rhythm.

Metrics:

- STT latency
- Claude first token latency
- Claude full response latency
- TTS start latency
- total turn duration
- interruption/retry behavior

Minimum accepted trace:

```json
{
  "case_id": "CV-B005",
  "input_mode": "voice",
  "stt_ms": 0,
  "first_token_ms": 0,
  "tts_start_ms": 0,
  "turn_duration_ms": 0
}
```
