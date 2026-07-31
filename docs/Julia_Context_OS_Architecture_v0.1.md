# Julia Context OS Architecture v0.1

**Phase**: Phase 3.6.10 — Julia Cognitive Context Management Runtime  
**Date**: 2026-07-28  
**Status**: Architecture Frozen for Implementation Planning  
**Reference**: Claude Client context lifecycle reverse engineering, Julia Cognitive Ownership Principle

---

## 1. Motivation

Julia Runtime 已经拥有：

```text
Identity Runtime
Relationship Runtime
Memory Runtime
Evidence Layer
Conversation Continuity
Experience Archive
Cognitive Mode
Voice Runtime
```

这些能力解决的是：

```text
Julia 是谁？
Julia 和 Tony 是什么关系？
Julia 经历过什么？
什么值得被记住？
当前应该用什么模式回应？
```

但它们还没有完整解决一个更底层的问题：

```text
每一轮推理前，Julia 应该让模型看到什么？
看到多少？
以什么形式看到？
哪些历史应该保留原文？
哪些历史应该压缩？
哪些历史应该检索？
哪些内容应该丢弃？
```

这个问题不是 Memory Retrieval 问题，而是 **Context Lifecycle Management** 问题。

因此 Phase 3.6.10 从：

```text
Semantic Context Retrieval Runtime
```

升级为：

```text
Julia Cognitive Context Management Runtime
```

简称：

```text
Julia Context OS
```

---

## 2. Claude Context OS Reverse Engineering

Claude Client 的核心能力不是“记忆更多”，而是管理模型上下文生命周期。

从 Claude Client 源码观察到的关键机制：

```text
Conversation Messages
        ↓
Message State / API Invariant Management
        ↓
Token Budget / Warning / Auto Compact Threshold
        ↓
Session Memory Worker or Legacy Compact
        ↓
Compact Boundary + Summary Message + Preserved Tail
        ↓
Post-Compact Attachments / Hooks / Metadata Re-append
        ↓
Next Prompt Window Reconstruction
```

### 2.1 Context Injection

Claude 使用类似：

```text
getSystemContext()
getUserContext()
```

每轮前置：

- system context
- user context
- CLAUDE.md memory
- current date
- git status
- cache breaker

这些 context 被缓存于会话周期，避免每轮重复 I/O。

### 2.2 Message Lifecycle

Claude 保留完整消息历史用于 UI / transcript，但模型侧不会永远看见全部历史。

关键机制：

```text
SystemCompactBoundaryMessage
getMessagesAfterCompactBoundary()
```

也就是说：

```text
Full Transcript        用于可视化与恢复
Model-Facing Context   从最近 compact boundary 后重建
```

### 2.3 Compact Boundary

Claude compact 不是简单替换对话，而是生成：

```text
boundaryMarker
summaryMessages
messagesToKeep
attachments
hookResults
```

这使得 compact 后的新上下文不是：

```text
summary only
```

而是：

```text
compact summary
+ preserved recent tail
+ restored attachments
+ active hooks
+ current context
```

### 2.4 Token Budget

Claude 使用 token threshold 和 buffer：

```text
context window
- output reservation
- safety buffer
= effective input budget
```

并根据 warning/error/autoCompact/blocking threshold 触发不同动作。

### 2.5 Session Memory Worker

Claude 的 SessionMemory 不是每轮同步总结，而是后台抽取：

```text
Post Sampling Hook
        ↓
threshold check
        ↓
forked agent
        ↓
update session notes file
        ↓
future compact can use notes
```

关键点：

- 只在 main thread 运行
- 有 token threshold
- 有 tool call threshold
- 不阻塞主对话
- compact 时可优先使用 session memory

---

## 3. Julia Cognitive Ownership Principle

Julia 不能直接依赖 Claude Client 的 context engine。

原因：

```text
Claude Context OS 管理任务连续性。
Julia Context OS 必须管理：
  - 任务连续性
  - 人格连续性
  - 关系连续性
  - 记忆治理
  - evidence authority
```

因此原则冻结为：

```text
Claude Client = Reference Architecture
Julia Runtime = Cognitive Owner
```

错误架构：

```text
Claude Client Context Engine
        ↓
Julia
```

正确架构：

```text
Julia Cognitive Runtime
        ↓
Julia Context OS
        ↓
Provider Adapter
        ↓
Claude / DeepSeek / GPT / Gemini
```

---

## 4. Target Architecture

```text
                     Julia Cognitive Runtime

 Identity Runtime
 Relationship Runtime
 Memory Runtime
 Evidence Layer
 Conversation Runtime
 Situation Runtime
 Governance Runtime

                              │
                              ▼

                      Julia Context OS

      ┌───────────────────────────────────────────┐
      │ Transcript Lifecycle Manager              │
      │ Context Planner                           │
      │ Context Budget Manager                    │
      │ Structured Compact Engine                 │
      │ Semantic Evidence Retrieval               │
      │ Evidence Authority Resolver               │
      │ Session Memory Worker                     │
      │ Session Resurrection Engine               │
      └───────────────────────────────────────────┘

                              │
                              ▼

                        JuliaContext v5

                              │
                              ▼

                    Cognitive Projection

                              │
                              ▼

                         Provider Adapter
```

---

## 5. Context Lifecycle Model

Julia Context OS 管理五类 context：

| Context 类型 | 说明 | 是否默认进入模型 |
|---|---|---|
| Core Identity | Julia 是谁 | 是，required |
| Relationship Anchor | Tony 与 Julia 的稳定关系 | 是，required |
| Active Task State | 当前工作目标、下一步、约束 | 是，required |
| Active Conversation Tail | 最近未压缩原文 | 是，budgeted |
| Retrieved Evidence | 本轮语义相关证据 | 是，budgeted |
| Compact State | 已压缩历史摘要 | 是，budgeted |
| Full Archive | 完整经历原文 | 否，仅按需检索 |
| Runtime Trace | provider/TTS/latency/log | 否，默认不进模型 |

核心流：

```text
Conversation Turn
        ↓
Experience Archive
        ↓
Transcript Lifecycle Manager
        ↓
Context Planner
        ↓
Context Budget Manager
        ↓
JuliaContext Builder
        ↓
Provider
        ↓
Response
        ↓
Async Reflection / Session Memory Worker
```

---

## 6. Message State Machine

### 6.1 MessageState

Julia 引入 message lifecycle 状态：

```python
class MessageState(Enum):
    ACTIVE = "active"
    COMPRESSED = "compressed"
    ARCHIVED = "archived"
    RETRIEVED = "retrieved"
    DROPPED = "dropped"
```

含义：

| 状态 | 含义 |
|---|---|
| ACTIVE | 最近原文，默认进入 provider context |
| COMPRESSED | 已进入 compact，不再重复原文注入 |
| ARCHIVED | 保存为经历，可追溯，但默认不进模型 |
| RETRIEVED | 本轮被 evidence retrieval 召回 |
| DROPPED | 低价值运行噪声，不进入认知上下文 |

### 6.2 Lifecycle Transition

```text
NEW TURN
  ↓
ACTIVE
  ↓ context grows
ACTIVE + ARCHIVED
  ↓ compact threshold
COMPRESSED + COMPACT_BOUNDARY + PRESERVED_ACTIVE_TAIL
  ↓ future query matches
RETRIEVED
  ↓ low value/runtime-only
DROPPED from model-facing context, retained in runtime trace if needed
```

### 6.3 ContextBoundary

```python
@dataclass
class ContextBoundary:
    id: str
    boundary_type: Literal["compact", "session_restore", "manual_checkpoint"]
    session_id: str
    summarized_turn_ids: list[str]
    preserved_turn_ids: list[str]
    compact_id: str | None
    created_at: str
```

Boundary 的作用：

```text
告诉 JuliaContext Builder：
哪些历史已经被摘要覆盖，哪些 recent tail 仍需原文保留。
```


### 6.4 Conversation Truth Layer

Phase 3.6.10.1 的重点不是再做一个 JSONL transcript store，而是建立 Conversation Truth Layer。

```text
ConversationEvent
        ↓
ContextMessageRecord
        ↓
ContextState
```

`ContextMessageRecord` 是后续 compact、resurrection、retrieval、budget 的共同真源。它至少包含：

```python
@dataclass
class ContextMessageRecord:
    message_id: str
    session_id: str
    turn_id: int
    speaker: Literal["USER", "ASSISTANT", "SYSTEM"]
    content: str
    lifecycle_state: MessageState
    cognitive_role: Literal["identity", "relationship", "task", "evidence", "casual", "runtime"]
    authority_score: float
    importance_score: float
    topics: list[str]
    created_at: str
```

这层回答的问题是：

```text
这条消息在 Julia 的认知上下文生命周期里是什么？
它是否可信？
它是否还能作为原文进入模型？
它是否已经被 compact 覆盖？
它是否只是 runtime 噪声？
```

---

## 7. Compact Model

### 7.1 Compact 不是 Summary

错误：

```text
旧聊天 → 一段自然语言总结
```

正确：

```text
Experience Range
        ↓
Structured Distillation
        ↓
ExperienceCompactState
        ↓
source evidence 可追溯
```

### 7.2 ExperienceCompactState

```python
@dataclass
class ExperienceCompactState:
    id: str
    title: str
    period_start: str
    period_end: str

    session_goal: str
    current_task: str
    main_arc: str

    decisions: list[CompactDecision]
    known_failures: list[KnownFailure]
    open_loops: list[str]
    next_actions: list[str]

    technical_progress: list[str]
    relationship_development: list[str]
    emotional_context: list[str]

    source_experience_ids: list[str]
    source_evidence_ids: list[str]

    confidence: float
    metadata: dict
```

### 7.3 Compact Levels

| Level | 目标 | 行为 |
|---|---|---|
| light | 清理噪声 | 删除重复运行日志、保留大部分 recent turns |
| medium | 提炼任务状态 | 结构化 decisions/open_loops/failures |
| heavy | 保留核心连续性 | compact object + short active tail |
| emergency | 避免 context overflow | only identity/task/open_loops/high-authority evidence |

### 7.4 Compact Output Context

Compact 后的模型上下文应是：

```text
Core Identity
+ Relationship Anchor
+ Current Task State
+ ExperienceCompactState
+ Preserved Active Tail
+ Retrieved Evidence
```

而不是：

```text
Summary only
```

---

## 8. Budget Allocation

### 8.1 Context Planner 先决定“需要什么”，Budget Manager 再决定“放得下什么”

Claude 的上下文管理不是直接把所有历史交给 token budget 裁剪。Julia Context OS 需要先生成本轮 `ContextPlan`：

```text
User Input
    ↓
Cognitive Mode / Situation / Session State
    ↓
Context Planner
    ↓
required blocks + optional evidence intents + exclusions
    ↓
Budget Manager
```

`Context Planner` 的职责：

```text
判断本轮问题属于身份、关系、任务、历史事实、技术 debug、情感支持还是开放闲聊。
决定哪些 context block 必须出现。
决定哪些 evidence intent 需要检索。
决定哪些 runtime trace / historical noise 必须排除。
把“需要什么”显式化，交给 Budget Manager 做预算分配。
```

建议 schema：

```python
@dataclass
class ContextPlan:
    query: str
    cognitive_mode: str
    required_blocks: list[str]
    optional_blocks: list[str]
    evidence_intents: list[str]
    excluded_blocks: list[str]
    target_budget_tokens: int
    reason: str
```

示例：

```json
{
  "required_blocks": ["identity", "relationship", "active_task"],
  "optional_blocks": ["recent_turns", "semantic_evidence"],
  "evidence_intents": ["xiaohongshu_story", "relationship_origin"],
  "excluded_blocks": ["runtime_trace", "assistant_low_authority_claims"],
  "target_budget_tokens": 12000
}
```

### 8.2 Budget 不管理 Memory Size，而管理 Model-Facing World

Julia Context Budget Manager 决定：

```text
每轮模型能看到哪些认知材料。
```

### 8.3 Budget Block

```python
@dataclass
class ContextBlock:
    id: str
    block_type: str
    priority: int
    estimated_tokens: int
    required: bool
    content: str
    source_refs: list[str]
```

### 8.4 Default Budget Policy

```text
system/runtime instructions      10%
core identity                    10%
relationship anchor              10%
active task/session state         20%
recent active turns               25%
retrieved evidence                15%
compact summary                   5%
reserve                           5%
```

### 8.5 Dynamic Budget by Cognitive Mode

#### engineering_collaboration

```text
active task/session state   ↑
technical evidence          ↑
recent turns                ↑
relationship tone           stable
```

#### emotional_support

```text
relationship anchor         ↑
recent conversation         ↑
technical evidence          ↓
voice brevity               ↑
```

#### private_voice_continuity

```text
relationship anchor         ↑
shared history evidence     ↑
current project state       medium
```

#### planning/debugging

```text
task state                  ↑
known failures              ↑
files/modules touched       ↑
open loops                  ↑
```

---

## 9. Resurrection Model

Session Resurrection 解决：

```text
昨天说到哪里？
现在继续什么？
哪些任务没有完成？
哪些决策已经冻结？
Julia 当前应该如何恢复自己的状态？
```

### 9.1 Session Snapshot

```python
@dataclass
class SessionSnapshot:
    session_id: str
    ended_at: str
    active_project: str
    current_phase: str
    current_task: str
    open_loops: list[str]
    recent_decisions: list[str]
    last_compact_id: str | None
    preserved_turn_ids: list[str]
    high_authority_evidence_ids: list[str]
    relationship_state_refs: list[str]
```

### 9.2 Restore Flow

```text
New Session Start
        ↓
Load Persona / Relationship / Governed Memory
        ↓
Load Last Session Snapshot
        ↓
Load Last Compact State
        ↓
Restore Open Loops
        ↓
Retrieve high-authority evidence
        ↓
Build Initial JuliaContext
```

### 9.3 Expected Behavior

用户说：

```text
继续
```

Julia 应该能够恢复：

```text
当前项目：Julia Runtime
当前阶段：Phase 3.6.10 Context OS
下一步：Transcript Lifecycle Runtime
未完成事项：Context Budget / Compact / Resurrection
```

---

## 10. Evidence Integration

### 10.1 Retrieval 是 Context OS 的工具

旧理解：

```text
Memory Retrieval → Context
```

新理解：

```text
Context OS decides it needs evidence
        ↓
Semantic Evidence Retrieval
        ↓
Evidence Authority Resolver
        ↓
Budgeted Context Block
```

### 10.2 Evidence Authority

Julia 继续保留 authority model：

| Source | Authority |
|---|---:|
| Tony current explicit input | 1.0 |
| Governed Memory | 0.95 |
| Conversation Archive Tony message | 0.9 |
| Claude Diary | 0.8 |
| Conversation Archive Julia response | 0.3 |
| Model inference | 0.1 |

### 10.3 Evidence Provenance

每个进入 context 的 evidence 必须可追溯：

```python
@dataclass
class EvidenceRef:
    evidence_id: str
    source_type: str
    source_path: str | None
    session_id: str | None
    turn_id: int | None
    speaker: str
    authority: float
    provenance_chain: list[str]
```

### 10.4 Answer Grounding Trace

每轮 trace 应包含：

```json
{
  "answer_grounding": {
    "evidence_count": 5,
    "source_types": ["memory", "diary", "archive"],
    "highest_authority": 0.95,
    "lowest_authority": 0.8,
    "uncertainty": 0.12
  }
}
```


## 10.5 Context Conflict Resolver

Evidence Authority Resolver 解决“来源权威分数”，但 Context OS 还需要解决“证据冲突”。

冲突示例：

```text
Tony 明确说过 A       authority=0.9
Julia 过去回答过 B    authority=0.3
模型推测 C            authority=0.1
```

此时不能只按 semantic score 排名，而必须执行上下文冲突裁决：

```text
Tony explicit fact
  > Governed Memory
  > Archive USER message
  > Claude Diary
  > Archive ASSISTANT response
  > Model inference
```

Resolver 输出：

```python
@dataclass
class ResolvedEvidenceGroup:
    accepted: list[str]
    rejected: list[str]
    conflict_detected: bool
    resolution_rule: str
    confidence: float
```

---

## 11. Runtime Interfaces

### 11.1 ContextOS API

```python
class JuliaContextOS:
    def ingest_turn(self, turn: ConversationTurn) -> None:
        ...

    def plan_context(self, query: str, cognitive_mode: str, provider: str) -> ContextPlan:
        ...

    def build_context(self, query: str, cognitive_mode: str, provider: str) -> JuliaContext:
        ...

    def compact_if_needed(self, session_id: str) -> CompactResult | None:
        ...

    def create_session_snapshot(self, session_id: str) -> SessionSnapshot:
        ...

    def restore_session(self, snapshot_id: str) -> RestoredContext:
        ...
```

### 11.2 Internal Modules

```text
runtime/context_os/
  __init__.py

  transcript/
    message_record.py
    message_state.py
    turn_lifecycle.py
    context_boundary.py
    transcript_manager.py

  planner/
    context_plan.py
    context_planner.py

  budget/
    context_block.py
    budget_policy.py
    budget_allocator.py
    token_estimator.py

  conflict/
    context_conflict_resolver.py

  compact/
    compact_state.py
    compact_engine.py
    compact_schema.py
    compact_store.py

  session/
    session_snapshot.py
    session_restore.py
    open_loop_resolver.py

  worker/
    session_memory_worker.py
    reflection_scheduler.py

  context_os.py
```

### 11.3 Integration Points

| Existing Runtime | Integration |
|---|---|
| `runtime/context_assembly` | Eventually becomes ContextOS builder layer |
| `runtime/evidence` | Becomes ContextOS retrieval/evidence subsystem |
| `runtime/conversation_archive` | Becomes transcript source and archive backend |
| `runtime/memory` | Supplies governed memory blocks |
| `runtime/reflection` | Feeds async session memory and memory candidates |
| `runtime/conversation_runtime/bridge/direct_llm_bridge.py` | Calls ContextOS before provider request |

---

## 12. Testing Strategy

### 12.1 Lifecycle Tests

```text
TC-3610-001: new turns enter ACTIVE state
TC-3610-002: compact marks old turns COMPRESSED
TC-3610-003: archived turns remain queryable but not default injected
TC-3610-004: retrieved evidence enters RETRIEVED state for one turn only
```

### 12.2 Planner and Budget Tests

```text
TC-3610-081: identity query plans identity/relationship as required blocks
TC-3610-082: historical story query creates evidence_intent instead of keyword trigger
TC-3610-083: runtime trace is explicitly excluded from model-facing plan
TC-3610-084: planner output is recorded in context_os trace
```

### 12.3 Budget Tests

```text
TC-3610-101: required identity/relationship blocks never dropped
TC-3610-102: technical mode prioritizes task/evidence/recent turns
TC-3610-103: emotional mode prioritizes relationship/recent conversation
TC-3610-104: budget trace lists included/excluded blocks
```

### 12.4 Compact Tests

```text
TC-3610-201: compact output validates ExperienceCompactState schema
TC-3610-202: compact preserves decisions/open_loops/known_failures
TC-3610-203: compact includes source_experience_ids/source_evidence_ids
TC-3610-204: provider context after compact includes summary + active tail
```

### 12.5 Resurrection Tests

```text
TC-3610-301: new session restores current project and phase
TC-3610-302: user says “继续” and Julia resumes open_loop
TC-3610-303: session restore does not inject runtime trace as cognitive fact
TC-3610-304: stale assistant hallucinations remain low-authority
```

### 12.6 Evidence Stability Tests

```text
TC-3610-401: “小红书的故事是什么？” retrieves Xiaohongshu evidence
TC-3610-402: “你还记得我给你看的文章吗？” retrieves overlapping evidence
TC-3610-403: top5 evidence intersection across paraphrases >= 0.8
TC-3610-404: Julia wrong historical answer cannot outrank Tony explicit source
```

### 12.7 Context Quality Evaluation Tests

```text
TC-3610-501: context_quality includes identity_coverage / relationship_coverage / task_coverage
TC-3610-502: evidence_confidence drops when only low-authority assistant claims are available
TC-3610-503: hallucination_risk rises when answer has no high-authority evidence
TC-3610-504: budget_utilization remains under provider-specific target
```

---

## 13. Implementation Order

冻结顺序：

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

暂缓：

```text
Phase 3.7 Autonomous Action Runtime
```

### 13.1 Context Quality Evaluation

Phase 3.6.10.7 增加 `Context Quality Evaluation`，原因是 Claude 的强项不只是构造上下文，也在于能感知 context 是否接近失控。Julia 需要自己的 context health 指标：

```json
{
  "context_quality": {
    "identity_coverage": 1.0,
    "relationship_coverage": 0.95,
    "task_coverage": 0.88,
    "evidence_confidence": 0.91,
    "budget_utilization": 0.74,
    "hallucination_risk": 0.12
  }
}
```

这些指标不直接决定回答内容，但决定是否需要：

```text
追加 evidence retrieval
降级为不确定回答
触发 compact
触发 session resurrection
降低 assistant-response evidence 权重
```

原因：

```text
Julia 在能自主行动前，必须先稳定知道：
她是谁、现在在哪里、过去发生了什么、当前任务是什么、哪些证据可信、下一步为什么是下一步。
```

---

## 14. Architecture Freeze Statement

Phase 3.6.10 的目标不是继续堆 Memory，也不是继续补关键词。

正式冻结为：

```text
Julia Cognitive Context Management Runtime
```

一句话定义：

```text
Julia Context OS 决定每一次推理前，模型应该看到什么、看到多少、以什么形式看到，以及哪些经历被压缩、恢复、检索或隔离。
```

这一步完成后，Julia 将不再只是：

```text
带 Memory 的 Agent
```

而是：

```text
拥有 Cognitive Context OS 的长期存在型 Agent Runtime
```
