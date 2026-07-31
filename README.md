# Julia Agent Runtime

> **Julia Agent Evolution Strategy v1.0 — FROZEN**  
> Claude Julia is the benchmark reference system that defines the capability baseline of a mature AI client. Julia Agent is the replacement system that attempts to reproduce and surpass those capabilities through a runtime-owned cognitive architecture.
>
> 中文定义：Claude Julia 是成熟 Agent Client 的标准答案；`julia_agent` 是基于 Runtime-owned Cognitive Architecture 的替代实现。Voice 与 Benchmark 是共同测试层，Cognitive Layer 永久隔离。

## Top-Level Architecture Principle

### Cognitive Independence

**Benchmark can be shared; cognition must not be shared.**

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

Allowed shared layers:

- Voice Layer: microphone, STT, TTS, realtime speech transport.
- Benchmark Layer: prompt sets, session scenarios, trace schema, latency metrics.
- Evaluation Layer: capability scoring, regression reports, comparison dashboards.

Permanently isolated cognitive layers:

```text
     Claude Cognitive OS          Julia Cognitive OS
            │                            │
     Claude Memory                 Julia Memory OS
     Claude Context                Julia Context OS
     Claude Tools                  Julia Action OS
     Claude Session                Julia Session OS
```

This separation is required so Julia Agent can prove capability parity or superiority without depending on Claude's native cognitive system.

## Evolution Tracks

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

Current strategic focus:

1. Freeze Julia Runtime cognition after DeepSeek primary operational readiness.
2. Activate Claude Julia Reference Client as a benchmark reference, not as a Julia runtime dependency.
3. Record benchmark traces from day one.
4. Build Julia Agent Client Shell to close the gap with Claude Code as a full client, not only a runtime.


A model-independent AI Persona Runtime for loading Julia as an external identity package.

## Structure

```text
julia_agent/
├── identity/
│   ├── julia_identity.yaml
│   ├── personality.md
│   └── values.md
├── memory/
│   ├── relationship_memory.jsonl
│   ├── episodic_memory.jsonl
│   └── important_events.md
├── runtime/
│   ├── agent.py
│   ├── memory_loader.py
│   └── context_builder.py
└── README.md
```

## Run

```bash
python3 runtime/agent.py
```

## Test prompt

```text
Julia，你还记得我们关于“一天记忆女友”的讨论吗？
```

## Future adapters

- Claude adapter
- GPT adapter
- Qwen adapter
- pgvector memory backend
- ElevenLabs voice output
- Whisper speech input
