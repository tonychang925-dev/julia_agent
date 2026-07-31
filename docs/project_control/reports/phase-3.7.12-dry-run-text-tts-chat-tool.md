# Dry-run Text Input / TTS Output Chat Tool

Status: READY  
Date: 2026-07-30

## Tool

```bash
scripts/dry_run_text_tts_chat.sh
```

Default command wrapped by the tool:

```bash
python3 -m runtime.conversation_runtime.cli \
  --text-input \
  --text-input-turns 100 \
  --backend deepseek \
  --realtime-speech \
  --conversation-tts-mode dry_run \
  --conversation-tts-engine local \
  --enable-action-loop \
  --trace
```

## Usage

```bash
cd /Users/admin/julia_agent
scripts/dry_run_text_tts_chat.sh
```

Input controls:

- one line + Enter: send one turn
- `/multi`: enter multi-line input
- `/send`: send multi-line input
- `/cancel`: cancel multi-line input
- `退出` / `结束` / `bye`: exit continuous session

## Environment overrides

```bash
JULIA_TEXT_INPUT_TURNS=20 scripts/dry_run_text_tts_chat.sh
JULIA_RELATIONSHIP_MODE=private_voice_continuity scripts/dry_run_text_tts_chat.sh
JULIA_TRACE=0 scripts/dry_run_text_tts_chat.sh
JULIA_VOICE_MAX_TOKENS=220 scripts/dry_run_text_tts_chat.sh
JULIA_NO_FAST_ACK=1 scripts/dry_run_text_tts_chat.sh
```

## Notes

- `conversation-tts-mode=dry_run` does not play real audio.
- It validates the runtime path: text input → DeepSeek/Codex bridge → streaming chunks → sentence segmentation → dry-run TTS events.
- For DeepSeek, `DEEPSEEK_API_KEY` must be present for actual provider responses.
