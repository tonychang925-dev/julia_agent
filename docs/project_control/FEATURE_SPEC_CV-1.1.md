# FEATURE SPEC CV-1.1 — Continuous Voice Mode `/voice`

Status: REWORK / CLIENT SURFACE MISALIGNED  
Date: 2026-07-30  
Superseded by: `FEATURE_SPEC_CV-1.2.md`

## Decision

The previous CV-1.1 direction is rejected as the formal product/reference path.

Reason: it created a parallel Python CLI (`scripts/claude_reference_client.py`) and a custom continuous voice loop instead of preserving the Claude Code native client surface.

## Preserved Artifacts

The following may remain as test harness or fallback experiments only:

```text
/Users/admin/Claude_Julia_Project/scripts/claude_reference_client.py
/Users/admin/Claude_Julia_Project/client/voice_mode_controller.py
/Users/admin/Claude_Julia_Project/client/command_router.py
/Users/admin/Claude_Julia_Project/scripts/claude_voice_daemon.py
/Users/admin/Claude_Julia_Project/scripts/claude_voice_ctl.sh
```

They are not the accepted Claude Julia Reference Client entrypoint.

## Corrected Direction

Formal voice path is now:

```text
Phase CV-1.2 — Claude Native PTT Voice + TTS Auto-Rearm
```

Accepted constraints:

- Claude native `/voice tap` remains the voice input surface.
- Stop Hook provides TTS output.
- Optional auto-rearm only triggers one guarded PTT key after TTS completion.
- No custom STT loop.
- No external Claude client.
- No AppleScript prompt injection watcher.
- No Julia Runtime imports.
