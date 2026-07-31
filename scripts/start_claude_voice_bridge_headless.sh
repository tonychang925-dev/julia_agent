#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/admin/julia_agent"
WATCHER="$ROOT/scripts/claude_voice_headless_watcher.py"
LOG="/tmp/julia_voice_headless_watcher.log"
TTS_ENGINE="${JULIA_CONVERSATION_TTS_ENGINE:-local}"
TTS_MODE="${JULIA_CONVERSATION_TTS_MODE:-say}"
HANDOFF_TIMEOUT="${JULIA_HANDOFF_TIMEOUT:-240}"
CLAUDE_TIMEOUT="${CLAUDE_VOICE_TIMEOUT:-180}"
CLAUDE_CWD="${CLAUDE_VOICE_CWD:-$ROOT}"
CLAUDE_BIN="${CLAUDE_BIN:-/Users/admin/bin/claude}"

cd "$ROOT"

printf '[bridge-headless] No paste mode. Claude Code CLI: %s\n' "$CLAUDE_BIN"
printf '[bridge-headless] Watcher log: %s\n' "$LOG"

pkill -f "$WATCHER" >/dev/null 2>&1 || true
CONTINUE_ARGS=()
case "${CLAUDE_VOICE_CONTINUE:-0}" in
  1|true|TRUE|yes|YES) CONTINUE_ARGS=(--continue-session) ;;
esac
python3 -u "$WATCHER" \
  --claude-bin "$CLAUDE_BIN" \
  --cwd "$CLAUDE_CWD" \
  --timeout "$CLAUDE_TIMEOUT" \
  "${CONTINUE_ARGS[@]}" \
  >"$LOG" 2>&1 &
WATCHER_PID=$!
printf '[bridge-headless] watcher_pid=%s\n' "$WATCHER_PID"
trap 'kill "$WATCHER_PID" >/dev/null 2>&1 || true' EXIT INT TERM

./julia-conversation \
  --real-voice \
  --real-voice-session \
  --backend claude \
  --handoff-timeout "$HANDOFF_TIMEOUT" \
  --realtime-speech \
  --conversation-tts-engine "$TTS_ENGINE" \
  --conversation-tts-mode "$TTS_MODE"
