# FEATURE_SPEC_P3.phase6.3 — Memory Lifecycle Runtime

## Task `P3.phase6.3-T01` — Memory Evolution: reinforce / decay / merge / archive / retain

### 1) 目标与边界

目标：新增 Memory Lifecycle Runtime，对长期记忆执行强化、衰减、合并、归档和核心关系记忆保护，使 Memory Runtime 从保存/检索升级为可演化的认知记忆系统。

非目标：

- 不删除 memory；archive 仅标记归档。
- 不调用 LLM、embedding 或外部服务。
- 不改变现有 persistence/retrieval 文件格式。
- 不让 provider/backend/model/latency/tts/session_id 等 runtime metadata 参与 lifecycle decision。

### 2) 子功能分解

#### F-P3.phase6.3-T01-01 Lifecycle Decision 契约

- 输入：memory_id、action、reason、confidence。
- 处理逻辑：冻结 `MemoryLifecycleDecision`，action 限定 reinforce/merge/decay/archive/retain。
- 输出：可解释 lifecycle decision。
- 失败处理：未知 memory 不生成 action。
- 可观测证据：`tests/test_phase36_memory_lifecycle.py::test_tc_phase363_006_lifecycle_decision_explainability`。
- 验收映射：`ACPT-P3.6.3-01`。

#### F-P3.phase6.3-T01-02 Reinforcement

- 输入：MemoryObject + referenced_topics。
- 处理逻辑：重复出现的高价值 topic 增加 recurrence 与 dominant importance。
- 输出：action=reinforce + 更新后的 MemoryObject。
- 失败处理：无 topic hit 时 retain。
- 可观测证据：`tests/test_phase36_memory_lifecycle.py::test_tc_phase363_001_reinforcement_increases_recurrence_and_importance`。
- 验收映射：`ACPT-P3.6.3-02`。

#### F-P3.phase6.3-T01-03 Decay

- 输入：低 recurrence + 低平均 importance memory。
- 处理逻辑：降低 importance，但不删除。
- 输出：action=decay。
- 失败处理：protected relationship memory 不 decay。
- 可观测证据：`tests/test_phase36_memory_lifecycle.py::test_tc_phase363_002_decay_low_value_memory`。
- 验收映射：`ACPT-P3.6.3-03`。

#### F-P3.phase6.3-T01-04 Merge

- 输入：同组相关 milestone memories。
- 处理逻辑：MemoryMergePolicy 按 cognitive group key 合并，生成 consolidated milestone。
- 输出：action=merge，merged_memory_ids。
- 失败处理：不足两条不 merge。
- 可观测证据：`tests/test_phase36_memory_lifecycle.py::test_tc_phase363_003_merge_related_milestones`。
- 验收映射：`ACPT-P3.6.3-04`。

#### F-P3.phase6.3-T01-05 Archive

- 输入：obsolete / temporary / failed-test 等长期低价值 memory。
- 处理逻辑：action=archive；content 标记 archived=true。
- 输出：归档 memory，不进入默认高优先级认知路径。
- 失败处理：relationship protected memory 不 archive。
- 可观测证据：`tests/test_phase36_memory_lifecycle.py::test_tc_phase363_004_archive_obsolete_low_value_memory`。
- 验收映射：`ACPT-P3.6.3-05`。

#### F-P3.phase6.3-T01-06 Relationship Core Protection

- 输入：relationship memory。
- 处理逻辑：当 relationship importance 高且涉及 identity continuity / created Julia / independent existence 时 action=retain。
- 输出：protected retain decision。
- 失败处理：普通 relationship event 仍走正常 lifecycle。
- 可观测证据：`tests/test_phase36_memory_lifecycle.py::test_tc_phase363_005_relationship_core_memory_protected`。
- 验收映射：`ACPT-P3.6.3-06`。

### 3) 接口与契约

新增：

```text
runtime/memory/lifecycle/lifecycle_decision.py
runtime/memory/lifecycle/reinforcement.py
runtime/memory/lifecycle/decay.py
runtime/memory/lifecycle/archive.py
runtime/memory/lifecycle/merge_policy.py
runtime/memory/lifecycle/lifecycle_manager.py
runtime/memory/lifecycle/__init__.py
```

升级：

```text
runtime/memory/memory_runtime.py
```

### 4) 数据模型与状态变更

```python
@dataclass(frozen=True)
class MemoryLifecycleDecision:
    action: str
    memory_id: str
    reason: str
    confidence: float
    metadata: dict[str, object]
```

MemoryRuntime facade：

```python
evaluate_lifecycle(referenced_topics=None)
apply_lifecycle(referenced_topics=None)
```

### 5) 实现步骤

1. 新增 lifecycle decision DTO。
2. 新增 reinforcer/decay/archiver/merge policy。
3. 新增 MemoryLifecycleManager evaluate/apply。
4. MemoryRuntime 接入 lifecycle facade。
5. 新增 Phase 3.6.3 单元测试并全量回归。

### 6) 测试设计与命令

```bash
python3 -m unittest tests.test_phase36_memory_lifecycle
python3 -m unittest discover -s tests
```

预期：全部 OK。

### 7) 风险与回滚

风险：

- merge key 过宽误合并。
- archive 策略误归档仍有价值记忆。
- protection 规则过宽导致 relationship memory 永不演化。

缓解：

- merge 限定同 memory type + Julia Runtime cognitive milestone group。
- archive 不删除，仅标记。
- protection 只保护 relationship core，不保护全部 relationship event。

回滚：

- 删除 `runtime/memory/lifecycle/`。
- `MemoryRuntime` 移除 lifecycle facade。
- 移除 `tests/test_phase36_memory_lifecycle.py`。

### 8) 验收映射

- `ACPT-P3.6.3-01` LifecycleDecision explainable。
- `ACPT-P3.6.3-02` Reinforcement 提升 recurrence/importance。
- `ACPT-P3.6.3-03` Decay 降低低价值 memory importance。
- `ACPT-P3.6.3-04` Merge 形成 consolidated milestone。
- `ACPT-P3.6.3-05` Archive 标记 obsolete low-value memory。
- `ACPT-P3.6.3-06` Core relationship memory protected。
