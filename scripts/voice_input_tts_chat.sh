#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BACKEND="${JULIA_BACKEND:-deepseek}"
TURNS="${JULIA_REAL_VOICE_TURNS:-100}"
TTS_MODE="${JULIA_CONVERSATION_TTS_MODE:-say}"
TTS_ENGINE="${JULIA_CONVERSATION_TTS_ENGINE:-hook-routed}"
DEEPSEEK_MODEL="${JULIA_DEEPSEEK_MODEL:-deepseek-chat}"
VOICE_MAX_TOKENS="${JULIA_VOICE_MAX_TOKENS:-320}"
RELATIONSHIP_MODE="${JULIA_RELATIONSHIP_MODE:-}"
TRACE="${JULIA_TRACE:-1}"
FAST_ACK="${JULIA_FAST_ACK:-}"
NO_FAST_ACK="${JULIA_NO_FAST_ACK:-0}"
STT_BIN="${JULIA_STT_BIN:-/Users/admin/Desktop/speech_lab/stt}"
SPEECH_LAB_ROOT="${JULIA_SPEECH_LAB_ROOT:-/Users/admin/Desktop/speech_lab}"
STT_LANG="${JULIA_STT_LANG:-zh-CN}"
AUTO_STOP_MS="${JULIA_AUTO_STOP_MS:-1800}"
MAX_DURATION_MS="${JULIA_MAX_DURATION_MS:-30000}"
STT_TIMEOUT="${JULIA_STT_TIMEOUT:-45}"
STT_RETRIES="${JULIA_STT_RETRIES:-1}"
STT_EMPTY_LIMIT="${JULIA_STT_EMPTY_LIMIT:-3}"
LONG_SPEECH="${JULIA_LONG_SPEECH:-0}"

cmd=(
  python3 -m runtime.conversation_runtime.cli
  --real-voice
  --real-voice-turns "$TURNS"
  --backend "$BACKEND"
  --realtime-speech
  --conversation-tts-mode "$TTS_MODE"
  --conversation-tts-engine "$TTS_ENGINE"
  --enable-action-loop
  --deepseek-model "$DEEPSEEK_MODEL"
  --voice-max-tokens "$VOICE_MAX_TOKENS"
  --speech-lab-root "$SPEECH_LAB_ROOT"
  --stt-bin "$STT_BIN"
  --stt-lang "$STT_LANG"
  --auto-stop-ms "$AUTO_STOP_MS"
  --max-duration-ms "$MAX_DURATION_MS"
  --stt-timeout "$STT_TIMEOUT"
  --stt-retries "$STT_RETRIES"
  --stt-empty-limit "$STT_EMPTY_LIMIT"
)

if [[ "$TRACE" == "1" || "$TRACE" == "true" || "$TRACE" == "yes" ]]; then
  cmd+=(--trace)
fi

if [[ -n "$RELATIONSHIP_MODE" ]]; then
  cmd+=(--relationship-mode "$RELATIONSHIP_MODE")
fi

if [[ -n "$FAST_ACK" ]]; then
  cmd+=(--fast-ack "$FAST_ACK")
fi

if [[ "$NO_FAST_ACK" == "1" || "$NO_FAST_ACK" == "true" || "$NO_FAST_ACK" == "yes" ]]; then
  cmd+=(--no-fast-ack)
fi

if [[ "$LONG_SPEECH" == "1" || "$LONG_SPEECH" == "true" || "$LONG_SPEECH" == "yes" ]]; then
  cmd+=(--long-speech)
fi

cat <<EOF
[VOICE_INPUT_TTS_CHAT]
root=$ROOT
backend=$BACKEND
turns=$TURNS
stt_bin=$STT_BIN
stt_lang=$STT_LANG
auto_stop_ms=$AUTO_STOP_MS
max_duration_ms=$MAX_DURATION_MS
tts_engine=$TTS_ENGINE
tts_mode=$TTS_MODE
realtime_speech=true
action_loop=true
trace=$TRACE
relationship_mode=${RELATIONSHIP_MODE:-<auto>}

Tips:
- 看到 [VOICE] 请开始说话 后直接说话；停顿约 ${AUTO_STOP_MS}ms 自动提交。
- 说 退出 / 结束 / bye 可结束。
- 若没识别到，会按 JULIA_STT_RETRIES=${STT_RETRIES} 重试；连续空输入达到 JULIA_STT_EMPTY_LIMIT=${STT_EMPTY_LIMIT} 会跳过该轮。
- 默认 TTS 是 hook-routed + say，会有真实语音输出；想只看日志可设 JULIA_CONVERSATION_TTS_MODE=dry_run。

Command:
${cmd[*]}
EOF

exec "${cmd[@]}"
