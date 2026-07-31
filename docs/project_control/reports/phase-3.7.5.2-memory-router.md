# Phase 3.7.5.2 — Memory Router

Date: 2026-07-29
Status: READY FOR REVIEW
Scope: route retrieved memories by cognitive scope, provenance, governance class, and injection eligibility

## Objective

Memory Router is not designed to find more memory. It decides which retrieved memories are eligible to enter the current cognitive scope.

Frozen principle:

```text
Retrieval ≠ Injection.
Semantic score may surface a candidate, but Memory Router decides whether it can be seen.
```

Core chain:

```text
Memory Object / Evidence Chunk
       ↓
Governance / Memory Class
       ↓
Provenance
       ↓
Current Cognitive Scope
       ↓
MemoryRouteDecision
       ↓
inject / suppress / defer
```

## Implemented Modules

```text
runtime/context_os/memory_router/
├── memory_route_decision.py
├── memory_scope_classifier.py
├── memory_scope_policy.py
└── __init__.py
```

### MemoryRouteDecision

Implemented immutable route decision:

```python
@dataclass(frozen=True)
class MemoryRouteDecision:
    memory_id: str
    action: str          # inject / suppress / defer
    scope: str           # engineering / emotional / relationship / learning / planning
    reason: str
    provenance_required: bool
    confidence: float
    memory_class: str | None = None
    allowed_domains: tuple[str, ...] = ()
    blocked_domains: tuple[str, ...] = ()
    provenance_id: str | None = None
```

### MemoryScopeClassifier

Implemented first-pass scope classification:

- `engineering`
- `planning`
- `emotional`

Engineering/planning scopes allow project, architecture, technical, normal episode, and behavior preference memories.

Emotional scope allows relationship, emotion, personal continuity, and behavior preference memories.

### MemoryScopePolicy

Implemented final injection policy:

- missing provenance → `suppress`
- unsupported provenance source → `suppress`
- cognitive scope mismatch → `suppress`
- archival/temp event → `defer`
- scope + provenance allowed → `inject`

Supported provenance sources for routed evidence:

- `GOVERNED_MEMORY`
- `CONVERSATION_ARCHIVE`
- `CLAUDE_DIARY`

## Semantic Retriever Integration

`runtime/evidence/semantic_retriever.py` now performs:

```text
retrieve candidates
    ↓
build provenance records
    ↓
classify cognitive scope
    ↓
route each candidate
    ↓
render only injected evidence
    ↓
record suppressed/deferred evidence as exclusion provenance
```

Important correction made during implementation:

```text
Suppressed evidence must not be rendered into the provider prompt.
```

The prompt section now renders `included_ranked` only, while excluded records remain available in `provenance_chain` for audit.

Metadata added:

```json
{
  "scope_decision": {},
  "route_decisions": [],
  "provenance_chain": {},
  "provenance_validation": {}
}
```

## Context Assembly Integration

`runtime/context_assembly/source_memory_resolver.py` now passes the current cognitive mode into `SemanticContextRetriever.prompt_section(...)`, allowing evidence routing to depend on runtime scope rather than raw retrieval score alone.

## Acceptance Tests

| TC | Name | Result |
| --- | --- | --- |
| TC-3752-001 | Engineering Isolation | PASS |
| TC-3752-002 | Emotional Scope | PASS |
| TC-3752-003 | Same Memory Different Scope | PASS |
| TC-3752-004 | Provenance Enforcement | PASS |
| TC-3752-005 | Retrieval ≠ Injection | PASS |
| TC-3752-006 | Semantic Retriever Route Metadata | PASS |
| TC-3752-007 | Suppressed Memory Not Rendered | PASS |

## Verification

### Phase 3.7.5.2 targeted

```text
Ran 7 tests in 0.449s
OK
```

### Context Governance / E2E boundary regression

Command covered:

- Phase 3.7.5.2 Memory Router
- Phase 3.7.5.1 Context Provenance Runtime
- E2E Alpha input/routing fixes
- E2E Alpha continuity guard
- Action E2E Alpha Runtime
- Phase 3.6.10.15 Context OS Integration Benchmark

```text
Ran 36 tests in 2.381s
OK
```

### Full regression

```text
Ran 458 tests in 54.183s
OK
```

## Boundary Notes

NOTE-3752-001
Memory Router consumes provenance. It does not operate on raw retrieval candidates alone.

NOTE-3752-002
Retrieval score is not authority and does not imply prompt injection.

NOTE-3752-003
Suppressed memories remain auditable through exclusion provenance but are not rendered into provider context.

NOTE-3752-004
The same memory may route differently under different cognitive scopes.

NOTE-3752-005
Engineering/planning contexts suppress relationship/private/intimacy memories unless explicitly routed by a future higher-level policy.

NOTE-3752-006
Memory Router is a Context Governance layer, not a Memory Search layer.

## Current Status

Phase 3.7.5.2 — Memory Router is implementation-complete and regression-clean.

Recommended review decision:

```text
Decision: ACCEPT
Status: APPROVED / FROZEN
Freeze Note:
Memory Injection Boundary Established.
Retrieved Memory Requires Scope, Provenance, and Route Approval Before Context Injection.
```

## Next Candidate Phase

Phase 3.7.5.3 — Context Cache

Primary goal:

```text
Reduce repeated Context OS assembly cost without caching current user input,
semantic evidence route decisions, or action governance decisions.
```
