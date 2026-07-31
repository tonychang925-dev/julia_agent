# FEATURE_SPEC_P3.phase5.4 — Situation Runtime Implementation

## Task `P3.phase5.4-T01` — Situation Runtime 基础层

### 1) 目标与边界

目标：新增独立 `runtime/situation/` 模块，把“当前正在发生什么”编译成 `SituationContext`，为 JuliaContext v2 提供 Now 层输入。

量化目标：

- 新增 `SituationContext` dataclass。
- 新增 `SituationLoader`，读取可选 `situation/situation_state.json`，缺失时使用稳定默认场景。
- 新增 `SituationRuntime`，输出 provider-independent 的当前场景上下文。
- 支持通过显式 state 文件进行 mode 切换。
- 新增纯 runtime 单测，不调用 DeepSeek，不改 PromptBuilder。

非目标：

- 不实现 Context Compiler。
- 不接入 ContextBuilder 或 PromptBuilder。
- 不读取 memory content。
- 不推断 Tony 心理状态。
- 不调模型和 TTS/STT。

### 2) 子功能分解

#### F-P3.phase5.4-T01-01 SituationContext 数据契约

- 输入：当前活动、环境、目标、交互模式、活跃话题。
- 处理逻辑：用 frozen dataclass 固定当前场景上下文。
- 输出：`SituationContext`。
- 失败处理：字段缺失由 runtime 提供默认值。
- 可观测证据：`tests/test_phase35_situation_runtime.py::test_tc_phase354_001_situation_context_has_no_memory_or_runtime_fields`。
- 验收映射：`ACPT-P3.5.4-01`。

#### F-P3.phase5.4-T01-02 SituationLoader 读取当前场景状态

- 输入：可选 `situation/situation_state.json`。
- 处理逻辑：读取 current_activity/environment/goal/interaction_mode/active_topics；缺失时使用默认 Julia Runtime 架构调试场景。
- 输出：`SituationSource`。
- 失败处理：文件缺失或 JSON 非法时返回默认状态。
- 可观测证据：`tests/test_phase35_situation_runtime.py::test_tc_phase354_002_situation_runtime_returns_current_building_context`。
- 验收映射：`ACPT-P3.5.4-02`。

#### F-P3.phase5.4-T01-03 Mode Switch 支持

- 输入：临时项目根目录中的 `situation_state.json`。
- 处理逻辑：根据 state 文件输出不同 SituationContext。
- 输出：不同 interaction_mode/goal/active_topics。
- 失败处理：不污染默认项目状态；测试使用临时目录。
- 可观测证据：`tests/test_phase35_situation_runtime.py::test_tc_phase354_003_situation_mode_switch_changes_context_without_provider_state`。
- 验收映射：`ACPT-P3.5.4-03`。

### 3) 接口与契约

新增文件：

```text
runtime/situation/situation_context.py
runtime/situation/situation_loader.py
runtime/situation/situation_runtime.py
runtime/situation/__init__.py
```

核心接口：

```python
@dataclass(frozen=True)
class SituationContext:
    current_activity: str
    environment: str
    goal: str
    interaction_mode: str
    active_topics: list[str]
```

禁止字段：

```text
memory_content
relationship_history
backend
provider
runtime
model
latency
tts
session_id
turn_id
emotion_score
```

### 4) 数据模型与状态变更

本阶段支持可选只读状态文件：

```text
situation/situation_state.json
```

如果文件不存在，SituationRuntime 返回默认状态。

### 5) 实现步骤

1. 新增 `runtime/situation/` 包。
2. 实现 `SituationContext` 与 `SituationSource`。
3. 实现 `SituationLoader.load()`。
4. 实现 `SituationRuntime.build_context()`。
5. 新增单测。
6. 运行单测。

### 6) 测试设计与命令

测试文件：

```text
tests/test_phase35_situation_runtime.py
```

命令：

```bash
python3 -m unittest tests.test_phase35_situation_runtime
```

预期：3 个测试全部通过。

### 7) 风险与回滚

风险：

- Situation 与 Relationship/Memory 边界混淆。

缓解：

- schema 不包含 memory content / relationship history。
- 单测显式禁止 provider/runtime/memory/relationship history 字段。

回滚：

- 删除 `runtime/situation/` 与 `tests/test_phase35_situation_runtime.py`。

### 8) 验收映射

- `ACPT-P3.5.4-01`: SituationContext 不含 memory/provider/runtime 字段。
- `ACPT-P3.5.4-02`: 默认 SituationContext 表达当前 Julia Cognitive Environment 架构建设场景。
- `ACPT-P3.5.4-03`: 显式 state 文件可切换当前 mode，且不引入 provider 状态。
