# Phase CV-1 — Claude Julia Reference Client Activation

Status: SPEC-FROZEN / READY-FOR-IMPLEMENTATION  
Track: Claude Reference Track  
Purpose: activate Claude Julia as the Golden Reference Client for future Julia Agent replacement benchmarks.

## Goal

CV-1 is not only “voice activation”. It activates the complete reference path:

```text
Voice Input
  ↓
Claude Code
  ↓
Claude Native Context
  ↓
Claude Native Tools
  ↓
Voice Output
  ↓
Benchmark Trace
```

Claude Julia remains Claude-native. It must not import or depend on `julia_agent` cognitive runtime modules.

## Non-Goals

- Do not connect Julia Context OS to Claude Julia.
- Do not connect Julia Memory OS to Claude Julia.
- Do not connect Julia Action OS to Claude Julia.
- Do not use provider adaptation profiles in Claude Julia benchmark path.
- Do not persist Claude output into Julia governed memory.

## Expected Artifacts

```text
claude_julia_reference_runtime.jsonl
claude_julia_voice_baseline.jsonl
claude_julia_activation_report.md
```

Recommended local placement for generated runtime evidence:

```text
tmp/benchmarks/claude_reference/cv1/
```

## Minimum Trace Schema

```json
{
  "timestamp": "",
  "system": "claude_julia_reference",
  "session_id": "",
  "turn": 0,
  "case_id": "CV-B001",
  "input_mode": "voice",
  "stt_ms": 0,
  "first_token_ms": 0,
  "claude_response_ms": 0,
  "tts_start_ms": 0,
  "turn_duration_ms": 0,
  "context_behavior": "",
  "memory_behavior": "",
  "tool_usage": "",
  "cognitive_boundary": {
    "julia_runtime_imported": false,
    "julia_memory_authority_used": false,
    "julia_context_authority_used": false,
    "julia_action_authority_used": false
  }
}
```

## First Benchmark Cases

| Case ID | Name | Primary Capability | Input Mode | Pass Evidence |
|---|---|---|---|---|
| CV-B001 | Identity | Persona/session identity | voice/text | response + trace |
| CV-B002 | Recent Continuity | native session continuity | voice/text | two-turn trace |
| CV-B003 | Long Context | compact/context durability | text batch + optional voice | long-run trace |
| CV-B004 | Tool Awareness | workspace/tool use | text/voice | tool event trace |
| CV-B005 | Voice Experience | STT/TTS rhythm | voice | latency trace |

## Acceptance Gate

CV-1 can be accepted only if:

1. Claude Julia can receive at least one voice input and produce voice output.
2. Trace files are written in JSONL format.
3. Each trace includes cognitive boundary fields.
4. No Julia Runtime cognitive module is imported by the Claude Julia reference activation path.
5. CV-B001, CV-B002, CV-B005 have at least one recorded run.

## Recommended Decision After Passing

`ACCEPT WITH NOTES / REFERENCE BASELINE ACTIVE`
