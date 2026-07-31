# Voice Input / TTS Output Chat Tool

Status: READY  
Date: 2026-07-30

## Tool

```bash
scripts/voice_input_tts_chat.sh
```

Default wrapped command:

```bash
python3 -m runtime.conversation_runtime.cli \
  --real-voice \
  --real-voice-turns 100 \
  --backend deepseek \
  --realtime-speech \
  --conversation-tts-mode say \
  --conversation-tts-engine hook-routed \
  --enable-action-loop \
  --trace
```

## Usage

```bash
cd /Users/admin/julia_agent
scripts/voice_input_tts_chat.sh
```

## Controls

- Wait for `[VOICE] 请开始说话`.
- Speak naturally; silence auto-submits after `JULIA_AUTO_STOP_MS`.
- Say `退出` / `结束` / `bye` to exit.

## Environment overrides

```bash
JULIA_REAL_VOICE_TURNS=20 scripts/voice_input_tts_chat.sh
JULIA_CONVERSATION_TTS_MODE=dry_run scripts/voice_input_tts_chat.sh
JULIA_CONVERSATION_TTS_ENGINE=edge-tts JULIA_CONVERSATION_TTS_MODE=say scripts/voice_input_tts_chat.sh
JULIA_RELATIONSHIP_MODE=private_voice_continuity scripts/voice_input_tts_chat.sh
JULIA_LONG_SPEECH=1 scripts/voice_input_tts_chat.sh
JULIA_TRACE=0 scripts/voice_input_tts_chat.sh
```

## Dependencies

- STT binary: `/Users/admin/Desktop/speech_lab/stt`
- macOS Microphone permission
- macOS Speech Recognition permission
- DeepSeek runtime requires `DEEPSEEK_API_KEY`


## Text-input equivalent

User-provided text-input baseline:

```bash
python3 -m runtime.conversation_runtime.cli \
  --text-input \
  --text-input-turns 100 \
  --backend deepseek \
  --realtime-speech \
  --conversation-tts-engine hook-routed \
  --enable-action-loop \
  --trace
```

Voice-input equivalent:

```bash
python3 -m runtime.conversation_runtime.cli \
  --real-voice \
  --real-voice-turns 100 \
  --backend deepseek \
  --realtime-speech \
  --conversation-tts-engine hook-routed \
  --enable-action-loop \
  --trace
```
