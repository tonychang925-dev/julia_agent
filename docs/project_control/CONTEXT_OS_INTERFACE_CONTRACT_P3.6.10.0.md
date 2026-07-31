# Phase 3.6.10.0 — Context OS Interface Contract Freeze

**Date**: 2026-07-28  
**Status**: FROZEN FOR IMPLEMENTATION READINESS REVIEW  
**Scope**: Interface contracts only. No runtime implementation in this phase.

---

## 1. Readiness Review Conclusion

Phase 3.6.10 is not a normal feature module. It becomes the mandatory path before every provider request:

```text
User Input
  ↓
Julia Cognitive Runtime
  ↓
Context OS
  ↓
JuliaContext
  ↓
Provider
```

Therefore implementation must not start from individual modules like retrieval or transcript persistence. It must first freeze the interface contracts that all downstream modules depend on.

Phase 3.6.10.0 freezes five contracts:

```text
ContextMessageRecord
ContextPlan
ContextBlock
ContextQuality
ContextOS API
```

And adds two runtime principles:

```text
Conversation Truth Layer
Context Conflict Resolver
```

---

## 2. Phase 3.6.10 Final Order

Frozen implementation order:

```text
Phase 3.6.10.0 Context OS Interface Contract Freeze
        ↓
Phase 3.6.10.1 Transcript Lifecycle Runtime / Conversation Truth Layer
        ↓
Phase 3.6.10.2 Context Planner + Context Quality
        ↓
Phase 3.6.10.3 Context Budget Manager
        ↓
Phase 3.6.10.4 Structured Compact Runtime
        ↓
Phase 3.6.10.5 Semantic Evidence Integration
        ↓
Phase 3.6.10.6 Session Resurrection Runtime
        ↓
Phase 3.6.10.7 Async Session Memory Worker
```

Rationale:

```text
First freeze what a conversation event means.
Then decide what this turn needs.
Then evaluate whether the planned context is healthy.
Then budget it.
Then compact, retrieve, resurrect, and asynchronously learn.
```

---

## 3. Conversation Truth Layer

### 3.1 Motivation

Julia currently has multiple history-bearing systems:

```text
Conversation Archive
Memory Runtime
Evidence Layer
Claude Diary
Runtime Trace
```

But it lacks a canonical lifecycle record for model-facing conversation truth.

Conversation Archive answers:

```text
What happened?
```

Memory Runtime answers:

```text
What has been governed into long-term memory?
```

Evidence Layer answers:

```text
What source supports this fact?
```

Conversation Truth Layer answers:

```text
What should Julia treat this message as in the context lifecycle?
```

### 3.2 ContextMessageRecord

```python
@dataclass(frozen=True)
class ContextMessageRecord:
    message_id: str
    session_id: str
    turn_id: int

    speaker: Literal["USER", "ASSISTANT", "SYSTEM"]
    content: str

    lifecycle_state: Literal[
        "ACTIVE",
        "COMPRESSED",
        "ARCHIVED",
        "RETRIEVED",
        "DROPPED",
    ]

    cognitive_role: Literal[
        "identity",
        "relationship",
        "task",
        "evidence",
        "decision",
        "emotion",
        "casual",
        "runtime",
    ]

    authority_score: float
    importance_score: float
    topics: list[str]
    source_refs: list[str]

    created_at: str
    updated_at: str | None
```

### 3.3 Lifecycle State Semantics

| State | Meaning | Model-facing behavior |
|---|---|---|
| ACTIVE | Recent message still needed as raw conversation tail | Eligible by default |
| COMPRESSED | Covered by a compact object | Excluded unless source trace needed |
| ARCHIVED | Saved as raw experience | Excluded by default, retrievable |
| RETRIEVED | Brought back for current turn | Included for this turn only |
| DROPPED | Runtime noise or unsafe low-value content | Never included as cognitive fact |

### 3.4 Authority Defaults

| Source | Authority |
|---|---:|
| Tony current explicit input | 1.0 |
| Governed Memory | 0.95 |
| Archive USER message | 0.9 |
| Claude Diary | 0.8 |
| Archive ASSISTANT message | 0.3 |
| Model inference | 0.1 |
| Runtime trace | 0.0 model-facing |

---

## 4. Context Planner Contract

### 4.1 Principle

Context Planner must not be keyword-trigger based.

Incorrect:

```text
小红书 → xiaohongshu_story
```

Correct:

```text
User asks about a shared past experience
  ↓
intent = retrieve_shared_life_experience
  ↓
evidence_intents = personal_story / creative_work / relationship_origin
  ↓
Evidence Layer resolves concrete sources
```

### 4.2 ContextPlan

```python
@dataclass(frozen=True)
class ContextPlan:
    plan_id: str
    query: str
    session_id: str
    cognitive_mode: str

    primary_intent: Literal[
        "identity_question",
        "relationship_question",
        "current_task_question",
        "retrieve_shared_life_experience",
        "technical_debug",
        "planning",
        "emotional_support",
        "private_voice_continuity",
        "casual",
    ]

    required_blocks: list[str]
    optional_blocks: list[str]
    evidence_intents: list[str]
    excluded_blocks: list[str]

    target_budget_tokens: int
    planner_confidence: float
    reason: str
```

### 4.3 Planner Example

For:

```text
我记得那个你以前分享给我的人生故事
```

Expected plan:

```json
{
  "primary_intent": "retrieve_shared_life_experience",
  "required_blocks": ["core_identity", "relationship_anchor"],
  "optional_blocks": ["recent_turns", "semantic_evidence", "compact_state"],
  "evidence_intents": ["personal_story", "creative_work", "relationship_origin"],
  "excluded_blocks": ["runtime_trace", "assistant_generated_history"],
  "planner_confidence": 0.75
}
```

---

## 5. ContextBlock Contract

```python
@dataclass(frozen=True)
class ContextBlock:
    block_id: str
    block_type: Literal[
        "core_identity",
        "relationship_anchor",
        "active_task",
        "session_state",
        "recent_turns",
        "semantic_evidence",
        "compact_state",
        "open_loops",
        "runtime_instruction",
    ]

    priority: int
    estimated_tokens: int
    required: bool
    content: str

    source_refs: list[str]
    evidence_ids: list[str]
    authority_score: float

    included: bool
    exclusion_reason: str | None
```

Budget Manager consumes `ContextPlan` and candidate `ContextBlock[]`, then emits included/excluded blocks.

---

## 6. Context Quality Contract

### 6.1 ContextQuality

```python
@dataclass(frozen=True)
class ContextQuality:
    plan_id: str

    identity_coverage: float
    relationship_coverage: float
    task_coverage: float
    evidence_confidence: float
    budget_utilization: float
    hallucination_risk: float

    highest_authority: float
    evidence_count: int
    low_authority_evidence_count: int

    pass_gate: bool
    warnings: list[str]
```

### 6.2 Gate Rules

Initial rules:

```text
If identity_coverage < 0.8 for identity/relationship questions → fail gate.
If evidence_confidence < 0.6 for historical fact questions → warn or ask uncertainty-aware answer.
If highest_authority <= 0.3 for factual memory question → high hallucination risk.
If budget_utilization > 0.92 → trigger budget reduction or compact readiness.
If low_authority_evidence dominates → run Context Conflict Resolver.
```

---

## 7. Context Conflict Resolver Contract

### 7.1 Problem

Ranking is not enough. Evidence can conflict.

Example:

```text
Evidence A: Tony said he shared Xiaohongshu posts. authority=0.9
Evidence B: Julia previously guessed a wrong story. authority=0.3
Evidence C: Model inference guesses another story. authority=0.1
```

The correct action is not simply “top semantic score wins”. The resolver must decide which source becomes model-facing fact.

### 7.2 Resolver API

```python
class ContextConflictResolver:
    def resolve(self, evidence_group: list[EvidenceChunk]) -> ResolvedEvidenceGroup:
        ...
```

```python
@dataclass(frozen=True)
class ResolvedEvidenceGroup:
    accepted: list[str]
    rejected: list[str]
    conflict_detected: bool
    resolution_rule: str
    confidence: float
```

### 7.3 Resolution Priority

```text
Tony explicit current fact
    >
Governed Memory
    >
Archive USER message
    >
Claude Diary
    >
Archive ASSISTANT response
    >
Model inference
```

---

## 8. ContextOS API Contract

```python
class JuliaContextOS:
    def ingest_event(self, event: ConversationEvent) -> ContextMessageRecord:
        ...

    def plan_context(
        self,
        query: str,
        session_id: str,
        cognitive_mode: str,
        provider: str,
    ) -> ContextPlan:
        ...

    def retrieve_blocks(self, plan: ContextPlan) -> list[ContextBlock]:
        ...

    def resolve_conflicts(self, blocks: list[ContextBlock]) -> list[ContextBlock]:
        ...

    def evaluate_quality(self, plan: ContextPlan, blocks: list[ContextBlock]) -> ContextQuality:
        ...

    def allocate_budget(self, plan: ContextPlan, blocks: list[ContextBlock]) -> list[ContextBlock]:
        ...

    def build_julia_context(self, plan: ContextPlan, blocks: list[ContextBlock]) -> JuliaContext:
        ...
```

Required call order:

```text
ingest_event
  ↓
plan_context
  ↓
retrieve_blocks
  ↓
resolve_conflicts
  ↓
evaluate_quality
  ↓
allocate_budget
  ↓
build_julia_context
```

---

## 9. Implementation Readiness Gate

Coding can start only when these are true:

```text
[ ] ContextMessageRecord schema frozen
[ ] ContextPlan schema frozen
[ ] ContextBlock schema frozen
[ ] ContextQuality schema frozen
[ ] ContextConflictResolver rules frozen
[ ] ContextOS API call order frozen
[ ] Test cases mapped to each contract
[ ] Existing ConversationArchive integration point identified
[ ] Existing EvidenceLayer integration point identified
[ ] DirectLLMBridge insertion point identified
```

---

## 10. Non-Goals

Phase 3.6.10.0 does not implement:

```text
No transcript migration
No compact generation
No semantic embedding changes
No provider changes
No memory object writes
No voice runtime changes
No Phase 3.7 action loop
```

---

## 11. Freeze Statement

Phase 3.6.10.0 freezes the Context OS interface boundary before implementation.

The most important architectural shift is:

```text
Memory Search is no longer the entry point.
Context Planning is the entry point.
```

Julia should not ask:

```text
What memory matches this keyword?
```

Julia should ask:

```text
What cognitive world does this turn require, and which sources are trustworthy enough to construct it?
```
