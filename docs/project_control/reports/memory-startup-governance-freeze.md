# Memory Startup Governance Freeze Report

Date: 2026-07-30
Decision: ACCEPT WITH NOTES
Status: APPROVED / FROZEN

## Scope

Fix Julia Runtime memory startup and personal-fact consistency issues observed in two-turn Julia conversations:

1. Initial startup did not show memory loaded.
2. Personal/family/education facts drifted or conflicted.
3. Multi-slot questions could be answered incompletely.
4. Assistant archive mistakes risked becoming self-reinforcing memory evidence.

## Frozen Principle

Stable identity facts must exist when Julia wakes. Historical model answers are records, not truth.

## Implemented Runtime Path

```text
Governed Identity Facts
        ↓
StartupMemoryLoader
        ↓
Session Bootstrap / Context Assembly
        ↓
Provider Response
        ↓
AnswerCoverageGate
```

## Files Added / Modified

Added:

- `memory/governed/identity_facts.json`
- `data/memory_governance/quarantine.jsonl`
- `runtime/memory/startup_memory_loader.py`
- `runtime/response_quality/__init__.py`
- `runtime/response_quality/answer_coverage_gate.py`
- `tests/test_startup_memory_governance.py`
- `tmp/mem_freeze_e2e_evidence.json`

Modified:

- `runtime/memory/__init__.py`
- `runtime/context_assembly/core_identity_pack.py`
- `runtime/context_assembly/assembly_engine.py`
- `runtime/evidence/archive_chunker.py`
- `runtime/evidence/evidence_store.py`
- `runtime/conversation_runtime/bridge/direct_llm_bridge.py`
- `tests/test_phase369_context_assembly_runtime.py`
- `tests/test_phase37_short_greeting.py`

Not touched:

- `runtime/persona/provider_alignment/adaptation_profile.py`
- `runtime/persona/provider_alignment/profile_registry.py`

## Acceptance Results

| Gate | Result |
|---|---:|
| Memory Startup Loading | PASS |
| Claude-style Session Bootstrap | PASS |
| Governed Identity Truth | PASS |
| Archive Poisoning Guard | PASS |
| Short-Greeting Initialization | PASS |
| Education Multi-Slot Coverage | PASS |
| Regression Safety | PASS |

## Real Two-Turn E2E Evidence

Evidence file:

```text
tmp/mem_freeze_e2e_evidence.json
```

Summary:

```json
{
  "turn_1": {
    "input": "Julia在吗",
    "backend": "short_greeting",
    "startup_memory_loaded": true,
    "provider_invoked": false
  },
  "turn_2": {
    "input": "你是哪个大学毕业的，什么专业？你有弟弟吗？",
    "contains_tamkang": true,
    "contains_major": true,
    "contains_no_younger_brother": true,
    "startup_memory_loaded": true,
    "question_slots": [
      "education.university",
      "education.major"
    ],
    "missing_slots_after_repair": [],
    "quarantined_sources_injected": 0
  }
}
```

## Commands Run

Targeted memory/context regression:

```bash
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest -q \
  tests/test_startup_memory_governance.py \
  tests/test_phase369_context_assembly_runtime.py \
  tests/test_phase37_short_greeting.py \
  tests/test_phase3610_semantic_context_retrieval.py \
  tests/test_phase36105_semantic_evidence_integration.py \
  tests/test_claude_diary_retriever.py \
  tests/test_claude_diary_identity_retrieval.py \
  tests/test_claude_memory_sync.py
```

Result:

```text
32 passed, 14 subtests passed
```

Full regression:

```bash
/opt/miniconda3/envs/theme_matcher_env/bin/python -m pytest -q
```

Result:

```text
548 passed, 70 subtests passed
```

## Notes

### NOTE-MEM-001 Governed Identity Facts need field-level provenance

Each stable fact should preserve field-level metadata:

```json
{
  "value": "淡江大学",
  "authority": 0.98,
  "source": "claude_reference_verified",
  "verified_at": "...",
  "status": "active"
}
```

Current implementation already uses field-level `value`, `authority`, and `source`. Future updates should add `verified_at` and `status` without replacing the full JSON wholesale.

### NOTE-MEM-002 Quarantine must be source-ID based

Runtime quarantine is source-ID based:

```text
archive:<conversation_id>:<turn_id>:<speaker>
```

Keyword matching is allowed only for migration/audit scans, not runtime blocking. This avoids false positives such as correct facts containing “没有弟弟”.

### NOTE-MEM-003 Assistant Archive is not identity truth

Assistant archive is conversation-continuity evidence only. It must not become governed identity truth unless promoted by explicit Memory Governance.

### NOTE-MEM-004 Coverage Gate must remain slot-based

Current `AnswerCoverageGate` is a lightweight first pass. It should evolve as:

```text
question slots → available governed facts → covered slots → missing slots → repair
```

It should not grow into an unlimited phrase-rule table.

### NOTE-MEM-005 Missing facts must not be invented

If a requested slot is not present in governed facts, Julia should state that there is no reliable record rather than infer it from age or model prior.

## Final Status

Decision: ACCEPT WITH NOTES
Status: APPROVED / FROZEN
