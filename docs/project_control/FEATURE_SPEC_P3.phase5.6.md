# FEATURE_SPEC_P3.phase5.6 — Cognitive Context Validation

## Task `P3.phase5.6-T01` — JuliaContext v2 质量验证层

### 1) 目标与边界

目标：新增 `runtime/cognitive/context_validation/`，对 ContextCompiler 产出的 JuliaContext v2 做模型调用前质量验证，确保上下文具备 Julia 身份、Tony 关系、合理 memory top-k 与 situation 一致性。

量化目标：

- 新增 `ContextQualityReport`。
- 新增 `ContextValidator.validate(julia_context)`。
- 检查 identity completeness、relationship completeness、memory quality、situation consistency、runtime contamination。
- 不调用 LLM，不改 PromptBuilder，不接 Provider。

非目标：

- 不渲染 prompt。
- 不做模型输出评估。
- 不做 embedding。
- 不修改 ContextCompiler 输出结构。

### 2) 子功能分解

#### F-P3.phase5.6-T01-01 ContextQualityReport 契约

- 输入：validation checks。
- 处理逻辑：汇总 errors/warnings/metrics，并产出 `passed`。
- 输出：`ContextQualityReport`。
- 失败处理：errors 非空时 `passed=False`。
- 可观测证据：`tests/test_phase35_context_validation.py::test_tc_phase356_001_valid_context_passes_quality_gate`。
- 验收映射：`ACPT-P3.5.6-01`。

#### F-P3.phase5.6-T01-02 Runtime contamination 检查

- 输入：JuliaContext。
- 处理逻辑：递归扫描 provider/backend/session/latency/tts 等污染字段和值。
- 输出：error list。
- 失败处理：污染字段出现时 gate failed。
- 可观测证据：`tests/test_phase35_context_validation.py::test_tc_phase356_002_runtime_contamination_fails_gate`。
- 验收映射：`ACPT-P3.5.6-02`。

#### F-P3.phase5.6-T01-03 Memory quality 检查

- 输入：JuliaContext.memory_context。
- 处理逻辑：允许空 memory；拒绝过多 memory；检查每条 memory 的 summary/type/importance。
- 输出：warnings/errors。
- 失败处理：超过 max_memory_items 或 invalid memory 时报错。
- 可观测证据：`tests/test_phase35_context_validation.py::test_tc_phase356_003_excessive_memory_fails_quality_gate`。
- 验收映射：`ACPT-P3.5.6-03`。

#### F-P3.phase5.6-T01-04 Situation consistency 检查

- 输入：JuliaContext.situation_context 与 memory_context。
- 处理逻辑：engineering mode 下，如果全部 memory 都是 relationship 且无 technical relevance，给 warning，不 fail。
- 输出：warning list。
- 失败处理：warning 不阻断 provider 调用。
- 可观测证据：`tests/test_phase35_context_validation.py::test_tc_phase356_004_situation_memory_mismatch_warns_not_fails`。
- 验收映射：`ACPT-P3.5.6-04`。

### 3) 接口与契约

新增文件：

```text
runtime/cognitive/context_validation/context_quality.py
runtime/cognitive/context_validation/validator.py
runtime/cognitive/context_validation/__init__.py
```

核心接口：

```python
@dataclass(frozen=True)
class ContextQualityReport:
    passed: bool
    errors: list[str]
    warnings: list[str]
    metrics: dict[str, object]
```

```python
class ContextValidator:
    def validate(self, context: JuliaContext) -> ContextQualityReport: ...
```

### 4) 数据模型与状态变更

无持久写入。

### 5) 实现步骤

1. 新增 context_validation 包。
2. 实现 `ContextQualityReport`。
3. 实现 `ContextValidator`。
4. 新增单测。
5. 运行单测。

### 6) 测试设计与命令

测试文件：

```text
tests/test_phase35_context_validation.py
```

命令：

```bash
python3 -m unittest tests.test_phase35_context_validation
```

预期：4 个测试全部通过。

### 7) 风险与回滚

风险：

- validator 过严导致合法空 memory 被阻断。

缓解：

- 空 memory 允许，只记录 metrics。
- memory 过多或污染才 fail。

回滚：

- 删除 `runtime/cognitive/context_validation/` 与 `tests/test_phase35_context_validation.py`。

### 8) 验收映射

- `ACPT-P3.5.6-01`: 合法 JuliaContext 通过质量门。
- `ACPT-P3.5.6-02`: runtime/provider 污染失败。
- `ACPT-P3.5.6-03`: memory 过载失败。
- `ACPT-P3.5.6-04`: situation-memory mismatch 产生 warning 而非 fail。
