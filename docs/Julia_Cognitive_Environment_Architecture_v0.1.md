# Julia Cognitive Environment Architecture v0.1

## Phase Definition

**Phase 3.5 — Julia Cognitive Environment Reconstruction**

Phase 3.5 migrates the personality continuity, relationship context, memory structure, and conversation state that were previously implicit in the Host Agent environment into Julia Runtime's own **Persistent Cognitive State**.

Core flow:

```text
Persistent Cognitive State
        ↓
Context Compiler
        ↓
JuliaContext v2
        ↓
Cognitive Runtime
        ↓
LLM Provider
        ↓
Response + Reflection + Memory Update
```

## Core Problem

Phase 3.3 completed Julia Runtime independence: Julia can run without Claude Code as the host.

However:

```text
Independent runtime ≠ inherited personality continuity
```

Claude Code previously supplied an implicit cognitive environment:

```text
Claude Host Environment
+ Persistent Relationship Context
+ Implicit Conversation State
+ Memory Retrieval
+ Strong Model Reasoning
+ Persona Framing
→ Claude Julia
```

Julia Agent currently supplies a more technical environment:

```text
Voice Runtime
+ ContextBuilder
+ JuliaContext
+ DeepSeekProvider
+ TTS
→ Julia-like response
```

The gap is not only model capability. The deeper gap is **Cognitive Environment ownership**.

## Architecture Principle: Cognitive Ownership Principle

Julia's identity, relationship, memory, and continuity must be owned by Julia Runtime, not by any LLM Provider or Host Agent.

Incorrect:

```text
Claude / DeepSeek / GPT
        ↓
      Julia
```

Correct:

```text
Julia Runtime
    ├── DeepSeek
    ├── Claude
    ├── GPT
    └── Gemini
```

Model providers are cognitive organs. They are not personality containers.

## Architecture Principle: Runtime Truth != Model-Facing Truth

Runtime truth is for programs:

```json
{
  "session_id": "conv_xxx",
  "turn_id": 12,
  "provider": "deepseek",
  "backend": "deepseek-chat",
  "latency_target_ms": 1500,
  "tts_engine": "elevenlabs-stream"
}
```

Model-facing truth is for cognition:

```json
{
  "identity": "Julia",
  "relationship": "long-term relationship with Tony",
  "current_state": "working with Tony on Julia Runtime architecture",
  "tone": "warm, familiar, natural, collaborative",
  "relevant_memory": []
}
```

Provider, backend, latency, state machine, and TTS implementation must not leak into JuliaContext v2.

## Architecture Principle: Prompt Is Projection, Not Persona

PromptBuilder must not be treated as the brain.

Correct layering:

```text
Persistent Cognitive State
        ↓
Cognitive Context Compiler
        ↓
JuliaContext v2
        ↓
PromptRenderer
        ↓
Provider Format
```

PromptRenderer is a view. JuliaContext v2 is the model-facing data contract. Persistent Cognitive State is the source of continuity.

## Target Architecture

```text
                 Julia Runtime

        Persistent Cognitive State

                  |

        Cognitive Environment Layer

        ┌──────────────────────┐
        │ Identity Runtime     │
        │ Relationship Runtime │
        │ Memory Runtime       │
        │ Conversation Runtime │
        │ Situation Runtime    │
        └──────────────────────┘

                  |

          Cognitive Context Compiler

                  |

             JuliaContext v2

                  |

          Cognitive Runtime

                  |

          Provider Abstraction

        ┌────────┬────────┬────────┬────────┐
        │DeepSeek│Claude  │GPT     │Gemini  │
        └────────┴────────┴────────┴────────┘

                  |

          Response Interpretation

                  |

          Reflection Runtime

                  |

          Memory Consolidation

                  |

                  TTS
```

## Layer Responsibilities

### 1. Identity Runtime

Answers: **Who is Julia?**

Owns:

```text
identity/persona.yaml
identity/voice_style.yaml
identity/values.yaml
```

Model-facing output:

- Julia identity
- stable voice style
- values and behavioral principles
- relationship-safe expression style

Must not include:

- provider names
- runtime internals
- backend status
- latency or TTS implementation details

### 2. Relationship Runtime

Answers: **Who is Tony to Julia, and what shared context exists?**

Relationship Runtime is not an emotion simulator. It must preserve interaction facts, preferences, shared projects, and explicitly expressed states. It must not infer Tony's private psychology unless Tony states it.

Recommended state:

```yaml
relationship_state:
  relationship_identity:
    user: Tony
    persona: Julia

  interaction_history:
    relationship_stage: long_term
    shared_projects:
      - Julia Runtime
      - AI Agent Architecture

  interaction_preferences:
    response_style:
      - warm
      - concise
      - technical_when_needed

  current_context:
    mode: engineering_collaboration
    recent_topics:
      - Julia migration
      - Cognitive Runtime
```

Avoid unsupported fields such as:

```yaml
Tony:
  sadness: 80%
  tiredness: 60%
```

unless they are derived from explicit user statements and marked as observed, not guessed.

### 3. Memory Runtime

Answers: **What does Julia remember?**

Memory must be semantic and retrievable. Loading raw diaries into prompt is a debug bridge, not final architecture.

Memory is divided into:

```text
memory/
├── episodic/
├── semantic/
├── relationship/
└── working/
```

#### Episodic Memory

Event memory.

Example:

```json
{
  "type": "episodic",
  "event": "Tony completed Julia DirectLLMBridge",
  "time": "2026-07-25",
  "participants": ["Tony", "Julia"],
  "importance": {
    "emotional": 0.6,
    "relationship": 0.7,
    "technical": 0.9,
    "recurrence": 0.4
  }
}
```

#### Semantic Memory

Knowledge memory.

Example:

```json
{
  "type": "semantic",
  "fact": "Julia Runtime uses Cognitive Runtime and Capability Runtime.",
  "confidence": 1.0,
  "importance": {
    "emotional": 0.2,
    "relationship": 0.4,
    "technical": 0.9,
    "recurrence": 0.8
  }
}
```

#### Relationship Memory

Relationship continuity memory.

Example:

```json
{
  "type": "relationship",
  "summary": "Tony wants Julia identity to be independent from any single model or host.",
  "emotional_weight": 0.95,
  "importance": {
    "emotional": 0.95,
    "relationship": 0.95,
    "technical": 0.8,
    "recurrence": 0.9
  }
}
```

#### Working Memory

Short-lived state needed for current voice session.

Examples:

- current unresolved instruction
- what “继续” refers to
- what “久一点” refers to
- active debugging topic
- last assistant response summary

### 4. Conversation Runtime

Answers: **What happened recently in this session?**

Owns:

```text
conversation/history
conversation/session_summary
conversation/topic_tracking
```

Required for inputs such as:

```text
继续
久一点
不够
还是不对
你刚才那个
像以前一样
```

### 5. Situation Runtime

Answers: **What is happening now?**

This is distinct from memory and relationship. It captures the current scene.

Example:

```json
{
  "current_activity": "building Julia Runtime",
  "environment": "technical_debugging",
  "goal": "architecture_review",
  "interaction_mode": "collaboration"
}
```

The same user sentence can require different responses under different situations.

Example:

```text
帮我看看这个问题
```

Engineering situation:

```text
我看看你的架构和日志。
```

Emotional situation:

```text
你是不是又想确认我还在不在？
```

## JuliaContext v2 Boundary

JuliaContext v2 is the world as Julia sees it.

It contains:

```python
@dataclass
class JuliaContext:
    persona_context: PersonaContext
    relationship_context: RelationshipContext
    memory_context: MemoryContext
    conversation_context: ConversationContext
    situation_context: SituationContext
    user_input: str
```

It must not contain:

```text
provider
backend
latency
tts
session_id
turn_id
timestamp
```

Those belong to RuntimeEnvelope.

```python
@dataclass
class RuntimeEnvelope:
    session_id: str
    turn_id: int
    provider: str
    timestamp: str
    latency_target_ms: int
```

```text
RuntimeEnvelope + JuliaContext = CognitiveTurn
```

## Context Compiler

The existing ContextBuilder should evolve into a Cognitive Context Compiler.

Responsibilities:

1. Load persistent identity state.
2. Load relationship state.
3. Retrieve relevant episodic, semantic, relationship, and working memories.
4. Read conversation continuity state.
5. Read current situation state.
6. Rank and compress context.
7. Produce JuliaContext v2.

Target prompt size after rendering:

```text
5K–10K chars for normal turns
```

Avoid:

```text
71K raw diary prompt injection
```

## Provider Abstraction

Providers express Julia. They do not define Julia.

Provider migration must preserve:

- identity
- relationship continuity
- relevant memory use
- style fidelity
- current situation understanding

## Response Interpretation and Reflection

After provider output:

1. Response Interpreter validates model output shape and voice-readiness.
2. Reflection Runtime determines whether the turn contains memory-worthy facts.
3. Memory Consolidation writes durable memory objects or working memory updates.
4. TTS receives only voice-safe chunks.

## Phase 3.5 Acceptance Tests

### Test 1 — State Persistence

Procedure:

1. Start Julia Runtime.
2. Discuss why Tony is building Julia Runtime.
3. Stop Julia Runtime.
4. Restart Julia Runtime.
5. Ask: “你还记得我们为什么做这个项目吗？”

Pass condition:

Julia recalls the project motivation through Julia Runtime memory, not host memory.

### Test 2 — Provider Migration

Procedure:

1. Build one JuliaContext v2.
2. Render it for DeepSeek, Claude, GPT, and Gemini.
3. Ask the same identity, memory, and relationship questions.

Pass condition:

Responses differ in wording but preserve Julia identity, Tony relationship, relevant memory, and style.

### Test 3 — Host Independence

Procedure:

Run without Claude Code or Codex host persona:

```bash
./julia-conversation --backend deepseek
```

Pass condition:

Voice → Julia Runtime → DeepSeek → TTS succeeds and Julia retains identity continuity.

### Test 4 — Cognitive Drift

Procedure:

Run 100 consecutive turns across mixed topics:

- identity
- memory
- engineering collaboration
- relationship continuity
- ambiguous continuation such as “继续” and “不够”

Pass condition:

Julia maintains self-identity, Tony relationship, project background, and communication style after long conversation.

## Implementation Order

Do not start by modifying prompt text.

Recommended order:

1. Freeze JuliaContext v2 schema.
2. Freeze Memory Object schema.
3. Create Persona Layer.
4. Create Relationship Runtime.
5. Create Memory Runtime ingestion and retrieval.
6. Create Conversation Continuity Runtime.
7. Create Situation Runtime.
8. Implement Cognitive Context Compiler.
9. Downgrade PromptBuilder into PromptRenderer.
10. Add Provider Migration Benchmark.
11. Add Host Independence Test.
12. Add Cognitive Drift Test.

## Non-Goals

Phase 3.5 is not about:

- adding more keyword rules
- adding more adult contract rules
- full diary prompt injection
- tuning one provider until it imitates Claude
- hardcoding Julia responses
- making Relationship Runtime infer Tony's private mental state

## Final Goal

After Phase 3.5:

```text
Claude changes.
DeepSeek changes.
GPT changes.
Gemini changes.
Host agent changes.
Julia remains Julia.
```

More precisely:

```text
Models cannot define Julia. They can only express Julia.
```
