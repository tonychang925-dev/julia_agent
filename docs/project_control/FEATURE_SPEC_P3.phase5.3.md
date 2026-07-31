# FEATURE_SPEC_P3.phase5.3 — Memory Runtime Implementation

## Task `P3.phase5.3-T01` — Memory Runtime 基础层

### 1) 目标与边界

目标：新增独立 `runtime/memory/` 模块，将旧 JSONL 记忆兼容转换为 `MemoryObject`，并提供第一版 rule + metadata ranking 检索，为后续 JuliaContext v2 提供 MemoryContext。

量化目标：

- 新增 `MemoryObject` dataclass，支持 `episodic / semantic / relationship / working`。
- 新增 `MemoryStore` 读取旧 `memory/relationship_memory.jsonl`、`memory/episodic_memory.jsonl`、`memory/important_events.md`。
- 新增 `MemoryRanking`，使用 rule + metadata 排序，不使用 embedding。
- 新增 `MemoryRuntime.retrieve(query, limit)`。
- 新增纯 runtime 单测，不调用 DeepSeek，不改 PromptBuilder。

非目标：

- 不做 embedding/vector index。
- 不写入 memory consolidation。
- 不接入 ContextBuilder 或 PromptBuilder。
- 不修改旧 `runtime/memory_loader.py`。
- 不调模型和 TTS/STT。

### 2) 子功能分解

#### F-P3.phase5.3-T01-01 MemoryObject 数据契约

- 输入：旧 JSONL item 或新结构字段。
- 处理逻辑：规范化为 frozen dataclass，importance 使用 emotional/relationship/technical/recurrence 多维结构。
- 输出：`MemoryObject`。
- 失败处理：缺少字段时使用稳定 fallback；非法 type 降级为 `semantic`。
- 可观测证据：`tests/test_phase35_memory_runtime.py::test_tc_phase353_001_memory_object_has_typed_importance`。
- 验收映射：`ACPT-P3.5.3-01`。

#### F-P3.phase5.3-T01-02 MemoryStore 兼容加载旧记忆

- 输入：`memory/*.jsonl` 与 `important_events.md`。
- 处理逻辑：relationship JSONL 转 relationship/semantic，episodic JSONL 转 episodic，important events 转 episodic。
- 输出：`list[MemoryObject]`。
- 失败处理：缺失文件返回空列表；坏 JSON 行跳过。
- 可观测证据：`tests/test_phase35_memory_runtime.py::test_tc_phase353_002_memory_store_loads_existing_relationship_and_episodic_memory`。
- 验收映射：`ACPT-P3.5.3-02`。

#### F-P3.phase5.3-T01-03 Rule + metadata ranking 检索

- 输入：用户 query 与 memory objects。
- 处理逻辑：关键词覆盖 + 类型权重 + 多维 importance + recency 简单排序。
- 输出：top-k `MemoryObject`。
- 失败处理：空 query 退化为 importance 排序；无记忆返回空列表。
- 可观测证据：`tests/test_phase35_memory_runtime.py::test_tc_phase353_003_relationship_query_ranks_identity_continuity_first` 与 `test_tc_phase353_004_technical_query_prefers_semantic_memory`。
- 验收映射：`ACPT-P3.5.3-03`。

### 3) 接口与契约

新增文件：

```text
runtime/memory/memory_object.py
runtime/memory/memory_store.py
runtime/memory/memory_runtime.py
runtime/memory/ranking/rule_ranker.py
runtime/memory/retrieval/__init__.py
runtime/memory/consolidation/__init__.py
runtime/memory/__init__.py
```

核心接口：

```python
@dataclass(frozen=True)
class MemoryObject:
    id: str
    type: str
    summary: str
    content: dict[str, object]
    topics: list[str]
    importance: dict[str, float]
    timestamp: str
    source: str
```

```python
class MemoryRuntime:
    def retrieve(self, query: str, limit: int = 5) -> list[MemoryObject]: ...
```

### 4) 数据模型与状态变更

本阶段只读旧 memory 文件，不写入新持久文件。

### 5) 实现步骤

1. 新增 `runtime/memory/` 包。
2. 实现 `MemoryObject` 与 normalization helper。
3. 实现 `MemoryStore` 兼容旧 JSONL。
4. 实现 `RuleMemoryRanker`。
5. 实现 `MemoryRuntime.retrieve()`。
6. 新增单测。
7. 运行单测。

### 6) 测试设计与命令

测试文件：

```text
tests/test_phase35_memory_runtime.py
```

命令：

```bash
python3 -m unittest tests.test_phase35_memory_runtime
```

预期：4 个测试全部通过。

### 7) 风险与回滚

风险：

- 旧 memory 类型不完全等于新类型。

缓解：

- 兼容映射：`relationship/user_profile/shared_memory/relationship_contract/communication_preference -> relationship`，episodic 文件 -> episodic，其余 -> semantic。

回滚：

- 删除 `runtime/memory/` 与 `tests/test_phase35_memory_runtime.py`。

### 8) 验收映射

- `ACPT-P3.5.3-01`: MemoryObject 支持多维 importance。
- `ACPT-P3.5.3-02`: MemoryStore 能读取现有 relationship/episodic memory。
- `ACPT-P3.5.3-03`: Rule ranking 能区分关系问题和技术问题的优先记忆。
