# Phase 3.7.5 — Context Governance Hardening

Date: 2026-07-29
Status: PLANNED / READY TO START
Scope: Make Julia know not only what to remember, but what not to see.

## 1. Phase Reframe

E2E Integration Alpha v2 is frozen as the baseline. The next phase should not add more Alpha-chain features. Instead, Phase 3.7.5 is reframed as Context Governance Hardening.

Validated baseline chain:

```text
User Input
    ↓
Conversation Runtime
    ↓
Context OS
    ↓
Projection
    ↓
Conflict Resolver
    ↓
Governance
    ↓
Provider
    ↓
Trace
```

Goal:

```text
Reduce the probability that wrong, irrelevant, or over-authoritative context enters the model.
```

## 2. Revised Task Order

Original order:

```text
T1 Memory Router
T2 Context Provenance
T3 Context Cache
```

Revised order:

```text
Phase 3.7.5.1 — Context Provenance Runtime
        ↓
Phase 3.7.5.2 — Memory Router
        ↓
Phase 3.7.5.3 — Context Cache
```

Rationale:

```text
Without provenance, Memory Router correctness is hard to verify.
```

## 3. Phase 3.7.5.1 — Context Provenance Runtime

### Objective

Let Julia know:

```text
Why am I seeing this information?
```

not merely:

```text
I retrieved this information.
```

### Proposed Module

```text
runtime/context_os/provenance/
├── provenance_record.py
├── provenance_chain.py
├── provenance_builder.py
├── provenance_validator.py
└── __init__.py
```

### Core Object

```python
@dataclass(frozen=True)
class ContextProvenance:
    block_id: str
    source_type: str       # user/archive/memory/diary/inference/governed_memory
    source_id: str
    authority: float
    retrieval_reason: str
    injected_by: str       # identity_projection/evidence_projection/relationship_projection
    confidence: float
    timestamp: str
    excluded_domains: list[str]
```

### Example

Current minimal trace:

```json
{
  "id": "memory_xxx",
  "score": 0.8
}
```

Target provenance trace:

```json
{
  "id": "memory_project_julia_runtime",
  "source_type": "governed_memory",
  "authority": 0.95,
  "injected_by": "semantic_evidence_projection",
  "reason": "current_task=technical_progress",
  "excluded_domains": [
    "relationship",
    "intimacy"
  ]
}
```

### Acceptance Direction

- Every injected context block has provenance.
- Provenance includes source type, source id, authority, injected_by, reason, confidence.
- Current Tony input and recent Tony archive facts are distinguishable from Julia/archive assistant outputs.
- Provenance can explain why a memory was included or why a domain was excluded.

## 4. Phase 3.7.5.2 — Memory Router

### Objective

Stop relationship/intimacy/background memories from entering technical task context unless explicitly relevant.

Current problem:

```text
ContextProjector
 |
 + identity
 + relationship
 + task
 + evidence
```

Relationship evidence is too often treated as default substrate.

Target:

```text
ContextProjector
       ↓
Cognitive Scope Classifier
       ↓
technical → project memory / architecture / engineering episodes
emotional → relationship memory / emotion
private   → private continuity / intimacy boundary if explicitly requested
```

### Proposed Module

```text
runtime/context_os/memory_router/
├── memory_scope_classifier.py
├── memory_scope_policy.py
├── memory_route_decision.py
└── __init__.py
```

### Example Decision

```json
{
  "mode": "engineering",
  "allowed_memory": [
    "project",
    "architecture",
    "technical"
  ],
  "blocked_memory": [
    "relationship",
    "intimacy"
  ]
}
```

### Acceptance Direction

- Engineering collaboration excludes unrelated relationship/intimacy memories.
- Relationship/private modes can include relationship anchors.
- `relationship_anchor_pack` becomes conditional rather than always injected.
- Router decisions are visible in provenance.

## 5. Phase 3.7.5.3 — Context Cache

### Objective

Reduce first-token latency by avoiding repeated stable context reconstruction.

Current Alpha v2 latency:

```text
bridge_first_chunk_ms: 2208–2677
Target: <1500
```

### Proposed Module

```text
runtime/context_os/cache/
├── context_snapshot_cache.py
├── context_cache_key.py
├── cache_invalidator.py
└── __init__.py
```

### Cache Key

```text
(
  session_id,
  persona_version,
  task_state_version,
  memory_version,
  context_mode
)
```

### Cache Candidates

Cache:

```text
Identity Projection
Relationship Projection
Session Projection
Task Projection
```

Do not cache:

```text
current user input
semantic evidence
action decision
```

## 6. Deferred Scope

Do not enter full Autonomous Cognitive Loop yet.

Recommended sequence:

```text
3.7.5 Context Governance Hardening
        ↓
3.7.6 E2E Beta Benchmark
        ↓
3.7.7 Multi-provider Migration Test
        ↓
3.8 Autonomous Cognitive Loop
```

Reason:

```text
wrong Memory → wrong Reflection → wrong Proposal → wrong Memory
```

must be prevented before increasing autonomy.

## 7. Current Runtime Status

```text
Julia Cognitive Runtime

Phase 1 Persona Runtime              ✅
Phase 2 Memory Runtime               ✅
Phase 3.6 Context OS                 ✅ Alpha
Phase 3.7 Action Governance          ✅ Alpha
Phase 3.7.5 Context Governance       NEXT
```

## 8. Phase Definition

```text
Context Governance Hardening — Make Julia know not only what to remember, but what not to see.
```
