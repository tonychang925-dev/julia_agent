#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/admin/julia_agent"
WATCHER="$ROOT/scripts/claude_voice_watcher.py"
LOG="/tmp/julia_voice_watcher.log"
APP_NAME="${CLAUDE_VOICE_TARGET_APP:-}"
TTS_ENGINE="${JULIA_CONVERSATION_TTS_ENGINE:-local}"
TTS_MODE="${JULIA_CONVERSATION_TTS_MODE:-say}"
HANDOFF_TIMEOUT="${JULIA_HANDOFF_TIMEOUT:-180}"

cd "$ROOT"

printf '[bridge] Start Claude Code first and leave its terminal input focused.\n'
printf '[bridge] Watcher log: %s\n' "$LOG"

pkill -f "$WATCHER" >/dev/null 2>&1 || true
if [ -n "$APP_NAME" ]; then
  "$WATCHER" --app "$APP_NAME" >"$LOG" 2>&1 &
else
  "$WATCHER" >"$LOG" 2>&1 &
fi
WATCHER_PID=$!
printf '[bridge] watcher_pid=%s\n' "$WATCHER_PID"
trap 'kill "$WATCHER_PID" >/dev/null 2>&1 || true' EXIT INT TERM

./julia-conversation \
  --real-voice \
  --real-voice-session \
  --backend claude \
  --handoff-timeout "$HANDOFF_TIMEOUT" \
  --realtime-speech \
  --conversation-tts-engine "$TTS_ENGINE" \
  --conversation-tts-mode "$TTS_MODE"
