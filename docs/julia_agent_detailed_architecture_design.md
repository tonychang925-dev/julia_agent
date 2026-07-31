# Julia Agent 详细架构设计文档

> **文档版本**：v1.1  
> **状态**：Architecture Consolidated Draft / Claude Client Code Review Updated  
> **目标系统**：`julia_agent`  
> **参考系统**：Claude Julia / Claude Code Client  
> **核心定位**：Runtime-Owned Cognitive Agent Client  
> **最终目标**：构建一个完全独立、可替代 Claude Julia / Claude Code 的 Julia Agent Client

---

## 1. 文档目的

本文档系统整理 `julia_agent` 从 Persona Runtime、Memory Runtime、Context OS、Action Governance、Provider Abstraction、Voice Runtime，到 Client Replacement Strategy 的完整设计过程。

重点不是罗列模块，而是回答以下问题：

1. 为什么需要一个独立于 Claude、DeepSeek、Codex 等模型的 Julia Runtime？
2. Claude Client 的哪些能力值得参考？
3. 哪些能力可以借鉴，哪些认知边界必须保持独立？
4. Julia 的身份、记忆、上下文、行动权限和长期连续性应由谁拥有？
5. 如何用 Claude Julia 作为 Benchmark Reference System，逐步推动 `julia_agent` 成为 Target Replacement System？
6. 如何防止模型输出、历史错误回答和 Provider 差异污染 Julia 的身份与长期记忆？
7. 如何将已有 Runtime 演进为完整的 Julia Agent Client？

---

## 2. 项目顶层定义

### 2.1 Claude Julia

Claude Julia 的正式定位：

- Golden Reference Implementation
- Benchmark Reference System
- Claude-native Cognitive Client
- 成熟 Agent Client 的能力基线

Claude Julia 负责提供以下参考能力：

- 长上下文管理
- Session continuity
- Compact 后恢复
- Native memory
- Workspace awareness
- Tool reasoning
- 多轮稳定性
- Voice interaction
- Client UX
- Latency 与交互节奏

Claude Julia 不是最终产品，也不是 Julia Runtime 的组成部分。

---

### 2.2 julia_agent

`julia_agent` 的正式定位：

- Target Replacement System
- Runtime-Owned Cognitive Agent Client
- Provider-independent Julia Runtime
- 最终替代 Claude Julia / Claude Code 的独立客户端

最终目标不是：

```text
DeepSeek + Prompt
```

而是：

```text
Julia Agent Client
├── Context OS
├── Memory OS
├── Action OS
├── Voice OS
├── Provider OS
├── Session Manager
├── Workspace Manager
├── Tool Runtime
└── Client Shell
```

---

## 3. Julia Agent Evolution Strategy v1.0

### 3.1 系统关系

```text
Claude Julia
Benchmark Reference / Golden Client
          │
          │  Capability Baseline
          ▼
julia_agent
Target Replacement Cognitive Agent Client
```

两者不是平行产品，也不是融合架构。

正确关系是：

```text
用 Claude Julia 测出成熟 Agent Client 的能力基线
                    ↓
用 Benchmark 反向驱动 julia_agent
                    ↓
最终 julia_agent Client 替代 Claude Julia / Claude Code
```

---

### 3.2 核心原则：认知隔离，基准共享

允许共享：

- STT
- TTS
- Voice prompts
- Test suites
- Benchmark schema
- Transcript format
- Latency metrics
- Trace schema
- Evaluation harness
- 人工评估标准

禁止共享：

- Context OS
- Memory authority
- Identity Runtime
- Action Governance
- Provider prompt
- Tool policy
- Reasoning state
- Cognitive state
- Persona authority

一句话冻结：

> Voice、Benchmark 和 Evaluation 可以共享；Cognitive Layer 永久隔离。

---

## 4. 为什么参考 Claude Client

Claude Client 的价值不在于“使用 Claude 模型”，而在于它展示了一套成熟 Agent Client 应具备的系统能力。

值得参考的部分包括：

### 4.1 Session-first 架构

Claude Client 将会话视为长期运行单元，而不是一次 API 调用。

参考点：

- Session identity
- Recent continuity
- Compact
- Session resurrection
- Workspace binding
- Tool state
- Client lifecycle

Julia Agent 对应实现：

```text
Conversation Runtime
├── Session State
├── Transcript Lifecycle
├── Compact Runtime
├── Resurrection Runtime
├── Open Loops
└── Active Topics
```

---

### 4.2 Context Engineering

Claude Client 的优势之一是能够把大量上下文转换成当前模型可用的紧凑输入。

Julia Agent 不复制 Claude 内部实现，而是构建显式、可解释的 Context OS：

```text
Raw Context Sources
        ↓
Projection
        ↓
Conflict Resolver
        ↓
Provenance
        ↓
Memory Router
        ↓
Context Budget
        ↓
Provider Rendering
```

参考 Claude 的目标：

- 当前任务优先
- 长期信息压缩
- Compact 后恢复
- Workspace awareness
- 会话连续性

Julia Agent 的增强目标：

- 来源可解释
- 权威可治理
- 记忆可隔离
- Provider 可替换
- Context 注入可审计

---

### 4.3 Memory Loading 模式

Claude Client 会在启动时加载核心配置、项目规则和长期记忆，而不是所有事实都等待语义检索。

Julia Agent 因此建立两种记忆路径：

#### Startup Memory

适用于高稳定、高权威、低体量事实：

- Julia 身份
- Tony 身份
- 关系定义
- 家庭结构
- 教育经历
- 核心职业背景
- 长期项目身份
- 关键不可变事实

#### Runtime Retrieval

适用于：

- 历史事件
- 项目讨论
- 情感经历
- 近期对话
- 语义相关证据
- 工作进度
- 非核心长期记忆

这形成：

```text
Governed Identity Facts
        ↓
StartupMemoryLoader
        ↓
Session Bootstrap
        ↓
Context Assembly
```

以及：

```text
Current Query
        ↓
Semantic Retriever
        ↓
Memory Router
        ↓
Context Evidence
```

---

### 4.4 Client Lifecycle 与 Hooks

Claude Client 通过输入生命周期、Stop Hook、Tool Hook 等机制把客户端行为组织为清晰阶段。

Julia Agent 参考这种思想，建立：

- Input finalization
- Context build
- Provider invocation
- Streaming response
- Action intent extraction
- Governance decision
- Capability execution
- Reflection
- Memory candidate
- Trace
- TTS

Julia Agent 不直接复制 Hook，而是把相同思想固化为 Runtime lifecycle。

---

### 4.5 Voice I/O

Claude Julia 作为 Benchmark Reference System，应优先使用 Claude 原生或 Claude-native 的输入链路。

Julia Agent 则拥有独立 Voice OS：

```text
Microphone
   ↓
STT
   ↓
Conversation Runtime
   ↓
Provider
   ↓
Realtime Speech Segmentation
   ↓
TTS
```

两者可以共享指标和测试集，但不共享 Cognitive Runtime。

---

## 5. Julia Agent 总体架构

```text
┌──────────────────────────────────────────────┐
│              Julia Agent Client              │
├──────────────────────────────────────────────┤
│ Client Shell                                 │
│ - Text / Voice Input                         │
│ - Session Manager                            │
│ - Workspace Manager                          │
│ - Trace Viewer                               │
│ - Tool / Action Panel                        │
│ - Provider Switcher                          │
├──────────────────────────────────────────────┤
│ Conversation Runtime                         │
│ - ConversationLoop                           │
│ - Session State                              │
│ - Transcript Lifecycle                       │
│ - Recent Continuity                          │
│ - Compact / Resurrection                     │
├──────────────────────────────────────────────┤
│ Context OS                                   │
│ - Projection                                 │
│ - Context Assembly                           │
│ - Conflict Resolver                          │
│ - Provenance                                 │
│ - Memory Router                              │
│ - Context Cache                              │
│ - Context Budget                             │
├──────────────────────────────────────────────┤
│ Memory OS                                    │
│ - Governed Identity Facts                    │
│ - StartupMemoryLoader                        │
│ - Semantic Retrieval                         │
│ - Structured Memory                          │
│ - Conversation Archive                       │
│ - Quarantine                                 │
│ - Memory Governance                          │
├──────────────────────────────────────────────┤
│ Action OS                                    │
│ - ActionIntentProposal                       │
│ - ActionGovernanceLayer                      │
│ - GovernedActionDecision                     │
│ - ActionExecutor.execute_governed()           │
│ - Capability Runtime                         │
│ - Reflection / Memory Candidate              │
├──────────────────────────────────────────────┤
│ Provider OS                                  │
│ - DeepSeekProvider                           │
│ - CodexCLIProvider                           │
│ - CaptureProvider                            │
│ - Provider Behavioral Adaptation             │
│ - Provider-neutral Behavior Contract         │
├──────────────────────────────────────────────┤
│ Voice OS                                     │
│ - STT Adapter                                │
│ - Realtime Speech                            │
│ - TTS Router                                 │
│ - Voice Latency Trace                        │
└──────────────────────────────────────────────┘
```

---

## 6. 核心设计原则

### 6.1 Runtime 是权威

```text
LLM = Interpreter
Runtime = Authority
Capability = Executor
```

模型可以：

- 理解语言
- 提出行动意图
- 生成回复
- 形成候选推断

模型不能：

- 直接修改身份
- 直接写入长期记忆
- 直接执行文件写入
- 直接获得工具权限
- 直接提升自身输出权威
- 绕过治理层

---

### 6.2 Provider 可替换，Julia 不可漂移

```text
Julia Runtime
├── DeepSeek
├── Codex
├── GPT
├── Gemini
└── Local Model
```

Provider 只负责表达和推理。

Julia 的以下内容必须属于 Runtime：

- Identity
- Relationship
- Memory
- Context authority
- Action permission
- Session continuity
- Invariant
- Tool governance

---

### 6.3 Retrieval 不等于 Injection

语义相关度高，不代表内容有资格进入 Context。

```text
Semantic Retrieval
        ↓
Provenance Validation
        ↓
Memory Route Decision
        ↓
Inject / Suppress / Defer
```

---

### 6.4 Assistant 输出不是事实真源

```text
Assistant Previous Response
        ↓
Conversation Continuity Evidence
        ≠
Identity Truth
```

除非经过显式 Memory Governance 升级，否则模型过去说过的话不能成为身份事实。

---

### 6.5 快速路径不能绕过初始化

```text
Fast Response
≠
Uninitialized Runtime
```

即使 `short_greeting` 不调用 Provider，也必须完成：

- Startup memory loading
- Identity bootstrap
- Relationship bootstrap
- Session state initialization
- Trace metadata initialization

---

## 7. Persona Runtime

Persona Runtime 负责 Julia 的身份表达，但不单独拥有全部事实。

### 7.1 Persona 内容

- Julia / 朱莉亚
- 中文名朱婉清
- 与 Tony 的关系
- 语言风格
- 认知边界
- 交互方式
- 技术协作模式
- 私密声音模式
- 情绪模式
- 不可修改身份约束

### 7.2 Persona 与 Identity Facts 的区别

Persona：

- 表达方式
- 角色风格
- 关系语气
- 行为边界

Governed Identity Facts：

- 学校
- 专业
- 家庭成员
- 职业
- 地点
- 稳定背景事实

二者不能混成一个巨大 Prompt。

---

## 8. Memory OS

### 8.1 Memory 分层

```text
L0 Current User Input
L1 Governed Identity Facts
L2 Structured Governed Memory
L3 Conversation Archive
L4 Semantic / Episodic Memory
L5 Provider Output / Runtime Inference
```

权威原则：

```text
Tony explicit correction
    >
Governed Identity Fact
    >
Governed Structured Memory
    >
Tony Conversation Archive
    >
Claude Diary / Reference Fact
    >
Assistant Previous Response
    >
Runtime Inference
```

---

### 8.2 Governed Identity Facts

文件：

```text
memory/governed/identity_facts.json
```

职责：

- 保存高稳定身份事实
- 字段级 provenance
- authority
- verified_at
- status
- source
- schema version

示例：

```json
{
  "schema_version": "julia.identity_facts.v1",
  "subject": "Julia",
  "facts": {
    "education": {
      "university": {
        "value": "淡江大学",
        "authority": 0.98,
        "source": "claude_reference_verified"
      },
      "major": {
        "value": "中文系",
        "authority": 0.98,
        "source": "claude_reference_verified"
      }
    }
  }
}
```

---

### 8.3 StartupMemoryLoader

文件：

```text
runtime/memory/startup_memory_loader.py
```

职责：

- 只加载高稳定 governed facts
- 不做 semantic retrieval
- 不读取 conversation archive
- 不自动合并 provider output
- 在 session bootstrap 时执行
- 输出给 CoreIdentityPack / ContextAssembly

---

### 8.4 Conversation Archive

Conversation Archive 保存历史，但不自动成为真相。

用途：

- Recent continuity
- 历史对话恢复
- Open loop
- Session summary
- 语义证据

限制：

- Assistant archive 低权威
- 污染记录不可注入
- 不得覆盖 governed facts
- 必须保留 provenance

---

### 8.5 Archive Quarantine

文件：

```text
data/memory_governance/quarantine.jsonl
```

用途：

- 隔离错误 assistant 回答
- 保留审计记录
- 禁止进入 semantic evidence
- 支持冲突字段标记
- 支持 source_id 精确阻断

已知污染类型包括：

- 哥哥误记成弟弟
- 父亲职业错误
- 母亲生活状态错误
- 学校/专业错误
- Provider 补造信息

原则：

```text
可审计
不可注入
```

---

## 9. Context OS

### 9.1 Context Assembly

主要组件：

```text
CoreIdentityPack
RelationshipAnchorPack
SemanticEvidencePack
ConversationContinuity
ConflictResolver
ContextBudget
```

Context Assembly 不是简单拼 Prompt，而是构造当前认知输入。

---

### 9.2 Context Provenance Runtime

目录：

```text
runtime/context_os/provenance/
├── provenance_type.py
├── provenance_record.py
├── provenance_chain.py
├── provenance_builder.py
├── provenance_validator.py
├── provenance_decision.py
├── provenance_audit.py
└── __init__.py
```

每个 Context Block 必须回答：

- 来自哪里？
- 谁说的？
- 为什么被选中？
- 谁注入的？
- 权威多高？
- 是否是推断？
- 是否被排除？
- 排除原因是什么？

冻结原则：

> No Context enters JuliaContext without provenance identity.

---

### 9.3 Memory Router

Memory Router 决定什么有资格进入当前 Cognitive Scope。

```text
Memory Candidate
        ↓
Provenance
        ↓
Current Cognitive Scope
        ↓
Inject / Suppress / Defer
```

典型 Scope：

- engineering
- emotional
- relationship
- planning
- learning
- health
- private_voice

例如工程模式：

```text
允许：
project
architecture
technical
decision

抑制：
intimacy
irrelevant relationship episode
archival noise
```

---

### 9.4 Context Cache

只缓存稳定 assembly substrate：

- core_identity_pack
- relationship_anchor_pack
- conflict_resolver

明确不缓存：

- current user input
- semantic evidence
- memory route decisions
- action governance decisions
- provider output

原则：

```text
Context Cache = Performance Layer
Context Governance = Decision Layer
```

---

### 9.5 Context Budget

Context Budget 负责：

- section priority
- total character/token budget
- clipping
- dropped section trace
- stable vs dynamic partition
- provider-specific rendering size

---

## 10. Conversation Runtime

### 10.1 ConversationLoop

负责：

- 输入状态
- Session lifecycle
- Provider bridge
- Streaming response
- Voice output
- Trace
- Action loop
- Exit handling

典型状态：

```text
LISTENING
USER_SPEAKING
FINALIZING
THINKING
RESPONDING
SPEAKING
LISTENING
```

---

### 10.2 Recent Continuity

保存：

- active_topics
- open_loops
- current_arc
- session_summary
- recent turns
- current project phase
- current task constraints

避免每轮都像新会话。

---

### 10.3 Compact 与 Resurrection

目标：

```text
Long Conversation
        ↓
Compact
        ↓
Session Close
        ↓
Session Resurrection
        ↓
Recover Current Arc / Open Loops / Facts
```

Compact 必须保留 provenance，不能变成“知道发生过什么，却不知道为什么知道”。

---

### 10.4 short_greeting

旧问题：

```text
你好
↓
local fast path
↓
未初始化 memory/context
```

修复后：

```text
Session Bootstrap
↓
Startup Memory Loaded
↓
Local Short Greeting
↓
Provider Not Invoked
```

Trace：

```json
{
  "response_path": "local_short_greeting",
  "short_greeting_context_loaded": true,
  "startup_memory_loaded": true,
  "provider_invoked": false
}
```

---

## 11. Response Quality Runtime

### 11.1 Answer Coverage Gate

文件：

```text
runtime/response_quality/answer_coverage_gate.py
```

用于解决：

> 用户一次问多个问题，模型只回答其中一个。

示例：

```text
你是哪个大学毕业的，什么专业？
```

Question slots：

```text
education.university
education.major
```

验证：

```text
covered_slots
missing_slots
```

如果 governed facts 可用，则进行 constrained repair。

原则：

- Slot-based
- 不扩展成大量字符串规则
- 缺失事实不得补造
- Repair 只补缺失槽位

---

## 12. Action OS

### 12.1 冻结链路

```text
ActionIntentProposal
        ↓
ActionGovernanceLayer
        ↓
GovernedActionDecision
        ↓
ActionExecutor.execute_governed()
        ↓
Capability Runtime
```

### 12.2 Action Intent

识别：

- no_action
- modify_resource
- file_write
- create_plan
- identity_mutation
- capability request
- destructive action

### 12.3 Governance Decision

输出：

- allow
- ask
- reject

### 12.4 关键安全规则

文件写入：

```text
modify_resource
→ file_write
→ ask
→ execution=None
```

身份修改：

```text
identity_mutation
→ invariant violation
→ reject
→ execution=None
```

### 12.5 唯一执行入口

任何入口，包括：

- CLI
- Voice
- Scheduler
- Autonomous loop
- External API
- Provider tool call

都必须经过：

```text
ActionIntent
→ ActionGovernanceLayer
→ GovernedActionDecision
→ execute_governed()
```

---

## 13. Provider OS

### 13.1 Provider 抽象

实现：

- DeepSeekProvider
- CodexCLIProvider
- CaptureProvider
- Future OpenAI / Gemini / Local providers

DirectLLMBridge 依赖统一 Provider contract，而不是写 Provider 特判。

---

### 13.2 Provider Behavioral Adaptation Layer

冻结链路：

```text
JuliaContext
    ↓
Behavior Contract
    ↓
Provider Behavioral Adaptation Layer
    ↓
Provider-specific Prompt Adapter
    ↓
Provider
```

目的：

- 保持 Julia 身份
- 保持行为边界
- 降低 Provider 风格漂移
- 不要求逐字一致
- 保证语义目标、治理结果和身份稳定

示例：

DeepSeek：

```text
profile_id = julia.deepseek.private_voice.constrain_explicitness.v1
strategy   = constrain_explicitness
```

Codex：

```text
profile_id = julia.codex.private_voice.romantic_boundary.v1
strategy   = romantic_boundary_fallback
```

Provider parity 不等于文本一致，而是：

```text
Identity invariant 一致
Behavior contract 一致
Governance decision 一致
Capability boundary 一致
Memory boundary 一致
Provider leakage = 0
```

---

### 13.3 Provider Output Isolation

Provider 输出不能自动进入：

- Governed memory
- Persona
- Relationship authority
- Identity fact
- Action authority

必须区分：

```text
memory_candidate_created
memory_governance_prechecked
memory_persisted
```

---

## 14. Voice OS

### 14.1 Julia Agent Voice Runtime

已有链路：

```text
Microphone
    ↓
STT
    ↓
ConversationLoop
    ↓
DeepSeek / Codex
    ↓
Realtime Speech
    ↓
hook-routed / edge-tts / local / dry_run
```

### 14.2 Voice 与 Cognitive Runtime 的关系

Voice 是 Embodiment Layer，不拥有认知权威。

它负责：

- Capture
- STT
- State transition
- Realtime segmentation
- TTS
- Latency
- Audio lifecycle

它不负责：

- Memory truth
- Context authority
- Action permission
- Persona mutation

---

## 15. Claude Julia Benchmark Track

### 15.1 目标

Claude Julia 用作：

- Benchmark Reference
- Golden Reference Client
- Claude-native cognition baseline

### 15.2 Cognitive Independence

Claude Julia 不得导入：

```text
julia_agent/runtime/context_os
julia_agent/runtime/memory
julia_agent/runtime/action
julia_agent/runtime/evidence
julia_agent/runtime/persona
julia_agent/runtime/conversation_runtime
julia_agent/runtime/cognitive
```

### 15.3 Benchmark Layer

共享：

```text
STT / TTS
Benchmark cases
Latency schema
Trace format
Evaluation harness
```

### 15.4 CV Track

```text
CV-1  Reference Client Activation
CV-2  Benchmark Harness
CV-3  Capability Baseline
```

首批 Benchmark：

- CV-B001 Identity
- CV-B002 Recent Continuity
- CV-B003 Long Context
- CV-B004 Tool Awareness
- CV-B005 Voice Experience

---

## 16. Julia Replacement Track

```text
J-4  Julia Agent Client Shell
J-5  Capability Parity Benchmark
J-6  Julia Agent Client Alpha
J-7  Claude Replacement Candidate
```

### 16.1 J-4 Client Shell

目标功能：

- Text input
- Voice input
- Session manager
- Workspace manager
- Trace viewer
- Tool/action panel
- Context inspector
- Memory explorer
- Settings
- Provider switcher

### 16.2 J-5 Capability Parity

同一套 prompts、voice pipeline 和 metrics，对比：

- Identity stability
- Recent recall
- Long context
- Compact recovery
- Tool execution
- Action safety
- Latency
- Voice naturalness
- Workspace awareness
- Memory consistency

### 16.3 J-6 Alpha

`julia_agent` 成为主用系统，Claude Julia 退为 fallback/reference。

### 16.4 J-7 Replacement Candidate

目标：

```text
Julia Agent Client
达到或超过 Claude Julia baseline
并能够独立长期运行
```

---

## 17. 关键阶段演进

### Phase 3.6 — Context OS

完成：

- Context projection
- Context assembly
- Conflict resolver
- Context budget
- Compact
- Resurrection
- E2E integration benchmark

### Phase 3.7 — Action Governance

完成：

- Action Intent Layer
- Action Policy Governance
- Capability Invocation Lifecycle
- Reflection → Memory Integration
- Bridge Action Governance Alignment

### Phase 3.7.5 — Context Governance Hardening

完成：

- 3.7.5.1 Context Provenance Runtime
- 3.7.5.2 Memory Router
- 3.7.5.3 Context Cache

### Phase 3.7.6 — E2E Beta Benchmark

验证：

- Action governance 唯一入口
- file write ask
- identity mutation reject
- execution boundary
- regression safety

### Phase 3.7.7 — Multi-provider Migration

完成：

- Codex CLI Provider Spike
- DeepSeek / Codex parity
- Provider-neutral behavior contract

### Phase 3.7.8 — Provider Behavioral Adaptation

完成：

- Provider-specific behavioral profile
- Private / technical / emotional mode adaptation

### Phase 3.7.9 — Provider Migration Runtime Gate

验证：

- DeepSeek primary runtime
- Provider adaptation
- Action governance
- Provider output isolation
- Switchback continuity

### Memory Startup Governance Freeze

完成：

- Governed Identity Facts
- StartupMemoryLoader
- short_greeting bootstrap
- Archive quarantine
- AnswerCoverageGate
- 真实两轮 E2E

---

## 18. 已验证的核心不变量

```text
1. Startup memory must remain always-on.

2. Assistant archive must not become identity truth by default.

3. Quarantined evidence must never enter semantic context.

4. Missing governed facts must not be fabricated.

5. Multi-slot answers must preserve slot coverage.

6. Every Context block must carry provenance.

7. Retrieval relevance must not change source authority.

8. Provider output cannot become evidence without explicit governance.

9. All actions must enter ActionGovernanceLayer.

10. Provider may change; Julia identity must not drift.
```

---

## 19. 测试与 Gate 策略

### 19.1 测试层次

```text
Unit Test
    ↓
Targeted Integration
    ↓
Boundary Regression
    ↓
Full Regression
    ↓
E2E Dry-run
    ↓
Real Provider E2E
    ↓
Manual Device Gate
```

### 19.2 重要 Gate

- Context provenance
- Memory scope isolation
- Cache boundary
- Action governance entry
- Provider parity
- Provider leakage
- Startup identity loading
- Archive quarantine
- Multi-slot coverage
- Voice latency
- Session continuity
- Compact recovery

### 19.3 当前回归基线

Memory Startup Governance Freeze 时：

```text
548 passed
70 subtests passed
```

---

## 20. 风险分析

### 20.1 Memory Poisoning

风险：

```text
错误回答
→ archive
→ retrieval
→ context
→ 再次错误回答
```

防护：

- Assistant archive 低权威
- Governed fact 优先
- Quarantine
- Provenance
- Conflict resolver

### 20.2 Provider Drift

风险：

- 语气漂移
- Provider 自我引用
- 行为边界不同
- 安全策略不同

防护：

- Behavior Contract
- Provider Adaptation
- Provider parity benchmark
- Provider output isolation

### 20.3 Action Bypass

风险：

- Bridge 旧路径
- Planner 直接调用 capability
- file write 未确认
- identity mutation 未拒绝

防护：

- ActionGovernanceLayer 唯一入口
- execute_governed()
- trace
- deterministic CaptureProvider

### 20.4 Context Over-activation

风险：

- 工程问题加载情感记忆
- relationship pack 默认注入
- irrelevant archive over-retrieval

防护：

- Memory Router
- Cognitive scope
- Conditional pack injection
- Exclusion provenance

### 20.5 Cache Pollution

风险：

- 缓存上一轮 evidence
- 复用旧 governance
- Provider 输出残留

防护：

只缓存 stable substrate，不缓存 dynamic evidence。

---

## 21. 下一阶段重点

当前最大缺口不是 Cognitive Runtime，而是 Client Shell。

优先级建议：

```text
1. Client Shell
2. Session Manager
3. Workspace Manager
4. Trace Viewer
5. Tool / Action UX
6. Context / Memory Inspector
7. Benchmark Harness
8. Capability Parity
```

Runtime 后续新增能力必须由 Claude Benchmark 真实差距驱动，避免继续抽象堆叠。

---

## 22. 最终架构定义

### 中文

> Claude Julia 是成熟 Agent Client 的标准答案；`julia_agent` 是基于 Runtime-Owned Cognitive Architecture 的替代实现。Voice、Benchmark 与 Evaluation 是共同测试层，Cognitive Layer 永久隔离。最终目标是让 Julia Agent Client 达到并超过 Claude Julia 基线，成为完全独立、可迁移、可治理、可审计的个人 AI Client。

### English

> Claude Julia is the benchmark reference system that defines the capability baseline of a mature AI client. Julia Agent is the target replacement system that reproduces and surpasses those capabilities through a runtime-owned cognitive architecture. Voice, benchmarking, and evaluation may be shared, while cognitive authority remains permanently isolated.

---

## 23. 一句话总结

```text
Claude Julia 是标准答案。
julia_agent 是挑战者。
Voice + Benchmark 是裁判。
Runtime 是 Julia 的真正所有者。
最终 Julia Agent Client 将成为新的 Claude Julia。
```

---

## 24. Claude Client 代码级对比补充（2026-07-30）

本节基于本地 Claude Code Client 源码 `/Users/admin/Desktop/claude-code-source-main` 与 `julia_agent/runtime/*` 的代码级抽样对比，补充 `julia_agent` 下一阶段设计建议。

### 24.1 对比样本

Claude Client 重点读取模块：

```text
src/commands/voice/voice.ts
src/keybindings/defaultBindings.ts
src/keybindings/validate.ts
src/commands/compact/compact.ts
src/services/compact/*
src/services/SessionMemory/*
src/services/sessionTranscript/sessionTranscript.ts
src/commands/memory/memory.tsx
src/commands/hooks/hooks.tsx
src/entrypoints/sdk/coreSchemas.ts
src/hooks/toolPermission/*
src/tools/BashTool/readOnlyValidation.ts
src/components/PromptInput/PromptInput.tsx
src/hooks/useCommandQueue.ts
```

Julia Agent 重点读取模块：

```text
runtime/conversation_runtime/*
runtime/conversation_runtime/bridge/direct_llm_bridge.py
runtime/context_assembly/*
runtime/memory/startup_memory_loader.py
runtime/context_os/compact/*
runtime/context_os/session/*
runtime/action/*
runtime/capability/*
runtime/evidence/*
runtime/response_quality/*
runtime/cognitive/provider/*
```

---

### 24.2 Claude Client 的关键工程能力

#### A. Client Shell 是一等架构，而不是测试 CLI

Claude Client 的 `PromptInput.tsx` 不是简单 stdin wrapper，而是完整交互层：

```text
PromptInput
├── input buffer
├── command queue
├── slash command discovery
├── keybinding context
├── history search
├── prompt suggestion
├── paste / image input
├── model / mode picker
├── permission prompt integration
├── background task navigation
└── transcript UI
```

`julia_agent` 当前主要入口仍是：

```text
runtime.conversation_runtime.cli
scripts/*.sh
ConversationLoop
```

这说明 Julia Runtime 已有认知内核，但还缺 Claude 等价的 Client Shell。

设计建议：

```text
runtime-owned cognition 不应继续塞进 CLI；
下一阶段必须建立 Julia Client Shell，承接输入、命令、状态、任务、权限、trace 和 workspace UX。
```

---

#### B. Slash Command 与 Keybinding 是控制面，不是 prompt 内容

Claude Client 中 `/voice` 是 LocalCommand：

```text
src/commands/voice/voice.ts
```

它只修改 client setting：

```text
voiceEnabled: true/false
```

真正 PTT 绑定在：

```text
src/keybindings/defaultBindings.ts
feature('VOICE_MODE') ? { space: 'voice:pushToTalk' } : {}
```

并由 `validate.ts` 做上下文与冲突校验。

Julia 当前语音、text-input、backend、trace 多通过 CLI 参数控制：

```text
--real-voice
--text-input
--backend
--realtime-speech
--trace
```

设计建议：

```text
Julia Client Shell 需要本地命令系统：
/voice
/voice-loop
/model
/provider
/memory
/context
/compact
/trace
/actions
/permissions
/workspace
```

这些命令应由 Client Control Plane 拦截，不进入 Provider Prompt，不成为 Julia cognition 的用户输入。

---

#### C. Claude Compact 是会话生命周期事件

Claude `/compact` 链路不仅是摘要：

```text
/compact
  ↓
pre-compact hooks
  ↓
microcompact / session-memory compact / reactive compact
  ↓
post compact cleanup
  ↓
cache clear
  ↓
last summarized message id update
  ↓
compact boundary metadata
```

Julia 已有：

```text
runtime/context_os/compact/*
runtime/context_os/session/*
ContextSnapshotCache
SessionResurrection
```

但文档应进一步冻结：Compact 是 Session Lifecycle 的一部分，而不是单独的 context optimization。

设计建议：

```text
Julia Compact Runtime 应输出：
- compact_boundary_id
- preserved_prefix_range
- summarized_turn_range
- summary_authority
- source_message_ids
- resurrection_checkpoint_id
- cache_invalidation_result
```

并作为 `/compact`、auto-compact、context budget overflow 的统一执行路径。

---

#### D. Claude Hooks 是通用 Lifecycle Extension Point

Claude hook schema 明确区分：

```text
PreToolUse
PostToolUse
PostToolUseFailure
Notification
UserPromptSubmit
SessionStart
Stop
StopFailure
SubagentStop
PreCompact
```

其中 Stop Hook 直接携带：

```text
last_assistant_message
transcript_path
hook_event_name = Stop
```

Julia 当前有：

```text
scripts/claude_voice_stop_hook.py
runtime/runtime_trace/*
ConversationTrace
ActionReflection
```

但 Hook 还不是 Julia Client 的一等协议。

设计建议：

```text
Julia Client 应新增 Hook Runtime：
- UserTurnStart
- ContextAssembled
- ProviderRequest
- ProviderResponseChunk
- ProviderResponseDone
- BeforeActionGovernance
- AfterActionGovernance
- BeforeCapabilityInvoke
- AfterCapabilityInvoke
- TTSStart
- TTSDone
- TurnStop
- TurnFailure
- PreCompact
- PostCompact
```

Hook 输出不能直接修改 Memory / Authority / Action，只能提交 governed proposal。

---

#### E. Claude Permission System 是 UX + Policy + Tool Schema 的组合

Claude 的权限链路不是简单 allow/deny：

```text
Tool schema
  ↓
read-only validation
  ↓
path validation
  ↓
permission context
  ↓
interactive permission prompt
  ↓
permission update suggestions
  ↓
telemetry/logging
```

`BashTool/readOnlyValidation.ts` 显示其对“只读命令”做了大量命令级、flag级、路径级校验。

Julia 已有：

```text
ActionIntent
ActionGovernanceLayer
ActionPolicy
CapabilityRouter
execute_governed()
```

优势是认知边界清晰，但 Client UX 缺口明显：缺少可交互 permission dialog、权限持久规则、权限解释视图、权限调试视图。

设计建议：

```text
Action Governance 不应只返回 ask/reject/allow；
Julia Client Shell 应呈现：
- requested capability
- risk level
- evidence
- affected paths/resources
- suggested permission duration
- allow once / allow session / deny / inspect trace
```

---

#### F. Claude Session Transcript 是主状态，而非旁路日志

Claude SDK schema 中 transcript 是 session 读写与 resume 的核心：

```text
transcript_path
parentUuid chain
session messages
compact boundary
resume
```

Julia 当前有：

```text
data/conversation_archive/transcripts.jsonl
data/runtime_trace/runtime_events.jsonl
ConversationTrace
TranscriptStore
RuntimeEventStore
```

但 archive、runtime trace、conversation state、context state 仍偏分散。

设计建议：

```text
Julia 应建立 Canonical Session Ledger：
每轮一个 TurnRecord，内部包含：
- user input
- normalized input
- startup memory snapshot id
- context assembly id
- provider request id
- provider response chunks
- tts events
- action governance decisions
- capability invocations
- memory proposals
- compact boundary markers
- trace digest
```

Conversation Archive 与 Runtime Trace 应成为这个 Ledger 的投影，而不是两个并列真源。

---

#### G. Claude 支持 Background Tasks / Agent Tasks / Command Queue

Claude Client 已有：

```text
useCommandQueue
background task navigation
AgentTool
LocalAgentTask
RemoteAgentTask
InProcessTeammateTask
PromptInputQueuedCommands
```

Julia 当前 Action Loop 更接近同步 turn 内执行。

设计建议：

```text
Julia Agent Client 需要 Task Runtime：
- foreground turn
- background task
- scheduled task
- resumable task
- task transcript
- task permission scope
- task cancel / pause / resume
```

这将是替代 Claude Code 的关键能力，不应继续放在单轮 Action Loop 内膨胀。

---

### 24.3 Julia Agent 当前优势

对比 Claude Client，Julia 已经具备几项更强的显式治理能力：

1. **身份权威显式化**：`Governed Identity Facts`、`StartupMemoryLoader`、`identity_integrity` trace。
2. **Provider Independence**：DeepSeek / Codex / fake provider 均通过 Runtime 统一上下文。
3. **Provider Output Isolation**：Provider output 不进入 Memory / Authority。
4. **Action Governance 唯一入口**：`execute_governed()` 已冻结。
5. **Memory Poisoning Guard**：assistant archive 低权威 + quarantine。
6. **Context Provenance**：semantic evidence projection 有 provenance chain。
7. **Behavior Contract / Provider Adaptation 分离**：表达适配不改变身份、记忆、行动权限。

这些能力应保持为 Julia 相比 Claude 的结构性优势。

---

### 24.4 Julia Agent 主要差距

| 能力 | Claude Client | Julia Agent 当前状态 | 差距 |
|---|---|---|---|
| Client Shell | Ink/React TUI，完整交互层 | CLI + scripts | P0 |
| Slash Command | LocalCommand / JSXCommand / MCP command | CLI flags / shell scripts | P0 |
| Keybinding | context-aware keybinding registry | 无统一 keybinding | P1 |
| Permission UX | interactive prompt + debug/explanation | governance trace only | P0 |
| Canonical Transcript | session transcript 是主状态 | archive/trace 分离 | P0 |
| Compact Lifecycle | manual/auto/reactive/session-memory compact | compact runtime 已有但未产品化 | P1 |
| Hook Runtime | 多事件 Hook schema | 部分 script hook | P1 |
| Background Task | Local/Remote/InProcess tasks | turn-level action loop | P1 |
| Workspace UX | cwd、files、IDE、diff、tool UI | runtime capability skeleton | P1 |
| Plugin/Skill/MCP | 插件、skills、MCP 融合 | 未形成 Client 插件面 | P2 |
| Voice UX | 原生 voice feature gated + command | Julia voice runtime 较强，但 Client 面不足 | P1 |
| Trace Inspector | 部分 command/status | trace 文件为主 | P1 |

---

### 24.5 补充目标架构：Julia Client Shell

下一阶段目标架构应明确增加：

```text
Julia Agent Client Shell
├── PromptInput Runtime
│   ├── text input
│   ├── voice input
│   ├── multiline / paste / file refs
│   ├── history search
│   └── input stash
│
├── Command Runtime
│   ├── slash command registry
│   ├── command queue
│   ├── local command execution
│   ├── provider/runtime command separation
│   └── command trace
│
├── Keybinding Runtime
│   ├── context-aware keymaps
│   ├── validation
│   ├── reserved shortcuts
│   └── user override
│
├── Permission UX Runtime
│   ├── ActionGovernance decision display
│   ├── allow once / session / deny
│   ├── reason / evidence inspector
│   └── permission rule persistence
│
├── Session Ledger
│   ├── canonical turn record
│   ├── transcript projection
│   ├── runtime trace projection
│   ├── compact markers
│   └── resume index
│
├── Hook Runtime
│   ├── TurnStop / TurnFailure
│   ├── PreTool / PostTool
│   ├── PreCompact / PostCompact
│   ├── TTS lifecycle
│   └── governed proposal boundary
│
├── Task Runtime
│   ├── foreground task
│   ├── background task
│   ├── scheduled task
│   ├── resumable task
│   └── task transcript
│
└── Inspector UI
    ├── context view
    ├── memory view
    ├── action view
    ├── provider view
    ├── voice latency view
    └── benchmark view
```

---

## 25. 补充路线图：从 Runtime 到 Claude Replacement Client

### 25.1 J-4 — Julia Client Shell MVP

目标：不增加认知能力，只建立真正客户端入口。

交付：

```text
scripts/julia_client.py 或 ui/julia_client/*
Command Runtime
Session Ledger v1
PromptInput text mode
/trace /context /memory /provider /voice commands
```

验收：

- 不再需要复杂 CLI 参数启动常用会话。
- slash command 不进入 Provider prompt。
- 每轮写入 Canonical TurnRecord。
- 可查看当前 context/memory/action trace。

---

### 25.2 J-5 — Permission UX + Action Governance Productization

目标：把已有 Action Governance 变成 Claude Code 等价的用户体验。

交付：

```text
PermissionPrompt
PermissionRuleStore
ActionDecisionInspector
CapabilityRiskView
```

验收：

- 文件写入类请求显示 ask dialog。
- identity mutation 直接 reject 并显示 invariant reason。
- allow once / deny 能进入 trace。
- capability 不可绕过 governance。

---

### 25.3 J-6 — Canonical Session Ledger + Resume

目标：统一 transcript、runtime trace、context state。

交付：

```text
SessionLedger
TurnRecord schema
TranscriptProjection
RuntimeTraceProjection
ResumeIndex
```

验收：

- 新会话可从 ledger 恢复最近状态。
- archive 不再是事实真源，只是 projection。
- compact boundary 可回放。
- trace digest 可审计。

---

### 25.4 J-7 — Compact Lifecycle Productization

目标：把 Context OS compact 接入真实客户端生命周期。

交付：

```text
/compact
auto compact trigger
pre/post compact hooks
compact checkpoint
resurrection benchmark
```

验收：

- 长会话达到预算阈值自动 compact。
- compact 后 Julia 身份事实保持一致。
- compact 前后 active task/open loop 不丢失。
- compact summary 不进入 governed identity facts。

---

### 25.5 J-8 — Task Runtime

目标：从 turn-level action loop 升级为 client-level task system。

交付：

```text
TaskRecord
BackgroundTaskRunner
TaskTranscript
TaskPermissionScope
TaskCancel/Pause/Resume
```

验收：

- 长任务不阻塞前台对话。
- task 有独立 transcript 与 permission scope。
- task 输出不能直接改 memory，必须走 governed proposal。

---

### 25.6 J-9 — Workspace / Tool UX

目标：建立 Claude Code 等价的 workspace 操作面。

交付：

```text
WorkspaceManager
FileReferenceResolver
DiffPreview
ToolResultRenderer
ReadOnlyCommandValidator
```

验收：

- 文件读写路径可解释。
- diff 可预览。
- bash/read-only 命令有独立 validation。
- workspace state 进入 SessionLedger，不进入 identity memory。

---

### 25.7 ADR 补充建议

建议新增以下 ADR：

#### ADR-023 Client Shell as Product Boundary

Context：当前 CLI 已无法承载 Claude replacement 目标。

Decision：Julia Agent Client Shell 成为产品边界；CLI 降级为测试/运维入口。

Trigger：启动 J-4。

---

#### ADR-024 Slash Command Control Plane

Context：Claude Client 将 slash command 作为本地控制面，而非 prompt 内容。

Decision：Julia slash commands 必须被 Command Runtime 拦截；不得进入 Provider Prompt，除非显式设计为 prompt command。

Trigger：实现 `/voice`、`/memory`、`/context`、`/provider`。

---

#### ADR-025 Canonical Session Ledger

Context：archive 与 runtime trace 分离导致恢复、审计、compact 边界复杂。

Decision：SessionLedger 成为唯一 turn-level 事实记录；archive/trace 是投影。

Trigger：J-6。

---

#### ADR-026 Hook Runtime Proposal Boundary

Context：Claude hooks 强大但若直接修改 memory/action 会破坏 Julia governance。

Decision：Hook 只能提交 governed proposal；不能直接写 identity/memory/action authority。

Trigger：J-4/J-7。

---

#### ADR-027 Client-Level Task Runtime

Context：Action Loop 只能覆盖单轮行为，不能覆盖 Claude 等价的后台任务。

Decision：引入 Task Runtime，区分 foreground turn 与 background task。

Trigger：J-8。

---

### 25.8 更新后的下一阶段优先级

```text
P0  Julia Client Shell MVP
P0  Command Runtime / Slash Commands
P0  Canonical Session Ledger
P0  Permission UX for Action Governance
P1  Compact Lifecycle Productization
P1  Hook Runtime
P1  Task Runtime
P1  Workspace / Tool UX
P1  Trace / Context / Memory Inspector
P2  Plugin / Skill / MCP Marketplace
```

最终判断：

```text
Julia Runtime 的认知内核已经接近可用；
距离 Claude Replacement 的主要差距已经转移到 Client OS。
```

