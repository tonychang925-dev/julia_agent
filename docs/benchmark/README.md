# Julia Agent Benchmark Layer

Status: FROZEN-SCOPE / ACTIVE-STARTING  
Strategy: Julia Agent Evolution Strategy v1.0  
Boundary ADRs: ADR-021, ADR-022

## Purpose

This directory is the shared裁判层 for comparing:

```text
Claude Julia Reference Client  ->  Golden Reference / Benchmark System
julia_agent Replacement System ->  Runtime-owned Product System
```

Benchmark assets live here because they must not belong to either cognitive system.

## Hard Boundary

**Benchmark can be shared; cognition must not be shared.**

Allowed in this directory:

- benchmark prompts
- scenario definitions
- trace schemas
- latency metrics
- scoring rubrics
- comparison reports

Not allowed in this directory:

- Claude Context / Memory / Tool state as Julia Runtime authority
- Julia Context OS / Memory OS / Action OS as Claude Julia benchmark runtime
- provider prompt adapters
- governed memory writes
- identity or relationship authority mutation

## Directory Layout

```text
docs/benchmark/
├── claude_reference/
│   ├── CV1_REFERENCE_CLIENT_ACTIVATION.md
│   ├── context_cases.md
│   ├── memory_cases.md
│   └── voice_cases.md
├── julia_agent/
│   └── README.md
└── comparison/
    └── README.md
```

## Track Definition

### Phase CV — Claude Reference Track

- CV-1 Reference Client Activation
- CV-2 Benchmark Harness
- CV-3 Capability Baseline

### Phase J — Julia Replacement Track

- J-4 Client Shell
- J-5 Capability Parity
- J-6 Julia Agent Alpha
- J-7 Claude Replacement Candidate

## Trace Principle

Every reference run should emit JSONL evidence from day one. Minimum fields:

```json
{
  "timestamp": "",
  "system": "claude_julia_reference",
  "session_id": "",
  "turn": 0,
  "case_id": "",
  "input_mode": "voice|text",
  "stt_ms": 0,
  "first_token_ms": 0,
  "response_ms": 0,
  "tts_start_ms": 0,
  "turn_duration_ms": 0,
  "context_behavior": "",
  "memory_behavior": "",
  "tool_usage": "",
  "notes": ""
}
```
