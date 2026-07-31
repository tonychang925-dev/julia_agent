# FEATURE_SPEC_P3.phase6.1 — Memory Runtime Persistence Adapter

## Task `P3.phase6.1-T01` — MemoryCandidate 安全持久化到 Memory Runtime

### 1) 目标与边界

目标：将通过 Reflection + ConsolidationPolicy 筛选的 `MemoryCandidate` 转换为 `MemoryObject`，并由 Memory Runtime 的 persistence adapter 负责 create / merge / reject。

非目标：

- ReflectionEngine 不直接写 memory 文件。
- 不调用 LLM、embedding、外部数据库或网络服务。
- 不改变 retrieval/ranking 主逻辑。
- 不允许 provider/backend/model/latency/tts/session_id 等 runtime metadata 进入持久化 memory。

### 2) 子功能分解

#### F-P3.phase6.1-T01-01 Persistence Request/Result 契约

- 输入：MemoryCandidate、source_reflection_id、created_at。
- 处理逻辑：构造 `MemoryPersistenceRequest`；输出 create/merge/reject 结果。
- 输出：`MemoryPersistenceResult(stored, memory_id, action, reason)`。
- 失败处理：reject 返回 stored=false 与 reason，不写文件。
- 可观测证据：`tests/test_phase36_memory_persistence.py::test_tc_phase361_001_candidate_accepted_creates_memory_object`。
- 验收映射：`ACPT-P3.6.1-01`。

#### F-P3.phase6.1-T01-02 Candidate Gate

- 输入：MemoryCandidate。
- 处理逻辑：复用 ConsolidationPolicy；低 confidence / 低 importance / 空 summary 拒绝。
- 输出：reject 或继续转换。
- 失败处理：不生成 JSONL 文件。
- 可观测证据：`tests/test_phase36_memory_persistence.py::test_tc_phase361_002_low_confidence_candidate_rejected`。
- 验收映射：`ACPT-P3.6.1-02`。

#### F-P3.phase6.1-T01-03 MemoryObject 转换与写入

- 输入：通过 gate 的 MemoryCandidate。
- 处理逻辑：生成 stable memory_id，规范化 type/importance，写入对应 JSONL 文件。
- 输出：MemoryObject persisted。
- 失败处理：type unknown 归一化为 semantic。
- 可观测证据：`tests/test_phase36_memory_persistence.py::{test_tc_phase361_001_candidate_accepted_creates_memory_object,test_tc_phase361_004_memory_type_preserved_for_relationship_candidate}`。
- 验收映射：`ACPT-P3.6.1-03`。

#### F-P3.phase6.1-T01-04 Duplicate Merge

- 输入：candidate + existing MemoryObject list。
- 处理逻辑：DuplicateDetector 按 memory_type + cognitive topic key 检测重复；MemoryWriter merge 替换原行。
- 输出：action=merge，文件仍保持单条 consolidated memory。
- 失败处理：未检测到 duplicate 时 create。
- 可观测证据：`tests/test_phase36_memory_persistence.py::test_tc_phase361_003_duplicate_candidate_merges_existing_memory`。
- 验收映射：`ACPT-P3.6.1-04`。

#### F-P3.phase6.1-T01-05 Runtime Isolation

- 输入：可能污染的 MemoryCandidate。
- 处理逻辑：检测 provider/backend/latency/tts/session_id 等执行元数据语义；污染则 reject。
- 输出：reject，不写入。
- 失败处理：reason 包含 runtime metadata。
- 可观测证据：`tests/test_phase36_memory_persistence.py::test_tc_phase361_005_runtime_leakage_rejected`。
- 验收映射：`ACPT-P3.6.1-05`。

#### F-P3.phase6.1-T01-06 MemoryRuntime facade

- 输入：MemoryPersistenceRequest。
- 处理逻辑：`MemoryRuntime.persist_candidate()` 委托 PersistenceAdapter；持久化后可被 retrieve 召回。
- 输出：MemoryPersistenceResult + retrievable MemoryObject。
- 失败处理：Adapter reject 透传。
- 可观测证据：`tests/test_phase36_memory_persistence.py::test_tc_phase361_006_memory_runtime_facade_persists_candidate`。
- 验收映射：`ACPT-P3.6.1-06`。

### 3) 接口与契约

新增：

```text
runtime/memory/persistence/memory_persistence_adapter.py
runtime/memory/persistence/persistence_adapter.py
runtime/memory/persistence/memory_writer.py
runtime/memory/persistence/memory_id_generator.py
runtime/memory/persistence/duplicate_detector.py
runtime/memory/persistence/__init__.py
```

升级：

```text
runtime/memory/memory_runtime.py
runtime/memory/memory_store.py
```

### 4) 数据模型与状态变更

```python
@dataclass(frozen=True)
class MemoryPersistenceRequest:
    candidate: MemoryCandidate
    source_reflection_id: str
    created_at: str

@dataclass(frozen=True)
class MemoryPersistenceResult:
    stored: bool
    memory_id: str | None
    action: str  # create / merge / reject
    reason: str
```

持久化文件：

```text
memory/relationship_memory.jsonl
memory/episodic_memory.jsonl
memory/semantic_memory.jsonl
memory/working_memory.jsonl
```

### 5) 实现步骤

1. 新增 persistence DTO。
2. 新增 MemoryIdGenerator / DuplicateDetector / MemoryWriter。
3. 新增 MemoryPersistenceAdapter。
4. MemoryRuntime 增加 `persist_candidate()` facade。
5. MemoryStore 兼容保留已持久化 id/topics，支持 merge 替换。
6. 新增 Phase 3.6.1 单元测试并全量回归。

### 6) 测试设计与命令

```bash
python3 -m unittest tests.test_phase36_memory_persistence
python3 -m unittest discover -s tests
```

预期：全部 OK。

### 7) 风险与回滚

风险：

- duplicate key 过宽导致误合并。
- runtime leakage 规则过宽误杀合法 cognitive topic。
- JSONL merge 写回失败可能导致文件覆盖风险。

缓解：

- 第一版 duplicate 限定 memory_type + cognitive topic key。
- runtime leakage 检测执行元数据语义，不误杀“model migration”类 cognitive topic。
- 单测覆盖 create/merge/reject/type/retrieve。

回滚：

- 删除 `runtime/memory/persistence/`。
- `MemoryRuntime` 移除 `persist_candidate()`。
- `MemoryStore` 可回退旧读取逻辑。
- 移除 `tests/test_phase36_memory_persistence.py`。

### 8) 验收映射

- `ACPT-P3.6.1-01` Persistence DTO 完成。
- `ACPT-P3.6.1-02` 低置信 candidate 被拒绝。
- `ACPT-P3.6.1-03` 高价值 candidate 可 create MemoryObject。
- `ACPT-P3.6.1-04` duplicate candidate 可 merge。
- `ACPT-P3.6.1-05` runtime metadata 污染被拒绝。
- `ACPT-P3.6.1-06` MemoryRuntime facade 可持久化并被 retrieve 召回。
