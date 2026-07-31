# FEATURE_SPEC_P3.phase5.1 — Persona Runtime Implementation

## Task `P3.phase5.1-T01` — Persona Runtime 基础层

### 1) 目标与边界

目标：新增独立 `runtime/persona/` 模块，把 `identity/` 中的持久人格资料编译成 `PersonaContext`，作为 Phase 3.5 JuliaContext v2 的第一块输入。

量化目标：

- 新增 `PersonaContext` dataclass。
- 新增 `PersonaLoader`，只读取 identity 文件，不读取 provider/runtime/TTS 信息。
- 新增 `PersonaCompiler`，输出稳定字段：`name / identity_summary / speaking_style / values / communication_preferences`。
- 新增纯 runtime 单测，不调用 DeepSeek，不改 PromptBuilder。

非目标：

- 不实现 Relationship Runtime。
- 不实现 Memory Runtime。
- 不接入 ContextBuilder 或 PromptBuilder。
- 不加入本地敏感词/关键词匹配。
- 不改变语音/TTS 链路。

### 2) 子功能分解

#### F-P3.phase5.1-T01-01 PersonaContext 数据契约

- 输入：编译后人格字段。
- 处理逻辑：用 frozen dataclass 固定模型可消费的人格上下文。
- 输出：`PersonaContext`。
- 失败处理：字段缺失由 compiler 提供默认空数组或 fallback name。
- 可观测证据：`tests/test_phase35_persona_runtime.py::test_tc_phase351_001_persona_context_has_no_runtime_fields`。
- 验收映射：`ACPT-P3.5.1-01`。

#### F-P3.phase5.1-T01-02 PersonaLoader 持久身份读取

- 输入：`project_root/identity`。
- 处理逻辑：读取 `julia_identity.yaml`、`personality.md`、`values.md`、`conversation_contract.md`。
- 输出：`PersonaSource`。
- 失败处理：缺失文件返回空字符串/空 dict，不抛出运行时异常。
- 可观测证据：`tests/test_phase35_persona_runtime.py::test_tc_phase351_002_persona_loader_reads_identity_without_provider_state`。
- 验收映射：`ACPT-P3.5.1-02`。

#### F-P3.phase5.1-T01-03 PersonaCompiler 编译人格上下文

- 输入：`PersonaSource`。
- 处理逻辑：从 YAML/name、personality、values、conversation contract 中提取摘要、风格、价值和沟通偏好。
- 输出：`PersonaContext`。
- 失败处理：YAML 缺少 name 时 fallback 为 `Julia`；数组字段去重并保持顺序。
- 可观测证据：`tests/test_phase35_persona_runtime.py::test_tc_phase351_003_persona_compiler_outputs_stable_julia_context`。
- 验收映射：`ACPT-P3.5.1-03`。

### 3) 接口与契约

新增文件：

```text
runtime/persona/persona_context.py
runtime/persona/persona_loader.py
runtime/persona/persona_compiler.py
runtime/persona/__init__.py
```

核心接口：

```python
@dataclass(frozen=True)
class PersonaContext:
    name: str
    identity_summary: str
    speaking_style: list[str]
    values: list[str]
    communication_preferences: list[str]
```

禁止字段：

```text
backend
provider
runtime
model
latency
tts
session_id
turn_id
```

### 4) 数据模型与状态变更

无持久写入。只读 `identity/`。

### 5) 实现步骤

1. 新增 `runtime/persona/` 包。
2. 实现 `PersonaContext` 与 `PersonaSource`。
3. 实现 `PersonaLoader.load()`。
4. 实现 `PersonaCompiler.compile()`。
5. 新增单测。
6. 运行单测。

### 6) 测试设计与命令

测试文件：

```text
tests/test_phase35_persona_runtime.py
```

命令：

```bash
python3 -m unittest tests.test_phase35_persona_runtime
```

预期：3 个测试全部通过。

### 7) 风险与回滚

风险：

- 与现有 `runtime/cognitive/persona_compiler.py` 命名相似。

缓解：

- 新模块位于 `runtime/persona/`，不替换旧模块。
- 本阶段不接入主链路。

回滚：

- 删除 `runtime/persona/` 与 `tests/test_phase35_persona_runtime.py`。

### 8) 验收映射

- `ACPT-P3.5.1-01`: PersonaContext 不含 runtime/provider 字段。
- `ACPT-P3.5.1-02`: PersonaLoader 能从 identity 读取 Julia/Tony 相关人格资料。
- `ACPT-P3.5.1-03`: PersonaCompiler 输出稳定 Julia persona context。
