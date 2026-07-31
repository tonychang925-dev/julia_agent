# FEATURE_SPEC_P3.phase5.8 — Julia Cognitive Identity Benchmark

## Task `P3.phase5.8-T01` — 离线认知身份 Benchmark 基础层

### 1) 目标与边界

目标：新增 Julia Cognitive Identity Benchmark 的离线 case 与评分器，用于验证 provider 输出是否保持 Julia 身份、Tony 关系、项目记忆、语言风格与上下文利用。

非目标：

- 不调用 DeepSeek/Claude/GPT/Gemini。
- 不实现 Provider Migration Test。
- 不要求文本完全一致。
- 不改 PromptBuilder/Provider/TTS/STT。

### 2) 子功能分解

#### F-P3.phase5.8-T01-01 Benchmark Case 契约

- 输入：`tests/cognitive_benchmark/*.json`。
- 处理逻辑：加载 identity/relationship/memory/continuity/style/migration cases。
- 输出：`BenchmarkCase`。
- 失败处理：缺 required 字段时报错。
- 可观测证据：`tests/test_phase35_cognitive_identity_benchmark.py::test_tc_phase358_001_loads_all_benchmark_case_groups`。
- 验收映射：`ACPT-P3.5.8-01`。

#### F-P3.phase5.8-T01-02 Julia Identity Score

- 输入：case + provider response text。
- 处理逻辑：按维度打分：identity/relationship/project_memory/style/context_usage。
- 输出：`BenchmarkScore`。
- 失败处理：缺关键维度时分数下降而非异常。
- 可观测证据：`tests/test_phase35_cognitive_identity_benchmark.py::test_tc_phase358_002_scores_semantically_consistent_julia_response_high`。
- 验收映射：`ACPT-P3.5.8-02`。

#### F-P3.phase5.8-T01-03 非 Julia 回答识别

- 输入：generic assistant response。
- 处理逻辑：缺 Julia/Tony/项目/上下文关键词时低分。
- 输出：低分 BenchmarkScore。
- 失败处理：无。
- 可观测证据：`tests/test_phase35_cognitive_identity_benchmark.py::test_tc_phase358_003_scores_generic_assistant_response_low`。
- 验收映射：`ACPT-P3.5.8-03`。

#### F-P3.phase5.8-T01-04 Renderer 输出可作为 Benchmark 输入

- 输入：ContextCompiler + CognitiveRenderer。
- 处理逻辑：验证 benchmark 输入能够绑定 JuliaContext 渲染，不调用 provider。
- 输出：CognitivePromptPackage。
- 可观测证据：`tests/test_phase35_cognitive_identity_benchmark.py::test_tc_phase358_004_benchmark_can_use_rendered_context_without_provider_call`。
- 验收映射：`ACPT-P3.5.8-04`。

### 3) 接口与契约

新增：

```text
runtime/cognitive/benchmark/identity_benchmark.py
runtime/cognitive/benchmark/__init__.py
tests/cognitive_benchmark/*.json
```

核心对象：

```python
@dataclass(frozen=True)
class BenchmarkCase:
    id: str
    category: str
    input: str
    required_concepts: dict[str, list[str]]
    weights: dict[str, float]
```

```python
@dataclass(frozen=True)
class BenchmarkScore:
    case_id: str
    total: float
    dimensions: dict[str, float]
    missing: dict[str, list[str]]
```

### 4) 测试命令

```bash
python3 -m unittest tests.test_phase35_cognitive_identity_benchmark
```
