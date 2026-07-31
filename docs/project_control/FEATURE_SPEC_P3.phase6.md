# FEATURE_SPEC_P3.phase6 — Reflection & Autonomous Memory Consolidation Runtime

## Task `P3.phase6-T01` — Experience → Reflection → MemoryCandidate

### 1) 目标与边界

目标：新增 Reflection Runtime 第一版，将 ConversationContinuityContext / JuliaContext v4 / recent turns 中的连续经历转化为经过重要性评估和策略门控的 MemoryCandidate，作为后续 Memory Runtime 持久化输入。

非目标：

- 第一版不调用 LLM、embedding 或外部 API。
- 第一版不直接写入长期 memory 文件，先输出候选并提供 `to_memory_object()` 转换契约。
- 不做普通聊天 summary。
- 不携带 provider/backend/model/latency/tts/session_id 等 RuntimeEnvelope 信息。

### 2) 子功能分解

#### F-P3.phase6-T01-01 ReflectionInput 契约

- 输入：conversation_arc、recent_turns、active_topics、open_loops、situation_context。
- 处理逻辑：冻结 provider-independent experience slice。
- 输出：`ReflectionInput`。
- 失败处理：空 turns 输出空候选。
- 可观测证据：`tests/test_phase36_reflection_runtime.py::test_tc_phase36_001_milestone_detection_consolidates_trajectory`。
- 验收映射：`ACPT-P3.6-01`。

#### F-P3.phase6-T01-02 MemoryCandidate 契约

- 输入：memory_type、summary、reason、importance、confidence、topics、source。
- 处理逻辑：候选先于 MemoryObject；提供 `total_importance()` 与 `to_memory_object()`。
- 输出：`MemoryCandidate` / `MemoryObject`。
- 失败处理：memory_type 通过 MemoryRuntime normalizer 兜底。
- 可观测证据：`tests/test_phase36_reflection_runtime.py::test_tc_phase36_004_importance_gate_rejects_low_confidence_candidate`。
- 验收映射：`ACPT-P3.6-02`。

#### F-P3.phase6-T01-03 EventExtractor

- 输入：recent ConversationTurn trajectory + active topics + arc。
- 处理逻辑：识别 milestone / decision / relationship / noise event；第一版 rule+metadata，不调用模型。
- 输出：event dict 列表。
- 失败处理：未知低价值文本进入 noise，不产生长期候选。
- 可观测证据：`tests/test_phase36_reflection_runtime.py::{test_tc_phase36_001_milestone_detection_consolidates_trajectory,test_tc_phase36_002_noise_filtering_discards_low_value_turns}`。
- 验收映射：`ACPT-P3.6-03`。

#### F-P3.phase6-T01-04 ImportanceEvaluator

- 输入：event dict。
- 处理逻辑：根据事件类型生成带 reason/importance/confidence 的 MemoryCandidate。
- 输出：MemoryCandidate 或 None。
- 失败处理：noise 返回 None。
- 可观测证据：`tests/test_phase36_reflection_runtime.py::test_tc_phase36_001_milestone_detection_consolidates_trajectory`。
- 验收映射：`ACPT-P3.6-04`。

#### F-P3.phase6-T01-05 ConsolidationPolicy Gate + Merge

- 输入：MemoryCandidate 列表。
- 处理逻辑：`confidence >= 0.7` 且平均 importance 达标才保留；同主题候选合并。
- 输出：filtered + merged candidates。
- 失败处理：低置信/低价值/空 summary 丢弃。
- 可观测证据：`tests/test_phase36_reflection_runtime.py::{test_tc_phase36_003_memory_merge_combines_related_runtime_journey,test_tc_phase36_004_importance_gate_rejects_low_confidence_candidate}`。
- 验收映射：`ACPT-P3.6-05`。

#### F-P3.phase6-T01-06 Runtime Isolation

- 输入：可能带 runtime metadata 的 ConversationTurn。
- 处理逻辑：ConversationTurn 清理 runtime metadata；MemoryCandidate 不输出 provider/backend/model/latency/tts/session_id。
- 输出：cognitive-only reflection candidate。
- 失败处理：污染字段不进入 candidate。
- 可观测证据：`tests/test_phase36_reflection_runtime.py::test_tc_phase36_005_runtime_isolation_in_memory_candidate`。
- 验收映射：`ACPT-P3.6-06`。

### 3) 接口与契约

新增/升级：

```text
runtime/reflection/reflection_input.py
runtime/reflection/memory_candidate.py
runtime/reflection/event_extractor.py
runtime/reflection/importance_evaluator.py
runtime/reflection/reflection_policy.py
runtime/reflection/reflection_engine.py
runtime/reflection/__init__.py
```

保留兼容：

```text
runtime/reflection/analyzer.py
```

### 4) 数据模型与状态变更

```python
@dataclass(frozen=True)
class ReflectionInput:
    conversation_arc: str
    recent_turns: list[ConversationTurn]
    active_topics: list[str]
    open_loops: list[dict[str, object]]
    situation_context: SituationContext

@dataclass(frozen=True)
class MemoryCandidate:
    memory_type: str
    summary: str
    reason: str
    importance: dict[str, float]
    confidence: float
    topics: list[str]
    source: str
```

### 5) 实现步骤

1. 新增 ReflectionInput / MemoryCandidate。
2. 新增 deterministic EventExtractor。
3. 新增 ImportanceEvaluator。
4. 新增 ConsolidationPolicy gate + merge。
5. 新增 ReflectionEngine 管线。
6. 新增 Phase 3.6 单元测试并全量回归。

### 6) 测试设计与命令

```bash
python3 -m unittest tests.test_phase36_reflection_runtime
python3 -m unittest discover -s tests
```

预期：全部 OK。

### 7) 风险与回滚

风险：

- rule extractor 第一版覆盖有限。
- 若直接写入 memory，可能造成污染；因此第一版只输出 candidate。
- 后续 LLM-assisted reflection 可能引入 provider 差异。

缓解：

- Gate + merge 先于持久化。
- Runtime isolation 测试防止 trace metadata 进入 memory。
- 后续可在 Phase 3.6.x 增加 Hybrid Reflection，但保持 MemoryCandidate 契约不变。

回滚：

- 删除新增 `runtime/reflection/{reflection_input,memory_candidate,event_extractor,importance_evaluator,reflection_policy,reflection_engine}.py`。
- `runtime/reflection/__init__.py` 回退只导出 `ReflectionAnalyzer/ReflectionInsight`。
- 移除 `tests/test_phase36_reflection_runtime.py`。

### 8) 验收映射

- `ACPT-P3.6-01` ReflectionInput provider-independent。
- `ACPT-P3.6-02` MemoryCandidate 先于 MemoryObject。
- `ACPT-P3.6-03` Milestone/noise event extraction 成立。
- `ACPT-P3.6-04` ImportanceEvaluator 生成 reason + importance + confidence。
- `ACPT-P3.6-05` Gate + merge 防止 memory 污染。
- `ACPT-P3.6-06` Reflection candidate 无 runtime leakage。
