# FEATURE_SPEC_P3.phase5.7 — Cognitive Rendering Layer

## Task `P3.phase5.7-T01` — JuliaContext v2 Provider-Neutral Rendering

### 1) 目标与边界

目标：新增 `runtime/cognitive/rendering/`，将已验证的 JuliaContext v2 渲染为 provider-neutral `CognitivePromptPackage`，为后续 DeepSeek/Claude/GPT/Gemini formatter 提供统一输入。

量化目标：

- 新增 `CognitivePromptPackage` dataclass。
- 新增 `CognitiveRenderer.render(context)`。
- 新增 `ProviderFormatter.to_openai_messages(package)` 作为第一版 provider format 输出。
- Renderer 只接收 JuliaContext v2，不直接读取 identity/memory 文件。
- Renderer 输出不包含 provider/backend/session/latency/TTS/STT。
- 新增纯 runtime 单测，不调用 DeepSeek，不替换旧 PromptBuilder。

非目标：

- 不改旧 `runtime/cognitive/prompt_builder.py`。
- 不接入 DeepSeekProvider。
- 不做 provider migration runtime 切换。
- 不调模型回答。

### 2) 子功能分解

#### F-P3.phase5.7-T01-01 CognitivePromptPackage 契约

- 输入：system_context、conversation_messages、memory_summary、style_constraints。
- 处理逻辑：用 frozen dataclass 固定 provider-neutral prompt package。
- 输出：`CognitivePromptPackage`。
- 失败处理：Renderer 提供空 memory_summary fallback。
- 可观测证据：`tests/test_phase35_cognitive_rendering.py::test_tc_phase357_001_renderer_outputs_provider_neutral_package`。
- 验收映射：`ACPT-P3.5.7-01`。

#### F-P3.phase5.7-T01-02 JuliaContext-only Renderer

- 输入：JuliaContext v2。
- 处理逻辑：从 persona/relationship/memory/situation/conversation/user_input 渲染 system_context 与 messages。
- 输出：`CognitivePromptPackage`。
- 失败处理：空 memory list 输出 `No relevant memory selected for this turn.`。
- 可观测证据：`tests/test_phase35_cognitive_rendering.py::test_tc_phase357_002_renderer_uses_context_without_runtime_leakage`。
- 验收映射：`ACPT-P3.5.7-02`。

#### F-P3.phase5.7-T01-03 ProviderFormatter 输出 OpenAI messages

- 输入：CognitivePromptPackage。
- 处理逻辑：输出 OpenAI-compatible messages：system + conversation_messages。
- 输出：`list[dict[str, str]]`。
- 失败处理：空 user content 仍由 ContextCompiler/user_input 阶段保证；formatter 不读取外部文件。
- 可观测证据：`tests/test_phase35_cognitive_rendering.py::test_tc_phase357_003_provider_formatter_outputs_openai_messages`。
- 验收映射：`ACPT-P3.5.7-03`。

#### F-P3.phase5.7-T01-04 Provider Independence 渲染稳定性

- 输入：不同 RuntimeEnvelope 下相同 JuliaContext。
- 处理逻辑：渲染结果只依赖 JuliaContext。
- 输出：相同 CognitivePromptPackage。
- 失败处理：provider/backend 不进入 package。
- 可观测证据：`tests/test_phase35_cognitive_rendering.py::test_tc_phase357_004_same_context_renders_same_package_across_providers`。
- 验收映射：`ACPT-P3.5.7-04`。

### 3) 接口与契约

新增文件：

```text
runtime/cognitive/rendering/model_view.py
runtime/cognitive/rendering/renderer.py
runtime/cognitive/rendering/provider_formatter.py
runtime/cognitive/rendering/__init__.py
```

核心接口：

```python
@dataclass(frozen=True)
class CognitivePromptPackage:
    system_context: str
    conversation_messages: list[dict[str, str]]
    memory_summary: str
    style_constraints: list[str]
```

```python
class CognitiveRenderer:
    def render(self, context: JuliaContext) -> CognitivePromptPackage: ...
```

```python
class ProviderFormatter:
    def to_openai_messages(self, package: CognitivePromptPackage) -> list[dict[str, str]]: ...
```

### 4) 数据模型与状态变更

无持久写入。

### 5) 实现步骤

1. 新增 rendering 包。
2. 实现 `CognitivePromptPackage`。
3. 实现 `CognitiveRenderer`。
4. 实现 `ProviderFormatter`。
5. 新增单测。
6. 运行单测。

### 6) 测试设计与命令

测试文件：

```text
tests/test_phase35_cognitive_rendering.py
```

命令：

```bash
python3 -m unittest tests.test_phase35_cognitive_rendering
```

预期：4 个测试全部通过。

### 7) 风险与回滚

风险：

- Renderer 被误用为新 PromptBuilder 并重新开始堆规则。

缓解：

- Renderer 只消费 JuliaContext。
- 不直接读取文件。
- 不接 Provider。

回滚：

- 删除 `runtime/cognitive/rendering/` 与 `tests/test_phase35_cognitive_rendering.py`。

### 8) 验收映射

- `ACPT-P3.5.7-01`: Renderer 输出 provider-neutral package。
- `ACPT-P3.5.7-02`: Renderer 不泄漏 runtime/provider/TTS/STT 字段。
- `ACPT-P3.5.7-03`: ProviderFormatter 能输出 OpenAI-compatible messages。
- `ACPT-P3.5.7-04`: 相同 JuliaContext 跨 provider envelope 渲染稳定。
