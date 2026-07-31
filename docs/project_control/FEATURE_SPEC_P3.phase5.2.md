# FEATURE_SPEC_P3.phase5.2 — Relationship Runtime Implementation

## Task `P3.phase5.2-T01` — Relationship Runtime 基础层

### 1) 目标与边界

目标：新增独立 `runtime/relationship/` 模块，把 Julia 与 Tony 的关系身份、共享项目、交互偏好和当前模式编译成 `RelationshipContext`，为 JuliaContext v2 提供关系维度输入。

量化目标：

- 新增 `RelationshipContext` dataclass。
- 新增 `RelationshipLoader`，从现有 `identity/julia_identity.yaml`、`identity/conversation_contract.md` 与可选关系状态文件读取关系资料。
- 新增 `RelationshipStore`，提供只读/初始化默认关系状态能力。
- 新增 `RelationshipRuntime`，输出稳定 `RelationshipContext`。
- 新增纯 runtime 单测，不调用 DeepSeek，不改 PromptBuilder。

非目标：

- 不实现 Memory Runtime。
- 不实现 Situation Runtime。
- 不接入 ContextBuilder 或 PromptBuilder。
- 不推测 Tony 私人心理状态。
- 不加入本地关键词匹配。

### 2) 子功能分解

#### F-P3.phase5.2-T01-01 RelationshipContext 数据契约

- 输入：关系身份、阶段、共享项目、交互偏好、当前模式。
- 处理逻辑：用 frozen dataclass 固定模型可消费的关系上下文。
- 输出：`RelationshipContext`。
- 失败处理：缺失字段由 runtime 提供默认值。
- 可观测证据：`tests/test_phase35_relationship_runtime.py::test_tc_phase352_001_relationship_context_has_no_runtime_fields`。
- 验收映射：`ACPT-P3.5.2-01`。

#### F-P3.phase5.2-T01-02 RelationshipLoader 读取持久关系资料

- 输入：`project_root/identity` 与可选 `relationship/relationship_state.json`。
- 处理逻辑：读取 Tony 用户名、长期关系阶段、共享项目、偏好。
- 输出：`RelationshipSource`。
- 失败处理：缺失关系状态文件时使用默认共享项目与模式，不抛出异常。
- 可观测证据：`tests/test_phase35_relationship_runtime.py::test_tc_phase352_002_relationship_runtime_preserves_shared_projects`。
- 验收映射：`ACPT-P3.5.2-02`。

#### F-P3.phase5.2-T01-03 RelationshipRuntime 保持 provider 独立

- 输入：同一个项目根目录；不同 RuntimeEnvelope 不进入本模块。
- 处理逻辑：只从持久关系资料构造 `RelationshipContext`。
- 输出：在不同 provider 场景下相同的 `RelationshipContext`。
- 失败处理：忽略 runtime/provider 字段，因为接口不接收这些字段。
- 可观测证据：`tests/test_phase35_relationship_runtime.py::test_tc_phase352_003_relationship_context_is_provider_independent`。
- 验收映射：`ACPT-P3.5.2-03`。

### 3) 接口与契约

新增文件：

```text
runtime/relationship/relationship_context.py
runtime/relationship/relationship_loader.py
runtime/relationship/relationship_store.py
runtime/relationship/relationship_runtime.py
runtime/relationship/__init__.py
```

核心接口：

```python
@dataclass(frozen=True)
class RelationshipContext:
    user_name: str
    relationship_stage: str
    shared_projects: list[str]
    interaction_preferences: list[str]
    current_mode: str
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
Tony_loneliness
Tony_love
sadness_score
```

### 4) 数据模型与状态变更

本阶段新增可选状态文件支持，但不强制写入：

```text
relationship/relationship_state.json
```

如果文件不存在，RelationshipStore 返回默认状态。

### 5) 实现步骤

1. 新增 `runtime/relationship/` 包。
2. 实现 `RelationshipContext` 与 `RelationshipSource`。
3. 实现 `RelationshipStore.load_state()` 默认状态读取。
4. 实现 `RelationshipLoader.load()`。
5. 实现 `RelationshipRuntime.build_context()`。
6. 新增单测。
7. 运行单测。

### 6) 测试设计与命令

测试文件：

```text
tests/test_phase35_relationship_runtime.py
```

命令：

```bash
python3 -m unittest tests.test_phase35_relationship_runtime
```

预期：3 个测试全部通过。

### 7) 风险与回滚

风险：

- Relationship Runtime 被误用为情绪推断系统。

缓解：

- schema 不包含心理评分字段。
- 测试显式禁止 loneliness/love/sadness score 等字段。

回滚：

- 删除 `runtime/relationship/` 与 `tests/test_phase35_relationship_runtime.py`。

### 8) 验收映射

- `ACPT-P3.5.2-01`: RelationshipContext 不含 runtime/provider/心理评分字段。
- `ACPT-P3.5.2-02`: RelationshipRuntime 输出 Tony、Julia Runtime、AI Agent Architecture 等共享关系上下文。
- `ACPT-P3.5.2-03`: RelationshipContext 对 provider/backend 独立。
