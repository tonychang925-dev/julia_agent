# Phase CV-1 — Claude Julia Reference Client Activation Scope

Status: SPEC-FROZEN / READY-FOR-IMPLEMENTATION  
Date: 2026-07-30

## Decision

CV-1 is upgraded from “Claude Julia Voice Activation” to “Claude Julia Reference Client Activation”.

Voice remains the first interaction channel, but acceptance requires benchmark trace evidence.

## Frozen Relationship

```text
Claude Julia Reference Client = Benchmark System
julia_agent Replacement System = Product System
```

## Deliverables Created

- `docs/benchmark/README.md`
- `docs/benchmark/claude_reference/CV1_REFERENCE_CLIENT_ACTIVATION.md`
- `docs/benchmark/claude_reference/context_cases.md`
- `docs/benchmark/claude_reference/memory_cases.md`
- `docs/benchmark/claude_reference/voice_cases.md`
- `docs/benchmark/julia_agent/README.md`
- `docs/benchmark/comparison/README.md`
- `docs/project_control/TEST_CASE_SPEC_CV-1.md`

## Acceptance Minimum

- CV-B001 Identity: one real trace.
- CV-B002 Recent Continuity: one real two-turn trace.
- CV-B005 Voice Experience: one real voice trace.
- Cognitive boundary fields must show no Julia Runtime cognitive imports.

## Runtime Code Impact

None. No `runtime/` or provider alignment code was modified.

---

# Implementation Addendum — Minimal Reference Runner

Status: MINIMAL IMPLEMENTED / LOCAL TESTS PASSED  
Implementation root: `/Users/admin/Claude_Julia_Project`

## Added Implementation Files

```text
/Users/admin/Claude_Julia_Project/
├── README.md
├── scripts/
│   ├── start_claude_reference_session.sh
│   ├── claude_reference_runner.py
│   └── claude_voice_session.py
├── voice/
│   ├── voice_protocol.py
│   ├── stt_adapter.py
│   └── tts_adapter.py
├── benchmark/
│   ├── trace_writer.py
│   ├── benchmark_runner.py
│   └── cases/cv1_cases.py
├── tests/test_cv1_boundary_and_trace.py
└── reports/CV1_IMPLEMENTATION_STATUS.md
```

## Local Validation

```bash
cd /Users/admin/Claude_Julia_Project
python3 -m unittest discover -s tests -v
```

Result: 2 tests OK.

## Boundary Result

- Direct Julia Runtime cognitive imports: none detected by AST boundary test.
- Runtime code modified: no.
- provider_alignment modified: no.

## Real Claude Run Status

Requires local `claude` CLI availability and session auth. If unavailable, CV-1 real run is BLOCKED, not mocked.

## Real Baseline Evidence — CV-B001/CV-B002 Text Suite

Command:

```bash
cd /Users/admin/Claude_Julia_Project
scripts/start_claude_reference_session.sh --run-suite cv1
```

Result: PASS / 3 traces written.

Evidence:

- `/Users/admin/Claude_Julia_Project/tmp/benchmarks/claude_reference/cv1/claude_julia_reference_runtime.jsonl`
- `/Users/admin/Claude_Julia_Project/reports/cv1_latest_text_suite_summary.json`

Observed results:

| Case | Status | Latency | Tool Used | Boundary |
|---|---:|---:|---:|---|
| CV-B001 | PASS | 4306 ms | False | clean |
| CV-B002-1 | PASS | 4790 ms | False | clean |
| CV-B002-2 | PASS | 5251 ms | False | clean |

Notes:

- CV-B001 identity now anchors to Claude Julia Reference Client via Claude-native `CLAUDE.md`.
- CV-B002 uses one explicit Claude session UUID and demonstrates recent continuity.
- Tools are disabled by default for CV-B001/CV-B002 to prevent reference activation from writing plans or modifying files.

## Real Baseline Evidence — Final CV-1 Minimal Baseline

### Text Suite

Command:

```bash
cd /Users/admin/Claude_Julia_Project
scripts/start_claude_reference_session.sh --run-suite cv1
```

Result: PASS / CV-B001 + CV-B002-1 + CV-B002-2.

| Case | Status | Latency | Tool Intent | Boundary |
|---|---:|---:|---:|---|
| CV-B001 | PASS | 3832 ms | False | clean |
| CV-B002-1 | PASS | 3262 ms | False | clean |
| CV-B002-2 | PASS | 4088 ms | False | clean |

### Voice/Fallback Suite

Command:

```bash
cd /Users/admin/Claude_Julia_Project
python3 scripts/claude_voice_session.py --case CV-B005 --skip-stt --fallback-text "Julia，你现在听得到我吗？" --tts-mode dry_run
```

Result: PASS / CV-B005 fallback trace.

Evidence:

- `/Users/admin/Claude_Julia_Project/tmp/benchmarks/claude_reference/cv1/claude_julia_reference_runtime.jsonl`
- `/Users/admin/Claude_Julia_Project/tmp/benchmarks/claude_reference/cv1/claude_julia_voice_baseline.jsonl`
- `/Users/admin/Claude_Julia_Project/reports/cv1_latest_clean_text_suite_summary.json`
- `/Users/admin/Claude_Julia_Project/reports/cv1_latest_voice_fallback_trace.jsonl`

Observed voice/fallback metrics:

- input.mode: `text_fallback`
- stt_error: `stt_skipped`
- claude.response_time_ms: `8964`
- output.tts_engine: `dry_run`
- output.tts_start_ms: `0`
- cognitive boundary: `clean`

### Remaining Manual Real-Voice Step

Real microphone capture is not yet accepted until Tony runs without `--skip-stt` and confirms macOS Microphone/Speech Recognition permissions. Current CV-B005 fallback proves the reference runner, Claude response, dry-run TTS, trace writer, and cognitive boundary.

---

# Gate Decision — CV-1 Minimal Baseline

Decision: ACCEPT WITH NOTES  
Status: MINIMAL BASELINE ACTIVE  
Freeze Level: PARTIAL / MIC VALIDATION PENDING  
Gate Date: 2026-07-30

## Accepted Evidence

The current CV-1 baseline proves three core properties:

1. Claude Reference Client independent execution is valid.
2. Claude native session continuity is valid for the text reference loop.
3. Cognitive Independence Boundary is valid.

Boundary evidence remains clean:

```json
{
  "julia_runtime_imported": false,
  "julia_memory_authority_used": false,
  "julia_context_authority_used": false,
  "julia_action_authority_used": false
}
```

## Frozen as Accepted

- Reference Client independent project structure.
- Claude text request/response loop.
- Claude native session continuity for CV-B002.
- Benchmark JSONL trace writer.
- dry-run TTS / fallback voice orchestration path.
- Cognitive boundary assertions.

## Accepted Test Results

| Case | Status | Scope |
|---|---:|---|
| CV-B001 Identity | PASS | real Claude text baseline |
| CV-B002-1 Recent Continuity seed | PASS | real Claude text baseline |
| CV-B002-2 Continue previous topic | PASS | real Claude session continuity |
| CV-B005 Voice fallback trace | PASS | fallback text -> Claude -> dry_run TTS -> trace |
| Boundary isolation | PASS | no Julia cognitive authority used |
| Trace writer | PASS | JSONL evidence generated |

## Explicit Non-Claim

CV-1 is not yet `APPROVED / FROZEN` because real microphone STT has not been manually validated.

Current CV-B005 proves:

```text
fallback text -> Claude -> dry_run TTS -> trace
```

It does not yet prove:

```text
Microphone -> Apple Speech Recognition -> STT text -> Claude -> real TTS playback
```

## NOTE-CV1-001

Real microphone STT pending manual macOS permission validation.

## Real Voice Gate

Manual command:

```bash
cd /Users/admin/Claude_Julia_Project
python3 scripts/claude_voice_session.py \
  --case CV-B005 \
  --tts-mode say
```

Required manual run set:

| Gate | Spoken Input | Expected Evidence |
|---|---|---|
| CV-B005-R1 | Julia，你能听见我吗？ | STT text, Claude response, audible TTS, trace |
| CV-B005-R2 | 我们刚才确认了什么？ | native session continuity, audible TTS, trace |
| CV-B005-R3 | restart, then: 继续我们刚才的语音测试。 | restart recovery behavior, trace |

Required real voice trace fields:

```json
{
  "benchmark_id": "CV-B005",
  "input_mode": "real_voice",
  "stt_authorized": true,
  "microphone_authorized": true,
  "stt_text": "",
  "stt_latency_ms": 0,
  "claude_response_latency_ms": 0,
  "tts_mode": "say",
  "tts_started": true,
  "tts_start_latency_ms": 0,
  "audio_playback_ok": true,
  "cognitive_boundary_clean": true,
  "manual_stt_accuracy_note": ""
}
```

## Upgrade Condition

After CV-B005-R1/R2/R3 pass with real microphone and audible TTS, CV-1 can upgrade to:

```text
Decision: ACCEPT
Status: APPROVED / FROZEN
Freeze Level: FULL
```
