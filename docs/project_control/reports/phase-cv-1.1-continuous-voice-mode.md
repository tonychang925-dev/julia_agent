# Phase CV-1.1 — Continuous Voice Mode `/voice`

Decision: REWORK  
Status: CLIENT SURFACE MISALIGNED  
Date: 2026-07-30

## Reason

The previous implementation created a parallel Python command-line client instead of adding or preserving the intended Claude Code native client surface.

Rejected entrypoint:

```text
python3 scripts/claude_reference_client.py --tts-mode say
```

This can remain as a test harness only, but it is not the Claude Julia product/reference client surface.

## Corrected Direction

Do not continue the custom continuous voice loop as the formal path.

The accepted replacement is:

```text
Phase CV-1.2 — Claude Native PTT Voice + TTS Auto-Rearm
```

Input remains Claude Code native `/voice tap`; output is added by Stop Hook TTS; optional auto-rearm triggers one guarded PTT key after TTS completes.
