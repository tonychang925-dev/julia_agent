# FEATURE_SPEC_P3.phase5.5 — Cognitive Context Compiler Implementation

## Task `P3.phase5.5-T01` — Context Compiler 与 JuliaContext v2 基础层

### 1) 目标与边界

目标：新增 `runtime/cognitive/context_compiler/`，将 Persona / Relationship / Memory / Situation Runtime 输出编译为 JuliaContext v2，作为后续 PromptRenderer 和 Provider Migration 的统一认知输入。

量化目标：

- 新增 JuliaContext v2 dataclass。
- 新增 RuntimeEnvelope dataclass。
- 新增 CognitiveTurn dataclass。
- 新增 ContextCompiler。
- Memory 只选择 top-k relevant memories，不全量进入 JuliaContext。
- conversation_context 第一版保留占位 dict，不重构现有 Conversation Runtime。
- 新增纯 runtime 单测，不调用 DeepSeek，不改 PromptBuilder。

非目标：

- 不替换旧 `runtime/cognitive/context_builder.py`。
- 不改 `PromptBuilder`。
- 不改 Provider。
- 不做 embedding。
- 不做 conversation history 重构。

### 2) 子功能分解

#### F-P3.phase5.5-T01-01 JuliaContext v2 数据契约

- 输入：PersonaContext / RelationshipContext / selected MemoryObject / SituationContext / conversation_context / user_input。
- 处理逻辑：用 frozen dataclass 固定模型可消费的 Julia world state。
- 输出：`JuliaContext`。
- 失败处理：compiler 提供空 conversation_context 与空 memory list fallback。
- 可观测证据：`tests/test_phase35_context_compiler.py::test_tc_phase355_001_context_compiler_composes_core_contexts`。
- 验收映射：`ACPT-P3.5.5-01`。

#### F-P3.phase5.5-T01-02 RuntimeEnvelope 与 JuliaContext 分离

- 输入：RuntimeEnvelope 与 user_input。
- 处理逻辑：RuntimeEnvelope 只用于执行元数据，不进入 JuliaContext。
- 输出：`CognitiveTurn(runtime_envelope, julia_context)`。
- 失败处理：runtime metadata 不参与 context field 构造。
- 可观测证据：`tests/test_phase35_context_compiler.py::test_tc_phase355_002_julia_context_excludes_runtime_envelope_fields`。
- 验收映射：`ACPT-P3.5.5-02`。

#### F-P3.phase5.5-T01-03 MemorySelector top-k 检索

- 输入：user_input 与 MemoryRuntime。
- 处理逻辑：调用 `MemoryRuntime.retrieve(user_input, limit=memory_limit)`。
- 输出：top-k memory_context。
- 失败处理：MemoryRuntime 空结果时返回空 list。
- 可观测证据：`tests/test_phase35_context_compiler.py::test_tc_phase355_003_context_compiler_selects_relevant_memory_only`。
- 验收映射：`ACPT-P3.5.5-03`。

#### F-P3.phase5.5-T01-04 Provider Independence 准备

- 输入：不同 RuntimeEnvelope provider/backend。
- 处理逻辑：同一 user_input 下 JuliaContext 内容不受 provider/backend 影响。
- 输出：不同 runtime envelope + 相同 JuliaContext。
- 失败处理：provider/backend 只保存在 envelope。
- 可观测证据：`tests/test_phase35_context_compiler.py::test_tc_phase355_004_same_input_same_context_across_providers`。
- 验收映射：`ACPT-P3.5.5-04`。

### 3) 接口与契约

新增文件：

```text
runtime/cognitive/context_compiler/context_policy.py
runtime/cognitive/context_compiler/julia_context.py
runtime/cognitive/context_compiler/memory_selector.py
runtime/cognitive/context_compiler/context_compiler.py
runtime/cognitive/context_compiler/__init__.py
```

核心接口：

```python
@dataclass(frozen=True)
class JuliaContext:
    persona_context: PersonaContext
    relationship_context: RelationshipContext
    memory_context: list[MemoryObject]
    situation_context: SituationContext
    conversation_context: dict[str, object]
    user_input: str
```

```python
@dataclass(frozen=True)
class RuntimeEnvelope:
    session_id: str
    turn_id: int
    provider: str
    backend: str
    timestamp: str
    latency_target_ms: int
```

```python
@dataclass(frozen=True)
class CognitiveTurn:
    runtime_envelope: RuntimeEnvelope
    julia_context: JuliaContext
```

### 4) 数据模型与状态变更

无持久写入。只读已完成 runtime 输出。

### 5) 实现步骤

1. 新增 context_compiler 包。
2. 实现 dataclass 契约。
3. 实现 ContextPolicy。
4. 实现 MemorySelector。
5. 实现 ContextCompiler.compile()。
6. 新增单测。
7. 运行单测。

### 6) 测试设计与命令

测试文件：

```text
tests/test_phase35_context_compiler.py
```

命令：

```bash
python3 -m unittest tests.test_phase35_context_compiler
```

预期：4 个测试全部通过。

### 7) 风险与回滚

风险：

- 与旧 `JuliaContext` 名称冲突。

缓解：

- 新类型位于 `runtime.cognitive.context_compiler.julia_context`，不替换旧类型。
- 本阶段不接入 PromptBuilder。

回滚：

- 删除 `runtime/cognitive/context_compiler/` 与 `tests/test_phase35_context_compiler.py`。

### 8) 验收映射

- `ACPT-P3.5.5-01`: JuliaContext v2 能组合 Persona/Relationship/Memory/Situation。
- `ACPT-P3.5.5-02`: JuliaContext v2 不包含 RuntimeEnvelope 字段。
- `ACPT-P3.5.5-03`: MemoryContext 只包含 top-k relevant memories。
- `ACPT-P3.5.5-04`: 不同 provider/backend 下同一输入编译出相同 JuliaContext。
