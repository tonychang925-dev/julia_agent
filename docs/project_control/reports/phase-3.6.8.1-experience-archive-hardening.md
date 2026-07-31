# Phase 3.6.8.1 — Experience Archive Hardening

Date: 2026-07-28
Status: PASS

## Purpose

Harden the Conversation Experience Archive before any compaction work.

Key boundary:

```text
Experience Archive ≠ Runtime Log
```

## Implemented

### 1. Experience / Runtime Trace Separation

Experience archive:

```text
data/conversation_archive/transcripts.jsonl
```

Stores only Julia-lived experience:

- user text,
- assistant text,
- cognitive mode,
- topics,
- open loops,
- current arc,
- experience metadata,
- archive provenance.

Runtime trace:

```text
data/runtime_trace/runtime_events.jsonl
```

Stores machine execution facts:

- backend,
- audio/TTS status,
- latency,
- state trace.

### 2. Experience Classification

Added:

```text
runtime/conversation_archive/experience_classifier.py
```

Produces:

```json
{
  "experience_type": ["technical", "decision", "relationship", "emotion", "milestone", "casual"],
  "importance_hint": {
    "emotional": 0.0,
    "technical": 0.0,
    "relationship": 0.0,
    "project": 0.0
  },
  "archive_priority": 0.1,
  "reflection_candidate": false
}
```

This metadata is not Memory. It is archive metadata for later Reflection and Compression.

### 3. Archive Query API

Added:

```text
runtime/conversation_archive/archive_query.py
```

Supports:

- text filter,
- session filter,
- experience_type filter,
- reflection_candidate filter,
- minimum archive priority,
- latest reflection candidates.

This is a lexical/filter API for Phase 3.6.8.1. Semantic retrieval is deferred to Phase 3.6.10.

## Tests

Added:

```text
tests/test_phase3681_experience_archive_hardening.py
tests/test_phase3681_archive_query_api.py
```

Validation:

```text
Experience Archive excludes backend/audio/latency.
Runtime Trace preserves backend/audio/latency.
ExperienceClassifier marks technical/decision/milestone turns.
ArchiveQueryEngine retrieves typed experience records.
```

## Next

Do not immediately compact. First collect real voice/session archive data.

Next implementation target:

```text
Phase 3.6.9 — Cognitive Experience Compression Runtime
```

But only after enough real archive records exist to guide the compact schema.
