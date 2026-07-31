# Phase CV-1.2 — Claude Native PTT Voice + TTS Auto-Rearm

Decision: ACCEPT WITH NOTES  
Status: IMPLEMENTED-SPIKE / MANUAL PTT GATE PENDING  
Date: 2026-07-30

## Corrected Direction

CV-1.2 does not build a parallel Claude client and does not implement custom STT. Voice input remains Claude Code native `/voice tap` PTT.

Added automation is limited to:

```text
Claude Stop Hook
  -> TTS playback
  -> guarded one-shot PTT rearm helper
```

## Implemented

- `scripts/claude_native_tts_hook.py`
- `scripts/rearm_claude_ptt.py`
- `scripts/claude_ptt_rearm_ctl.sh`
- `scripts/cv12_real_gate_summary.py`
- `/ptt-auto-rearm`, `/ptt-auto-rearm-off`, `/ptt-auto-rearm-status`
- `.claude/settings.local.json` Stop Hook registration
- Old project `/voice` command removed from `.claude/commands`, so Claude native `/voice` remains the intended surface.

## State Synchronization Gate

The remaining real-client gate validates synchronization across three states:

```text
Claude voice recorder state
TTS playback state
Auto-rearm expected state
```

Failure modes guarded:

- PTT tap stops recording when it was expected to start.
- Rearm before TTS completion.
- Duplicate rearm for one Claude answer.
- Key sent to wrong foreground app/window.
- Hook reentry causing duplicate TTS/rearm.

## Added Guards

### NOTE-CV12-001 Foreground Guard

`rearm_claude_ptt.py` now records and can strictly validate:

- frontmost app allowlist: Terminal / iTerm2 / iTerm / Warp
- frontmost window title
- expected project marker

Strict mode is available via:

```text
--strict-title --expected-project /Users/admin/Claude_Julia_Project
```

### NOTE-CV12-002 Idempotent Rearm

One-shot lock uses:

```text
turn_key = session_id + response_digest
```

A duplicated Stop Hook for the same assistant response records `duplicate_turn` and does not trigger another key event.

### Timestamp Evidence

Trace records:

- `tts_complete_ts`
- `key_injection_ts`
- `tail_buffer_ms`

Manual gate should verify:

```text
key_injection_ts > tts_complete_ts
```

## Validation

Targeted:

```bash
cd /Users/admin/Claude_Julia_Project
python3 -m unittest tests/test_cv12_native_ptt_auto_rearm.py -v
```

Result: 8 tests OK.

Full Claude_Julia_Project test suite:

```bash
cd /Users/admin/Claude_Julia_Project
python3 -m unittest discover -s tests -v
```

Result: 14 tests OK.

## Boundary Evidence

- `julia_runtime_imported=false`
- `julia_memory_authority_used=false`
- `julia_context_authority_used=false`
- `julia_action_authority_used=false`
- no `claude -p`
- no AppleScript prompt injection watcher
- no project `voice.md` command shadowing Claude native `/voice`

## Manual Three-Round Gate

Inside Claude Code:

```text
/voice tap
/ptt-auto-rearm
```

Round 1:

```text
Julia，你能听见我吗？
```

Verify:

- native STT recognized
- Claude response completed
- TTS played completely
- exactly one rearm triggered
- Claude entered next recording-ready state

Round 2:

```text
我们刚才正在测试什么？
```

Verify:

- same Claude session
- context continuity preserved
- no TTS feedback captured as user input
- no empty prompt submitted

Round 3:

```text
下一步还需要验证什么？
```

Then disable:

```text
/ptt-auto-rearm-off
/voice off
```

Verify:

- no further rearm
- no orphan helper process
- Claude client remains usable
- text input remains normal

## Manual Evidence Summary Tool

After real testing, run:

```bash
cd /Users/admin/Claude_Julia_Project
scripts/cv12_real_gate_summary.py \
  --turns-expected 3 \
  --manual-native-stt-ok \
  --manual-session-preserved
```

If TTS feedback was detected, add:

```text
--manual-tts-feedback-detected
```

Summary output:

```text
/Users/admin/Claude_Julia_Project/tmp/ptt_rearm/cv12_real_gate_summary.json
```

## Freeze Upgrade Condition

If the real three-round gate passes, upgrade to:

```text
Decision: ACCEPT
Status: APPROVED / FROZEN
```

Required PASS fields:

- Native PTT Input
- Claude Session Continuity
- Stop Hook TTS
- PTT Auto-Rearm
- Duplicate Protection
- Foreground Guard
- Cognitive Independence
- Real Client Three-Turn Loop
