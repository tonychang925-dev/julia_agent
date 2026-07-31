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


## Domain Architecture Position

`julia_agent` is a **general-purpose Agent Runtime architecture**, not a financial-only application.

The runtime-owned cognitive architecture is designed to host multiple domain capabilities behind governed contracts:

```text
Julia Agent Runtime
  ├── Identity OS
  ├── Memory OS
  ├── Context OS
  ├── Action Governance
  ├── Capability Router
  ├── Provider Adaptation
  └── Domain Capability Providers
        ├── financial/        # first domain: Julia Financial Analyst
        ├── healthcare/       # future possible domain
        ├── coding/           # future possible domain
        └── personal_assist/  # future possible domain
```

The financial analyst work is the first production domain integration. It must not become a second Context OS, Memory OS, or Agent Runtime. Financial modules provide domain facts, typed contracts, EvidenceRef-backed reports, and governed workflows; Julia Context OS remains the single authority for model-facing context selection, budget, provenance, and projection.

Core principle:

```text
One Julia Cognitive Runtime.
Many domain capability providers.
No domain-specific duplicate Agent OS.
```

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
├── docs/                         # architecture, phase contracts, reports
├── runtime/                      # generic Julia Agent Runtime
│   ├── context_os/               # governed context lifecycle
│   ├── cognitive/                # cognitive projection/provider adaptation
│   ├── memory_loader.py          # memory loading boundary
│   ├── action/                   # action governance and loop runtime
│   ├── capability/               # capability contracts/providers
│   │   └── financial/            # first domain capability provider
│   ├── conversation_runtime/     # realtime/text conversation runtime
│   ├── conversation_archive/     # transcript/archive utilities
│   └── voice_validation/         # voice/runtime validation
├── frontend/                     # JuliaCopilot workbench entry
├── schemas/                      # public runtime schemas
├── scripts/                      # operational scripts without local secrets
├── stt/                          # speech-to-text adapters
├── tts/                          # text-to-speech adapters
└── tests/                        # regression and phase acceptance tests
```

Private runtime data stays outside the public repository: `identity/`, `memory/`, `data/`, `tmp/`, and `audio/`.

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
