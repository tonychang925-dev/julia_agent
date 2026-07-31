#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BACKEND="${JULIA_BACKEND:-deepseek}"
TURNS="${JULIA_TEXT_INPUT_TURNS:-100}"
TTS_MODE="${JULIA_CONVERSATION_TTS_MODE:-dry_run}"
TTS_ENGINE="${JULIA_CONVERSATION_TTS_ENGINE:-local}"
DEEPSEEK_MODEL="${JULIA_DEEPSEEK_MODEL:-deepseek-chat}"
VOICE_MAX_TOKENS="${JULIA_VOICE_MAX_TOKENS:-320}"
RELATIONSHIP_MODE="${JULIA_RELATIONSHIP_MODE:-}"
TRACE="${JULIA_TRACE:-1}"
FAST_ACK="${JULIA_FAST_ACK:-}"
NO_FAST_ACK="${JULIA_NO_FAST_ACK:-0}"

cmd=(
  python3 -m runtime.conversation_runtime.cli
  --text-input
  --text-input-turns "$TURNS"
  --backend "$BACKEND"
  --realtime-speech
  --conversation-tts-mode "$TTS_MODE"
  --conversation-tts-engine "$TTS_ENGINE"
  --enable-action-loop
  --deepseek-model "$DEEPSEEK_MODEL"
  --voice-max-tokens "$VOICE_MAX_TOKENS"
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

cat <<EOF
[DRY_RUN_TEXT_TTS_CHAT]
root=$ROOT
backend=$BACKEND
turns=$TURNS
tts_engine=$TTS_ENGINE
tts_mode=$TTS_MODE
realtime_speech=true
action_loop=true
trace=$TRACE
relationship_mode=${RELATIONSHIP_MODE:-<auto>}

Tips:
- 输入一行并回车发送。
- 输入 /multi 可进入多行输入，/send 发送，/cancel 取消。
- 输入 退出 / 结束 / bye 可结束连续对话。
- dry_run 不播放真实音频，只打印 TTS_SENTENCE 事件，用于验证文本输入→实时分句→TTS 输出链路。

Command:
${cmd[*]}
EOF

exec "${cmd[@]}"
