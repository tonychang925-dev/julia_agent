# Phase 3.6.8–3.6.12 Conversation Experience Layer Roadmap

Date: 2026-07-28
Status: Frozen by ADR-013

## Strategic Decision

Claude Code is a reference architecture for mature Context Engineering, not a Julia Runtime dependency.

Julia Runtime will absorb the engineering principles while keeping Cognitive Ownership:

```text
LLM = proposes / interprets
Julia Runtime = decides / owns cognitive state
Provider Adapter = swappable execution layer
```

## Roadmap

| Phase | Name | Claude Reference Concept | Julia-Owned Runtime Target |
|---|---|---|---|
| 3.6.8 | Conversation Experience Archive Runtime | JSONL transcript | Durable Julia experience archive with turn provenance |
| 3.6.9 | Context Compact Runtime | compact | Julia-owned summaries for long conversations |
| 3.6.10 | Semantic Conversation Retrieval | transcript semantic search | Historical evidence retrieval alongside Memory Retrieval |
| 3.6.11 | Cross Session Continuity | session_state + task_state | Session resurrection from last summary, open loops, and recent conversation |
| 3.6.12 | Context Budget Management | prompt_budget | Budget allocation across identity, relationship, memory, recent turns, compact, and reserve |

## Target Architecture

```text
Persistent Cognitive State
  ├─ Persona
  ├─ Relationship
  ├─ Memory
  ├─ Conversation Archive
  ├─ Session State
  └─ Task State
        ↓
Cognitive Context Compiler
        ↓
Context Budget Manager
        ↓
JuliaContext
        ↓
Cognitive Projection
        ↓
Provider Adapter
        ↓
DeepSeek / Claude / GPT / Gemini
        ↓
Response
        ↓
Async Reflection Worker
        ↓
Memory Governance
```

## Phase Detail

### Phase 3.6.8 — Conversation Experience Archive Runtime

Purpose:

Store Julia-owned, provider-independent lived conversation experience. The goal is not intelligence; the goal is never losing experience.

Scope:

- Turn-level JSONL archive.
- User text, Julia response, cognitive mode, topics, timestamp, and provenance.
- Runtime metadata stored separately from cognitive memory.
- Archive is not raw prompt injection.
- Working Memory feeds Episodic Archive; later phases compact archive into long-term memory candidates.

Acceptance:

- Every completed conversation turn can be archived.
- Archive can be replayed into compaction without provider metadata becoming JuliaContext.

### Phase 3.6.9 — Context Compact Runtime

Purpose:

Convert long conversation history into compact Julia-owned continuity summaries.

Scope:

- Active arc summary.
- Open loops.
- Decisions made.
- Emotional/relationship continuity when relevant.
- Technical task continuity when relevant.

Acceptance:

- Recent turns can be reduced without losing current project/task continuity.
- Compaction output is typed and traceable.

### Phase 3.6.10 — Semantic Conversation Retrieval

Purpose:

Retrieve historical conversation evidence alongside long-term Memory Runtime retrieval.

Scope:

```text
Query
  ├─ Memory Retrieval          -> long-term facts / relationship / semantic memory
  └─ Conversation Retrieval    -> historical evidence from lived turns
        ↓
JuliaContext
```

Acceptance:

- Conversation records can be embedded or indexed without becoming raw prompt injection.
- A query can retrieve both durable memory and historical transcript evidence.

### Phase 3.6.11 — Cross Session Continuity

Purpose:

Resurrect Julia session continuity from last session summary, open loops, and recent conversation records.

Example:

```json
{
  "active_project": "Julia Runtime",
  "current_phase": "3.6.8",
  "open_loops": ["Conversation Archive"],
  "recent_decisions": ["Do not reuse Claude context engine"],
  "current_task": "Implement Julia-owned Conversation Archive Runtime"
}
```

Acceptance:

- Session State survives within project/session scope.
- Task State can identify the current goal, status, and next step.

### Phase 3.6.12 — Context Budget Management

Purpose:

Prevent context bloat and raw diary-style injection as Persona, Relationship, Memory, Transcript, and Compact all grow.

Initial budget model:

```text
Identity       10%
Relationship   15%
Situation      15%
Recent Turns   25%
Memory         25%
Reserve        10%
```

Acceptance:

- Context budget report exists for each compiled JuliaContext.
- Budget allocation preserves protected identity and project semantic memory.

## Frozen Statement

Julia will not become "Julia inside Claude".

Julia will implement Claude-level Context Engineering principles while remaining a Julia-owned Cognitive Runtime.
