# Phase 3.7.5.3 — Context Cache

Date: 2026-07-29
Status: APPROVED / FROZEN
Scope: cache stable Context OS assembly substrate while preserving real-time evidence/governance boundaries

## Objective

Reduce repeated Context OS assembly cost without caching turn-specific or authority-sensitive decisions.

The first version caches only stable assembly sections:

```text
core_identity_pack
relationship_anchor_pack
conflict_resolver
```

The following are explicitly excluded from cache:

```text
current_user_input
semantic_evidence
memory_route_decisions
action_governance_decisions
provider_output
```

## Implemented Modules

```text
runtime/context_os/cache/
├── context_cache_key.py
├── context_snapshot_cache.py
├── cache_invalidator.py
└── __init__.py
```

### ContextCacheKey

Stable key over cache-safe identity/scope state.

For stable assembly sections, the key uses:

```text
session_id
persona_version
relationship_version
context_mode
component
```

and marks real-time states as excluded:

```text
task_state_version = excluded_from_stable_cache
memory_version = excluded_from_stable_cache
```

This is intentional: current task/open loops and semantic memory routes must be recomputed in real time.

### ContextSnapshotCache

Small deterministic in-memory cache with:

- hit/miss/write counters
- bounded size
- manual invalidation
- serializable stats

### ContextCacheInvalidator

Explicit invalidation helper for future versioned persona / relationship / memory snapshots.

## Integration

`runtime/context_assembly/assembly_engine.py` now performs:

```text
build stable cache key
      ↓
lookup stable assembly sections
      ↓
miss: build core_identity / relationship_anchor / conflict_resolver
hit: reuse stable sections
      ↓
always run SourceAwareMemoryResolver
      ↓
always run Semantic Retriever / Memory Router
      ↓
budget and render final context
```

This preserves the Phase 3.7.5.1 and 3.7.5.2 boundaries:

```text
Provenance remains mandatory.
Memory Router still decides injection every turn.
Suppressed evidence is not rendered.
Provider output is never cached as evidence.
```

## Trace Metadata

Context assembly metadata now includes:

```json
{
  "cache": {
    "enabled": true,
    "status": "hit | miss",
    "component": "context_assembly_stable_sections.v1",
    "key_digest": "...",
    "key": {},
    "cached_sections": [],
    "excluded_from_cache": [
      "current_user_input",
      "semantic_evidence",
      "memory_route_decisions",
      "action_governance_decisions",
      "provider_output"
    ],
    "stats": {}
  }
}
```

## Acceptance Tests

| TC | Name | Result |
| --- | --- | --- |
| TC-3753-001 | Stable Assembly Cache Miss → Hit | PASS |
| TC-3753-002 | Current User Input Not In Stable Cache Key | PASS |
| TC-3753-003 | Semantic Evidence / Routes Not Cached | PASS |
| TC-3753-004 | Context Mode Change Creates New Cache Key | PASS |
| TC-3753-005 | Manual Invalidation Clears Cache | PASS |
| TC-3753-006 | Cache Metadata Serializes For Trace | PASS |

## Verification

### Phase 3.7.5.3 targeted

```text
Ran 6 tests in 1.970s
OK
```

### Context Governance boundary regression

Covered:

- Phase 3.7.5.3 Context Cache
- Phase 3.7.5.2 Memory Router
- Phase 3.7.5.1 Context Provenance Runtime
- E2E Alpha input/routing fixes
- E2E Alpha continuity guard
- Action E2E Alpha Runtime
- Context OS Integration Benchmark
- Context Assembly Runtime

```text
Ran 46 tests in 10.540s
OK
```

### Full regression

```text
Ran 464 tests in 69.266s
OK
```

## Boundary Notes

NOTE-3753-001
Context Cache caches stable substrate only. It does not cache current user input.

NOTE-3753-002
Semantic evidence and Memory Router decisions remain real-time and are excluded from stable cache.

NOTE-3753-003
Action governance decisions and provider output are never cacheable context evidence.

NOTE-3753-004
Context mode is part of the stable cache key; emotional and engineering contexts do not share relationship-anchor cache entries.

NOTE-3753-005
Cache metadata is visible in Context Assembly trace for audit and latency diagnosis.

NOTE-3753-006
Manual invalidation is available; future versioned stores can wire persona/relationship/memory version changes into invalidation policy.

## Current Status

Phase 3.7.5.3 — Context Cache is implementation-complete and regression-clean.

Final decision:

```text
Decision: ACCEPT
Status: APPROVED / FROZEN
Freeze Note:
Stable Context Assembly Cache Established.
Real-Time Evidence, Memory Routing, Governance, and Provider Output Remain Uncached.
```

## Next Candidate Gate

Phase 3.7.5 — Context Governance Hardening can now be reviewed as a combined milestone:

```text
3.7.5.1 Context Provenance Runtime ✅
3.7.5.2 Memory Router ✅
3.7.5.3 Context Cache ✅
```

## Final Acceptance Notes

NOTE-3753-001 Cache Key Integrity
Future ContextCacheKey versions should include persona_version, relationship_version, invariant_schema_version, conflict_policy_version, and context_mode. Session or user identity alone is not sufficient for cache safety.

NOTE-3753-002 Precision Invalidation First
ContextCacheInvalidator should prefer dependency/version-driven invalidation over broad clearing or TTL-only invalidation.

NOTE-3753-003 Cache Provenance
Cache-hit trace should preserve cache key, cached sections, created_at, and original section provenance. Cached content must not lose lineage.

NOTE-3753-004 Cached Relationship Anchor Still Requires Scope Governance
Cache hit must not imply unconditional relationship-anchor injection. Cache optimizes construction; it must not bypass Memory Router / cognitive-scope governance.

