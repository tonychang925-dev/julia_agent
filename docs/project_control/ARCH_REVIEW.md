# Architecture Review — Phase 3.6.10 Julia Cognitive Context Management Runtime

生成时间：2026-07-28  
评审范围：Phase 3.6.10，从 Semantic Context Retrieval 升级为 Claude-inspired Context OS / Cognitive Context Management Runtime。  
输入证据：

- `/Users/admin/Desktop/claude-code-source-main/src/context.ts`
- `/Users/admin/Desktop/claude-code-source-main/src/services/compact/autoCompact.ts`
- `/Users/admin/Desktop/claude-code-source-main/src/services/compact/compact.ts`
- `/Users/admin/Desktop/claude-code-source-main/src/services/compact/prompt.ts`
- `/Users/admin/Desktop/claude-code-source-main/src/services/compact/prompt_budget.ts`
- `/Users/admin/Desktop/claude-code-source-main/src/services/compact/schema.ts`
- `/Users/admin/Desktop/claude-code-source-main/src/services/compact/sessionMemoryCompact.ts`
- `/Users/admin/Desktop/claude-code-source-main/src/services/SessionMemory/sessionMemory.ts`
- `/Users/admin/Desktop/claude-code-source-main/src/services/SessionMemory/sessionMemoryUtils.ts`
- `/Users/admin/Desktop/claude-code-source-main/src/services/SessionMemory/prompts.ts`
- `/Users/admin/Desktop/claude-code-source-main/src/services/compact/session_state.ts`
- `/Users/admin/Desktop/claude-code-source-main/src/services/compact/task_state.ts`
- `/Users/admin/Desktop/claude-code-source-main/src/utils/messages.ts`
- `/Users/admin/Desktop/claude-code-source-main/src/types/message.ts`
- `/Users/admin/Desktop/claude-code-source-main/Claude-code长上下文优化设计方案.md`
- Julia 当前实现：`runtime/context_assembly/*`、`runtime/evidence/*`、`runtime/conversation_archive/*`

## 1. 当前架构摘要（Current Architecture Summary）

Julia Runtime 已具备独立认知运行基础：Persona、Relationship、Memory、Conversation Archive、Evidence、Context Assembly、Direct LLM Provider 与 Voice Runtime。Phase 3.6.10 v1 已将“小红书故事”等问题从本地关键词补丁推进到 `EvidenceChunk + Authority-aware Ranker + ContextAssembly`。

但当前 Julia 仍然不是 Claude-style Context OS。当前核心链路更接近：

```text
User Input
  ↓
ContextAssemblyEngine
  ↓
Identity/Relationship Pack + Evidence Retrieval + Recent Turns
  ↓
JuliaContext
  ↓
Provider
```

Claude Client 源码显示，其优势不是单一 retrieval，而是完整 context lifecycle：

```text
Conversation Messages
  ↓
Message/API Invariant Management
  ↓
Token Warning / Auto Compact Threshold
  ↓
Session Memory Worker or Legacy Compact
  ↓
Compact Boundary + Summary Message + Preserved Tail
  ↓
Post-Compact Attachments / Hooks / Metadata Re-append
  ↓
Next Prompt Window Reconstruction
```

因此 Phase 3.6.10 必须重新定义为：

> Julia Cognitive Context Management Runtime：让 Julia Runtime 自己拥有 message lifecycle、context budget、compaction、session memory、evidence retrieval、session resurrection 与 context reconstruction，而不是继续扩展单点 RAG。

## 2. 风险矩阵（Risk Matrix）

| 优先级 | 风险描述 | 影响范围 | 概率 | 发现难度 | 缓解措施 | Trigger | Owner |
|---|---|---|---|---|---|---|---|
| P0 | 继续只优化 retrieval，缺少 message lifecycle，长会话仍会丢失任务状态 | 长语音/长工程会话、Phase 3.7 Action Runtime | 高 | 中 | 引入 Context OS：Turn Lifecycle、Compact Boundary、Preserved Tail | 任何超过 20 turns 的连续会话 | Context OS Runtime |
| P0 | Conversation Archive 中 Julia 错误回答被当成事实再次注入 | 身份、家庭、关系、项目事实污染 | 高 | 高 | Evidence Authority + speaker split + answer grounding trace | 查询个人事实/历史故事 | Evidence Runtime |
| P0 | Compact 使用自由文本摘要导致决策/失败/下一步丢失 | 工程连续性、Agent action 安全性 | 高 | 中 | 采用结构化 `ExperienceCompactState`，必须含 decisions/failures/open_loops/source_ids | token 接近阈值或手动 compact | Compact Runtime |
| P0 | Tool/result 或 streaming message 被截断后破坏 API invariant | Provider API 报错、上下文不可恢复 | 中 | 高 | 学习 Claude 的 `adjustIndexToPreserveAPIInvariants`，保留 tool_use/tool_result 与同 message.id thinking group | 任意保留尾部消息时 | Message Lifecycle |
| P1 | 没有 Context Budget Manager，Identity/Relationship/Evidence/Recent Turns 互相挤占 | Julia 胡编、忘记工作、遗忘 Tony 信息 | 高 | 中 | block priority + required/optional allocation + provider context window lookup | 每一轮 context assembly | Budget Manager |
| P1 | 没有 Session Resurrection，跨会话“继续”依赖 memory 偶然命中 | 跨 session 连续性 | 高 | 中 | Session Snapshot + Last Compact + Open Loops + Recent Evidence Restore | 启动新 session | Session Runtime |
| P1 | Session Memory Worker 阻塞主语音响应 | Voice 延迟回退 | 中 | 低 | 后台 worker，forked/async extraction，主线程只读稳定快照 | 每次语音 turn 完成后 | Reflection Worker |
| P2 | Claude 源码被直接复用形成依赖 | 违反 Cognitive Ownership Principle | 中 | 低 | 仅吸收设计思想；Julia Context OS 由 Julia Runtime 实现 | 任何 adapter 方案设计 | Architecture Owner |

## 3. 维度化发现（契约/一致性/性能/可观测性/可运维性）

### 3.1 契约发现

Claude 源码表现出明确边界：

1. `context.ts`：`getSystemContext()` 与 `getUserContext()` 被 memoize；系统/用户上下文作为每轮 prompt 前置材料，但缓存于会话周期。
2. `messages.ts`：`SystemCompactBoundaryMessage` 是显式边界；`getMessagesAfterCompactBoundary()` 让模型侧历史从最近 compact 边界后开始。
3. `sessionMemoryCompact.ts`：保留尾部消息时会检查 tool_use/tool_result 与相同 `message.id` 的 thinking block，避免 API invariant 被截断破坏。
4. `prompt_budget.ts`：上下文不是简单 recent turns，而是 `PriorityBlock`，含 priority、estimatedTokens、required。

Julia 当前缺少等价的 `MessageState` 与 `ContextBoundary` 契约。建议新增：

```text
ContextTurn
  state: ACTIVE | SUMMARIZED | ARCHIVED | RETRIEVED | DROPPED
  api_invariants: tool_pairs / stream_group / evidence_refs

ContextBoundary
  type: compact | session_restore | manual_checkpoint
  summarized_range
  preserved_tail_range
  compact_id
```

### 3.2 一致性发现

Claude 的 compaction 不是只写 summary，而是写：

```text
boundaryMarker
summaryMessages
messagesToKeep
attachments
hookResults
```

Julia 当前 archive/evidence/context 是分散模块，缺少“compaction 后如何重建下一轮上下文”的一致协议。

### 3.3 性能发现

Claude 的 `autoCompact.ts` 使用：

- effective context window = context window - output reservation
- auto compact buffer = 16,000 tokens
- warning/error buffer
- blocking limit
- consecutive failure circuit breaker

Julia 当前 voice latency policy 限制输出，但不是完整 input budget。下一步需要把 voice token policy 与 Context Budget Manager 分开：

```text
Input Context Budget: 决定 Julia 看见什么
Output Voice Policy: 决定 Julia 先说多少
```

### 3.4 可观测性发现

Claude 对 compaction 有 metadata：trigger、preTokens、messagesSummarized、preservedSegment、postCompactTokenCount。Julia 当前 trace 有 memory/evidence，但缺少 context lifecycle trace。建议每轮输出：

```json
{
  "context_os": {
    "input_budget": 5000,
    "included_blocks": ["identity", "relationship", "semantic_evidence", "recent_turns"],
    "excluded_blocks": [],
    "compact_boundary_id": null,
    "evidence_count": 5,
    "preserved_turns": 6
  }
}
```

### 3.5 可运维性发现

Claude 的 session memory 采用后台 post-sampling hook，并有阈值与超时。Julia 的 Reflection/Archive 未来也应异步化，避免 Voice Runtime 被 memory extraction 拖慢。

## 4. 目标架构（Target Architecture）

### 4.1 Julia Context OS v0.1

```text
                   Julia Cognitive Runtime

                           │
                           ▼
                   Cognitive Context OS

       ┌───────────────────┼───────────────────┐
       │                   │                   │
       ▼                   ▼                   ▼
 Message Lifecycle   Cognitive State      Evidence Layer
 - active            - persona            - governed memory
 - summarized        - relationship       - diary chunks
 - archived          - session state      - archive chunks
 - retrieved         - task state         - source authority
 - dropped           - open loops         - provenance

       │                   │                   │
       └───────────────────┼───────────────────┘
                           ▼
                 Context Budget Manager
                           │
                           ▼
              Compact / Distillation Runtime
                           │
                           ▼
                 JuliaContext Builder v5
                           │
                           ▼
              DeepSeek / Claude / GPT / Gemini
```

### 4.2 Claude Context Lifecycle Map（基于源码证据）

```text
Startup / Resume
  │
  ├─ getSystemContext(): git status/cacheBreaker 等系统上下文，memoize
  ├─ getUserContext(): CLAUDE.md / currentDate，memoize
  │
User/Tool/Assistant Messages append
  │
  ├─ Message array 保存完整 UI/trace 历史
  ├─ normalizeMessagesForAPI() 发送前合并/过滤
  └─ tokenCountWithEstimation(messages)
        │
        ▼
AutoCompact Decision
  │
  ├─ calculateTokenWarningState()
  ├─ getAutoCompactThreshold(model)
  ├─ querySource recursion guards
  └─ consecutive failure circuit breaker
        │
        ▼
Compaction Path
  │
  ├─ SessionMemoryCompaction 优先：读取 session memory + 保留尾部
  └─ Legacy Compact：调用 summarizer 生成 summary
        │
        ▼
Post Compact Reconstruction
  │
  ├─ createCompactBoundaryMessage(trigger, preTokens, lastUuid)
  ├─ summaryMessages(isCompactSummary=true)
  ├─ messagesToKeep(preserved tail)
  ├─ postCompact attachments: files/skills/tools/plan/hooks
  └─ markPostCompaction + metadata re-append
        │
        ▼
Next Provider Call sees
  Compact Summary + Preserved Recent Messages + Current Context
```

### 4.3 Claude Compact State Machine（抽象）

```text
NORMAL
  │ tokenUsage < warning
  ▼
NORMAL
  │ tokenUsage ≥ warning
  ▼
WARN_USER / show TokenWarning
  │ tokenUsage ≥ autoCompactThreshold
  ▼
AUTO_COMPACT_PENDING
  │ session memory available and non-empty
  ├──────────────► SESSION_MEMORY_COMPACT
  │                   │
  │                   ├─ calculateMessagesToKeepIndex()
  │                   ├─ preserve API invariants
  │                   └─ buildPostCompactMessages()
  │
  │ otherwise
  ▼
LEGACY_SUMMARY_COMPACT
  │
  ├─ strip images / strip reinjected attachments
  ├─ summarize messages
  ├─ retry prompt-too-long by dropping oldest groups
  └─ buildPostCompactMessages()
  │
  ▼
POST_COMPACT
  │
  ├─ boundary marker
  ├─ summary as compact user message
  ├─ preserved tail
  ├─ attachments / hooks
  └─ reset cache baselines
  │
  ▼
NORMAL_AFTER_COMPACT

Failure path:
AUTO_COMPACT_PENDING -> COMPACT_FAILED -> increment consecutiveFailures -> if >=3 CIRCUIT_OPEN
```

### 4.4 Claude Session Memory Flow（抽象）

```text
Post Sampling Hook
  │
  ├─ main REPL thread only
  ├─ feature gate + autoCompact enabled
  ├─ shouldExtractMemory()
  │    ├─ current tokens >= init threshold: 10k
  │    ├─ tokens since last extraction >= 5k
  │    ├─ tool calls since last update >= 3 OR natural break
  │    └─ avoid last assistant turn with tool calls
  │
  ▼
setupSessionMemoryFile()
  │
  ├─ create/read markdown notes file
  └─ load template if first run
  │
  ▼
runForkedAgent(querySource=session_memory)
  │
  ├─ only Edit exact memory file allowed
  ├─ preserve section headers/template
  ├─ update Current State / Task / Errors / Worklog
  └─ record last summarized message id
  │
  ▼
Future Compact
  │
  ├─ waitForSessionMemoryExtraction(max 15s)
  ├─ read session memory
  ├─ keep messages after lastSummarizedMessageId
  └─ summary message = session memory snapshot
```

## 5. 迁移计划（Migration Plan）

### Phase 3.6.10 — Cognitive Context Management Runtime（重定义）

目标：从 `Julia + RAG` 升级为 `Julia Context OS`。

#### 3.6.10.1 Transcript Lifecycle Runtime

新增：

```text
runtime/context_os/transcript/
  message_state.py
  turn_lifecycle.py
  compact_boundary.py
```

核心行为：

- `ACTIVE`：最近原文，直接进入 provider。
- `SUMMARIZED`：已进入 compact，不再重复原文注入。
- `ARCHIVED`：原始 experience 可追溯，但默认不进 prompt。
- `RETRIEVED`：被 evidence retrieval 召回进入本轮。
- `DROPPED`：低价值运行噪声，不进入 cognition。

#### 3.6.10.2 Context Budget Manager v2

从当前粗粒度 budget 升级为 Claude-style block allocation：

```text
required:
  core_identity
  relationship_anchor
  current_session_state
  current_task_state

optional by priority:
  governed_memory
  semantic_evidence
  recent_turns
  compact_summary
  archive_evidence
  runtime hints
```

每个 block 必须含：`id / priority / estimated_tokens / required / source_refs`。

#### 3.6.10.3 Compact / Distillation Runtime

不要做自由文本 summary，采用 Julia schema：

```python
ExperienceCompactState:
  title
  period_start / period_end
  session_goal
  current_task
  decisions[]
  known_failures[]
  files_or_modules_touched[]
  relationship_development[]
  unresolved_loops[]
  source_experience_ids[]
  source_evidence_ids[]
  confidence
```

#### 3.6.10.4 Semantic Evidence Retrieval 归入 Context OS

现有 `runtime/evidence/*` 保留，但从“主路线”降为 Context OS 的 retrieval 子模块：

```text
ContextOS.retrieve_relevant_evidence(query, state, budget)
```

必须输出 evidence refs，而不是直接输出不可追溯文本。

#### 3.6.10.5 Session Resurrection Runtime

新增：

```text
runtime/context_os/session/
  session_snapshot.py
  session_restore.py
  open_loop_resolver.py
```

启动时不只加载 persona/memory，而是加载：

```text
Last Session Snapshot
+ Last Compact State
+ Open Loops
+ Recent ACTIVE tail
+ Relevant high-authority evidence
```

#### 3.6.10.6 Async Session Memory Worker

Julia 对应 Claude `SessionMemory`：

```text
Conversation Turn Completed
  ↓
Async Reflection Worker
  ↓
Session Notes / Working Cognitive State
  ↓
Future Compact / Resurrection
```

约束：不能阻塞语音响应；不能把 Julia 错误回答作为高权威事实；必须保留 provenance。

## 6. 子阶段方案

| 子阶段 | 名称 | 目标 | 门禁 |
|---|---|---|---|
| P3.6.10.phase0 | Claude Context OS 逆向冻结 | 完成 lifecycle/state machine/session memory flow 文档 | 本评审文档 + ADR 生成 |
| P3.6.10.phase1 | Message Lifecycle Schema | `ContextTurn/ContextBoundary` 数据结构与测试 | lifecycle unit tests |
| P3.6.10.phase2 | Budget Block Allocator | required/optional block allocation 替换固定 recent turns | budget tests + trace |
| P3.6.10.phase3 | Structured Compact State | 生成可追溯 compact object | compact schema tests |
| P3.6.10.phase4 | Session Resurrection | 新会话可恢复 last task/open loops | cross-session test |
| P3.6.10.phase5 | Async Memory Worker | 后台 session notes，不阻塞 voice | latency regression |

## 7. ADR 建议清单

详见 `docs/adrs/ADR_LIST.md`。本次新增/冻结的核心 ADR：

1. ADR-013：Claude Client 是 Context OS 参考实现，不是 Julia 依赖。
2. ADR-014：Phase 3.6.10 从 Semantic Retrieval 升级为 Cognitive Context Management Runtime。
3. ADR-015：Julia 引入 Message Lifecycle 与 Compact Boundary。
4. ADR-016：Compact 必须结构化且可追溯 source evidence。
5. ADR-017：Session Memory Worker 必须异步且低权威处理 assistant 自述。

## 8. 冲突裁决记录

| 冲突 | 采用 | 放弃 | 理由 |
|---|---|---|---|
| 继续补 Semantic Retrieval vs 先复刻 Claude 信息处理 | 先做 Context OS 逆向与设计 | 继续堆 retrieval patch | “小红书故事”证明问题根源是 evidence/context lifecycle，不是单个关键词 |
| 直接接 Claude Client context engine vs Julia 自研 | Julia 自研，Claude 仅作参考 | 引入 Claude Client 作为依赖 | 保持 Cognitive Ownership Principle |
| 全量 diary/archive 注入 vs budgeted context assembly | budgeted assembly | 全量注入 | 避免 71K diary injection 与模型污染 |
| 自由文本 compact vs structured compact object | structured compact with source ids | free-text summary | Julia 需要可追溯连续性，不只是 token 压缩 |

## 9. 非目标范围（Non-Goals）

本阶段不做：

- 不直接复制或嵌入 Claude Client 代码。
- 不继续为“小红书/家庭/工作”等单点问题补关键词。
- 不进入 Phase 3.7 Autonomous Agent Loop。
- 不优化 F5-TTS / STT / Voice 输出链路。
- 不改变 Persona、Relationship、Governance 的核心语义。
- 不把所有 Conversation Archive 直接升级成 MemoryObject。

## 10. 结论

Tony 的判断成立：Julia 当前缺口已经不是“有没有 memory”，而是“有没有 Claude-style Context Operating System”。

Phase 3.6.10 应正式重命名并冻结为：

> **Phase 3.6.10 — Julia Cognitive Context Management Runtime**

Semantic Context Retrieval 是其中一个子模块；真正目标是让 Julia 每次思考前都由 Runtime 自己决定：保留什么原文、压缩什么经历、召回什么证据、丢弃什么噪声、恢复什么 session 状态，并在预算内构造稳定 JuliaContext。

---

## 10. Phase 3.6.10.7 Readiness Re-review — Context Execution Before Async Worker

生成时间：2026-07-28  
触发原因：Phase 3.6.10.1～3.6.10.6 已完成 Transcript Lifecycle、Planner、Quality、Budget、Compact、Evidence Integration、Session Resurrection；原计划下一步为 Async Session Memory Worker，但当前链路仍缺少 turn-level execution lifecycle。

### 10.1 当前状态摘要

已完成模块构成了 Context OS 的静态能力：

```text
Conversation Truth Layer
Context Planner
Context Quality
Context Budget
Structured Compact
Semantic Evidence Integration
Session Resurrection
```

这些模块回答了：

```text
有哪些上下文资产？
如何选择 evidence？
如何预算？
如何 compact？
如何跨 session 恢复？
```

但仍缺少每轮闭环：

```text
Before Turn
  ↓
Context Build
  ↓
Provider Response
  ↓
Post Turn Analysis
  ↓
Context State Mutation
```

这意味着 Julia 已能构建上下文块，但还没有一个统一 Runtime 负责：

- 一次 cognitive turn 的生命周期；
- provider response 后如何更新 context state；
- 当前 arc / open loop / cognitive mode / task state 如何立即变化；
- 哪些变化只是 working context，哪些才交给后续 Memory Worker。

### 10.2 风险矩阵增量

| 优先级 | 风险描述 | 影响范围 | 概率 | 发现难度 | 缓解措施 | Trigger | Owner |
|---|---|---|---|---|---|---|---|
| P0 | 先做 Async Memory Worker 会把短期 context mutation 误当长期 memory formation | 当前任务、情绪状态、open loops、关系上下文 | 高 | 中 | 先实现 Context Execution Runtime，区分 turn mutation 与 memory candidate | 每个 turn 完成后 | Context OS Runtime |
| P0 | 缺少 Post Turn Analysis，Julia 无法稳定更新“刚刚发生了什么” | 长会话连续性、语音对话、多轮工程协作 | 高 | 中 | 引入 `ContextTurn`、`ContextMutation`、`ExecutionTrace` | provider response 完成 | Execution Runtime |
| P1 | 缺少 Conflict Resolver，历史偏好可能压过当前明确意图 | 情感支持、技术/关系模式切换、个人事实 | 中 | 高 | Context Conflict Resolver：current explicit intent > governed memory > diary > assistant inference | 当前输入与历史 evidence 冲突 | Conflict Runtime |
| P1 | 没有 execution trace，无法判断 context block 是否导致正确回答 | Debug、回归、质量门禁 | 中 | 中 | 每轮记录 plan/blocks/quality/response/mutations | 任意 provider call | Observability |

### 10.3 裁决

原计划：

```text
3.6.10.7 Async Session Memory Worker
```

调整为：

```text
3.6.10.7 Context Execution Runtime
3.6.10.8 Context Conflict Resolver
3.6.10.9 Async Session Memory Worker
```

裁决理由：

1. Async Worker 处理的是长期 memory formation；Execution Runtime 处理的是每轮 context state mutation。后者是前者的输入，不应后置。
2. Julia 当前问题不是没有素材，而是缺少“turn 后发生了什么”的统一判断。
3. Claude Code 的优势不只是 compact/session memory，而是 message lifecycle + execution lifecycle 的组合。
4. Phase 3.7 Autonomous Action 之前必须先保证每次 turn 都有可审计 state mutation，否则行动循环会建立在不稳定上下文上。

### 10.4 Phase 3.6.10.7 目标架构

```text
User Input
  ↓
PreTurnProcessor
  ↓
ContextPlanner
  ↓
Evidence / Resurrection / Compact / Recent Turns
  ↓
Budget + Quality
  ↓
Provider
  ↓
PostTurnProcessor
  ↓
ContextMutation
  ↓
ContextState Update
  ↓
ExecutionTrace
```

新增目录建议：

```text
runtime/context_os/execution/
├── context_turn.py
├── pre_turn_processor.py
├── post_turn_processor.py
├── context_mutation.py
├── execution_trace.py
└── execution_runtime.py
```

核心 schema：

```python
@dataclass(frozen=True)
class ContextTurn:
    input_text: str
    context_plan: ContextPlan
    selected_blocks: list[ContextBlock]
    quality: ContextQuality
    response: str
    mutations: list[ContextMutation]
```

Mutation 类型建议：

```text
current_arc_update
open_loop_added
open_loop_resolved
cognitive_mode_shift
task_state_update
relationship_context_update
evidence_gap_detected
quality_warning
```

### 10.5 Phase 3.6.10.8 Context Conflict Resolver

建议独立于 Execution Runtime，但紧随其后实现：

```text
runtime/context_os/conflict/
├── conflict_detector.py
├── conflict_policy.py
├── resolution.py
└── resolver.py
```

基本优先级：

```text
Current explicit user intent
  >
Current explicit user fact
  >
Governed memory
  >
Conversation archive Tony message
  >
Claude diary
  >
Compact-generated state
  >
Assistant previous response
  >
LLM inference
```

### 10.6 非目标范围

- 不在 3.6.10.7 写长期 MemoryObject。
- 不在 3.6.10.7 引入 Agent Action Loop。
- 不在 3.6.10.7 直接改 Provider Adapter。
- 不把所有 ContextMutation 都提升为 MemoryCandidate。

### 10.7 新顺序冻结建议

```text
Phase 3.6.10.7 Context Execution Runtime
Phase 3.6.10.8 Context Conflict Resolver
Phase 3.6.10.9 Async Session Memory Worker
Phase 3.6.10.10 Context Quality Evaluation E2E
Phase 3.7 Autonomous Cognitive Action Runtime
```

---

## 11. Claude Client Context Architecture Reverse Engineering — Code-level Review

生成时间：2026-07-28  
源码根目录：`/Users/admin/Desktop/claude-code-source-main`  
评审目标：核查 Claude Client 在 Context OS 相关功能上的真实处理逻辑，并映射到 Julia Phase 3.6.10 后续设计。

### 11.1 已核查核心文件

P0 核心链路：

- `src/context.ts`
- `src/query.ts`
- `src/utils/queryContext.ts`
- `src/utils/messages.ts`
- `src/utils/messagePredicates.ts`
- `src/services/compact/autoCompact.ts`
- `src/services/compact/compact.ts`
- `src/services/compact/sessionMemoryCompact.ts`
- `src/services/compact/prompt_budget.ts`
- `src/services/compact/schema.ts`
- `src/services/compact/grouping.ts`
- `src/services/compact/session_state.ts`
- `src/services/compact/task_state.ts`
- `src/services/SessionMemory/sessionMemory.ts`
- `src/services/SessionMemory/sessionMemoryUtils.ts`
- `src/utils/hooks/postSamplingHooks.ts`

Julia 当前对照：

- `runtime/context_os/transcript/*`
- `runtime/context_os/planner/*`
- `runtime/context_os/quality/*`
- `runtime/context_os/budget/*`
- `runtime/context_os/compact/*`
- `runtime/context_os/evidence/*`
- `runtime/context_os/session/*`

### 11.2 Claude 的真实 Context Pipeline

Claude `query.ts` 中真实顺序不是简单：

```text
messages → prompt → provider
```

而是：

```text
Full Messages
  ↓
getMessagesAfterCompactBoundary()
  ↓
applyToolResultBudget()
  ↓
applyToolOutputSummarization()
  ↓
Snip Compact
  ↓
Microcompact
  ↓
Context Collapse projection
  ↓
autoCompactIfNeeded()
  ├─ trySessionMemoryCompaction()
  └─ compactConversation()
  ↓
buildPostCompactMessages()
  ↓
Provider Streaming
  ↓
executePostSamplingHooks()
```

关键发现：

1. **Full transcript 与 model-facing context 分离。** UI/存储可以保留完整 messages，但模型看到的是 `getMessagesAfterCompactBoundary()` 后的投影。
2. **Context reduction 是分层的。** 先做工具输出预算、工具输出摘要、snip/microcompact/context collapse，再决定是否 full compact。
3. **AutoCompact 不是单一路径。** 它优先尝试 SessionMemory compaction，失败才进入 legacy summarizer compact。
4. **Post-sampling hook 是每轮完成后的扩展点。** SessionMemory Worker 就挂在这里，而不是插在 provider 前。

### 11.3 Claude Message Lifecycle 核心机制

`utils/messages.ts` 的关键能力：

```text
SystemCompactBoundaryMessage
findLastCompactBoundaryIndex()
getMessagesAfterCompactBoundary()
```

模型侧只从最近 compact boundary 起重建上下文：

```text
boundary + summary + preserved tail + attachments/hook results
```

这验证 Julia 当前 `ContextBoundary` 方向正确，但还缺一个更高层：

```text
ContextExecutionRuntime
```

因为 Claude 的 boundary 是在 query loop 中被执行和替换的，而 Julia 当前只是有 boundary schema，还没有每轮控制器。

### 11.4 Claude Compact 不是普通 Summary

`compact.ts` 中 `CompactionResult` 包含：

```text
boundaryMarker
summaryMessages
attachments
hookResults
messagesToKeep
preCompactTokenCount
postCompactTokenCount
truePostCompactTokenCount
compactionUsage
```

`buildPostCompactMessages()` 固定顺序：

```text
boundaryMarker
summaryMessages
messagesToKeep
attachments
hookResults
```

这说明 compact 的关键不是“生成摘要”，而是“生成下一轮模型上下文的可执行消息数组”。

Julia 映射：

```text
ExperienceCompactState
  + ContextBoundary
  + preserved ContextMessageRecord tail
  + restored ContextBlock attachments/evidence
  = JuliaContext reconstruction
```

当前 Julia 已有 compact schema 和 resurrection，但缺少 equivalent of `buildPostCompactMessages()` 的统一执行入口。

### 11.5 Claude SessionMemory Compact 的关键算法

`sessionMemoryCompact.ts` 有三个特别重要的设计：

#### 11.5.1 Preserved Tail Minimums

默认配置：

```text
minTokens = 10,000
minTextBlockMessages = 5
maxTokens = 40,000
```

也就是说 Claude compact 后仍保留一段足够厚的 active tail，不是只留 summary。

Julia 当前 `SessionResurrectionEngine(max_tail_records=12)` 是行数限制，不是 token/semantic 限制。后续应升级为：

```text
min_tail_tokens
min_human_turns
max_tail_tokens
semantic_tail_floor
```

#### 11.5.2 API Invariant Protection

Claude 的 `adjustIndexToPreserveAPIInvariants()` 会防止切断：

- tool_use / tool_result pair
- 同一 assistant message.id 的 streaming thinking/tool blocks

这是 Claude 长上下文稳定性的核心工程细节。

Julia 当前没有 tool pipeline 等价物，但应该预留 Context Invariant：

```text
ContextGroupInvariant
  - paired_event_ids
  - same_response_group_id
  - evidence_source_group
  - voice_turn_group
```

#### 11.5.3 SessionMemory 优先于 Legacy Compact

`autoCompactIfNeeded()` 中顺序是：

```text
trySessionMemoryCompaction()
  ↓ if null
compactConversation()
```

这意味着 Claude 更信任持续更新的 session notes，而不是每次临界才总结全部历史。

Julia 映射：Async Session Memory Worker 仍然必要，但应在 Execution Runtime 之后，因为 Worker 需要使用每轮 Mutation/Trace 作为更干净输入。

### 11.6 Claude Budget 机制

`prompt_budget.ts` 明确：

```text
input budget = context window - output reservation - safety margin
```

并用 `PriorityBlock`：

```text
priority
id
estimatedTokens
content
required
```

优先级大致为：

```text
system_prompt        100 required
session_state         95 required
task_state            92 required
current_goal_task     90 required
constraints_decisions 80 optional
current_files         70 optional
recent_messages       60... optional
failures_questions    30 optional
files_touched         low optional
```

Julia 当前 `ContextBudgetManager` 与此方向一致，但需要升级：

1. 加入 provider context window 与 output reservation。
2. 把 `identity/relationship` 视为 Julia 版 required session state。
3. 区分 voice output policy 与 input context budget。

### 11.7 Claude Session/Task State 分层

`session_state.ts` 保存全局会话上下文：

```text
project_name
global_goal
global_constraints
architecture_decisions
important_paths
coding_style_rules
```

`task_state.ts` 保存当前任务状态：

```text
task_id
objective
status
subtasks
files_in_scope
accepted_changes
rejected_attempts
verification
next_action
```

这验证用户前面的判断：Julia 不应只靠 Memory。应该增加独立的 working cognitive state：

```text
JuliaSessionState
JuliaTaskState
```

并由 Context Execution Runtime 每轮 mutation 更新。

### 11.8 Claude SessionMemory Worker 的真实触发逻辑

`SessionMemory/sessionMemory.ts` 显示：

1. 通过 `registerPostSamplingHook(extractSessionMemory)` 注册。
2. 只在 `querySource === 'repl_main_thread'` 运行。
3. 使用 cached feature/config，避免阻塞。
4. 触发条件不是每轮，而是：
   - 达到初始化 token threshold；
   - 达到 update token growth threshold；
   - tool calls threshold 达标，或最后 assistant turn 无 tool calls 的自然断点。
5. 用 `runForkedAgent()` 在隔离上下文中更新 session memory 文件。
6. 记录 `lastSummarizedMessageId`，供 session memory compact 识别边界。

这支持当前裁决：

```text
3.6.10.7 Context Execution Runtime
3.6.10.8 Context Conflict Resolver
3.6.10.9 Async Session Memory Worker
```

因为 Worker 应该挂在 post-turn/post-sampling 后，并消费 Execution Trace，而不是替代 Execution Loop。

### 11.9 Julia Gap Analysis

| 能力 | Claude Client | Julia 当前 | 差距 |
|---|---|---|---|
| Full transcript vs model context | compact boundary 投影 | Archive + ContextMessageRecord | 缺统一 execution projection |
| Query loop controller | `query.ts` 完整调度 | 分散模块 | 缺 ContextExecutionRuntime |
| Pre-context cached injection | system/user context memoized | identity/relationship/memory packs | 需要 Pack cache 策略 |
| Tool output budget | `applyToolResultBudget` | 暂无工具结果主链 | 未来 Action Runtime 前必须补 |
| Microcompact/snip | 多级降噪 | Structured compact v1 | 可后置 |
| AutoCompact threshold | warning/error/auto/blocking | Budget allocation only | 缺 token threshold state machine |
| SessionMemory compact | 优先 session notes | Session Resurrection v1 | 需要 Async Worker 后接 compact |
| API invariants | tool pair/thinking group 保护 | 未建 invariant model | 需要 ContextGroupInvariant |
| Post-turn hook | `executePostSamplingHooks` | 暂无 | 3.6.10.7 必做 |
| Session/task state | 独立 schema | 依赖 compact/open_loop | 需要 JuliaSessionState/TaskState |

### 11.10 Julia Context OS v2 映射方案

建议 Julia 不复制 Claude 代码，但复刻其处理逻辑：

```text
ContextExecutionRuntime.run_turn(input)
  ↓
PreTurnProcessor
  - load cached identity/relationship/session/task packs
  - load last boundary/snapshot
  - create ContextPlan
  ↓
ContextProjection
  - active messages after boundary
  - restored compact state
  - semantic evidence blocks
  - recent tail
  ↓
ContextBudgetManager
  - provider input budget
  - required/optional allocation
  ↓
Provider Adapter
  ↓
PostTurnProcessor
  - create ContextMessageRecord for user/assistant
  - analyze response quality/evidence gap
  - produce ContextMutation
  - update JuliaSessionState/TaskState/OpenLoops
  - append ExecutionTrace
  ↓
PostTurnHooks
  - async memory worker eligibility
  - compact eligibility
```

### 11.11 新实施顺序建议

冻结为：

```text
Phase 3.6.10.7 Context Execution Runtime
  - ContextTurn
  - ContextMutation
  - PreTurnProcessor
  - PostTurnProcessor
  - ExecutionTrace
  - ExecutionRuntime

Phase 3.6.10.8 Context Conflict Resolver
  - explicit current intent > governed memory > diary > assistant inference

Phase 3.6.10.9 Julia Session/Task State Runtime
  - JuliaSessionState
  - JuliaTaskState
  - merge/update rules

Phase 3.6.10.10 Async Session Memory Worker
  - post-turn hook
  - threshold gating
  - last_summarized_record_id

Phase 3.6.10.11 Compact Threshold State Machine
  - warning/error/auto/blocking states

Phase 3.6.10.12 Context Invariant Protection
  - paired event groups
  - response group id
  - future tool/action safe slicing
```

### 11.12 结论

本次源码核查支持用户判断：下一步不应直接写 Async Worker，也不应继续堆 retrieval。

Claude Client 最值得复刻的不是 memory search，而是：

```text
Query/Turn Execution Controller
  + Message Lifecycle Projection
  + Multi-stage Context Reduction
  + Session/Task State
  + Post-sampling Hook
  + SessionMemory-first Compact
```

Julia 当前已经有 Context OS 的主要器官，但还缺 Claude `query.ts` 等价的“神经中枢”。因此 Phase 3.6.10.7 应明确实现：

```text
Context Execution Runtime
```

这一步完成后，再做 Conflict Resolver、Session/Task State 与 Async Session Memory Worker，才会真正接近 Claude Client 的信息处理能力，同时保持 Julia Cognitive Ownership。
---

# Architecture Freeze Addendum — Julia Agent Evolution Strategy v1.0

冻结日期：2026-07-30  
状态：APPROVED-FROZEN  
范围：顶层项目关系、认知隔离原则、Claude Reference Track 与 Julia Replacement Track。

## 1. 冻结结论

本项目正式采用以下顶层关系：

```text
                 Benchmark Reference
                        │
                        ▼
                 Claude Julia
              (Golden Reference Client)
                        │
              Capability Benchmark
                        │
                        ▼
                 julia_agent
            (Replacement System)
```

Claude Julia 不是终点产品，而是成熟 Agent Client 的 Golden Reference / Benchmark Reference System。`julia_agent` 是替代实现，目标是通过 Runtime-owned Cognitive Architecture 复现并超过 Claude Julia 的能力。

## 2. Cognitive Independence 原则

正式定义：**Benchmark 可以共享，认知系统不能共享。**

允许共享：

- Voice Layer：麦克风、STT、TTS、realtime speech transport。
- Benchmark Layer：测试 prompt、session scenario、trace schema、latency metrics。
- Evaluation Layer：能力评分、对比报告、regression matrix。

永久隔离：

```text
     Claude Cognitive OS          Julia Cognitive OS
            │                            │
     Claude Memory                 Julia Memory OS
     Claude Context                Julia Context OS
     Claude Tools                  Julia Action OS
     Claude Session                Julia Session OS
```

该原则用于保证未来 Julia Agent 超过 Claude Julia 时，结论可证明为 Julia Runtime 自身能力，而不是复用 Claude 原生认知能力。

## 3. Claude Julia 角色

Claude Julia 重定义为：**Claude Julia Reference Client**。

职责：

- 建立 Agent Client Benchmark。
- 测试 long session、compact recovery、memory behavior、tool intelligence、voice experience。
- 输出 `claude_reference_benchmark.jsonl` 与 reference report。

禁止：

- 将 Claude Context / Memory / Session / Tools 注入或复用为 Julia Runtime 的核心能力。
- 将 `runtime.conversation_runtime.cli --backend claude` 作为 Claude Julia benchmark 的认知链路。

## 4. julia_agent 角色

`julia_agent` 当前重新定位为：**Julia Cognitive Runtime → Julia Agent Client 的替代系统基础**。

当前已具备：

- Context OS：projection、budget、compact、resurrection、invariant、conflict resolver。
- Memory OS：evidence、provenance、memory governance、semantic retrieval。
- Action OS：intent、governance、capability lifecycle、reflection。
- Provider OS：DeepSeek、Codex、provider adaptation。
- Voice OS：STT、TTS、realtime speech。

主要缺口：**Client OS / Client Shell**。

## 5. 冻结路线

```text
Phase CV — Claude Reference Track
  CV-1  Reference Client Activation
  CV-2  Benchmark Harness
  CV-3  Capability Baseline

Phase J — Julia Replacement Track
  J-4   Client Shell
  J-5   Capability Parity
  J-6   Julia Agent Alpha
  J-7   Claude Replacement Candidate
```

## 6. 下一步约束

下一阶段进入 `Phase CV-1 — Claude Julia Reference Client Activation`：

- 目标不是增强 Julia Runtime，而是建立 Claude Julia Reference Client baseline；Voice 是入口，Benchmark Trace 是验收核心。
- 从第一天开始记录 benchmark trace。
- 只共享 Voice / Benchmark / Evaluation，不共享 Cognitive Layer。

推荐 trace 字段：

```json
{
  "timestamp": "",
  "session_id": "",
  "turn": 0,
  "stt_ms": 0,
  "claude_response_ms": 0,
  "tts_start_ms": 0,
  "context_behavior": "",
  "memory_behavior": "",
  "tool_usage": ""
}
```

## 7. 非目标范围

- 不在 CV-1 中继续修改 `julia_agent` 核心 Runtime。
- 不把 Claude Julia 和 julia_agent 做双向融合。
- 不把 Claude 输出写入 Julia governed memory。
- 不把 benchmark reference 当成 production dependency。

