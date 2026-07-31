# TEST CASE SPEC CV-1.1 — Continuous Voice Mode `/voice`

Status: REWORK / SUPERSEDED  
Date: 2026-07-30  
Superseded by: CV-1.2 native PTT tests.

## Rejected Test Scope

The previous tests validated a parallel Python reference client and custom continuous loop. Those tests may remain as harness regression coverage but no longer define formal acceptance.

## Replacement Acceptance Scope

Use CV-1.2 test cases instead:

- CV-PTT-001 Auto-rearm control state on/off/status
- CV-PTT-002 Disabled rearm skips
- CV-PTT-004 Stop Hook TTS trace + rearm schedule
- CV-PTT-007 Duplicate response triggers only one rearm
- CV-PTT-008 `stop_hook_active` guard
- CV-PTT-009 No Julia Runtime imports and no `claude -p`

Command:

```bash
cd /Users/admin/Claude_Julia_Project
python3 -m unittest tests/test_cv12_native_ptt_auto_rearm.py -v
```
