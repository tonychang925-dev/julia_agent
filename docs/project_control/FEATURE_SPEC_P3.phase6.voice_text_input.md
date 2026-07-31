# FEATURE_SPEC P3.phase6.voice_text_input — Conversation CLI Text Input Mode

## Status
✅ Implemented / PASS

## Motivation
Voice testing currently depends on STT/microphone capture. During debugging Tony needs to type complete long inputs, press Enter, and still exercise the normal Julia conversation path: backend, realtime sentence TTS, trace, context runtime, and latency reporting.

## Scope
Add a CLI text-input mode for `julia-conversation`:

- `--text-input`: read user turns from stdin line input instead of microphone/STT.
- `--text-input-turns N`: stop after N typed turns; `0` means manual exit / EOF / Ctrl+C.
- Preserve existing output pipeline: `ConversationLoop`, realtime speech, TTS engine, trace, state logs, latency logs.
- If both `--text-input` and `--real-voice` are present, text input takes precedence so STT is not invoked.

## Non-goals
- Does not change Memory Runtime, Context OS, Evidence retrieval, STT, or TTS behavior.
- Does not add a GUI.

## User Command
Recommended typed-input command:

```bash
./julia-conversation \
  --backend deepseek \
  --text-input \
  --realtime-speech \
  --conversation-tts-engine edge-tts \
  --long-speech \
  --trace
```

Compatibility form; `--text-input` overrides microphone/STT:

```bash
./julia-conversation \
  --backend deepseek \
  --real-voice \
  --text-input \
  --realtime-speech \
  --conversation-tts-engine edge-tts \
  --long-speech \
  --trace \
  --stt-retries 0 \
  --stt-empty-limit 2
```

## Acceptance Criteria
- Typed line is printed as `text=...` and passed into `ConversationLoop`.
- No `[VOICE]` prompt or STT capture occurs in text-input mode.
- Realtime sentence TTS and `trace=` are preserved.
- Manual continuous mode is supported when `--text-input-turns 0`.

## Tests
- `tests.test_text_input_cli.TextInputCLITests.test_tc_text_input_001_stdin_turn_bypasses_stt_and_preserves_realtime_tts_trace`
- `tests.test_text_input_cli.TextInputCLITests.test_tc_text_input_002_text_input_takes_precedence_over_real_voice`

## Validation
- Targeted: `python3 -m unittest tests.test_text_input_cli -v` → 2 tests OK
- Full: `python3 -m unittest discover -s tests` → 361 tests OK
