# FEATURE_SPEC_P3.phase6.2 — Memory Intelligence Upgrade

## Task `P3.phase6.2-T01` — Context-aware Cognitive Retrieval

### 1) 目标与边界

目标：将 Memory Runtime 从 query-only rule retrieval 升级为基于 JuliaContext 派生状态的 Cognitive Retrieval Layer，使记忆召回考虑 user input、active topics、current arc、cognitive mode、relationship stage，并提供可解释 ranking。

非目标：

- 不引入 embedding/vector database。
- 不调用 LLM。
- 不改变 Reflection/Persistence 写入链路。
- 不让 provider/backend/model/latency/tts/session_id 等 runtime metadata 进入 retrieval context。

### 2) 子功能分解

#### F-P3.phase6.2-T01-01 MemoryRetrievalContext / MemoryQuery

- 输入：user_input、active_topics、current_arc、cognitive_mode、relationship_stage。
- 处理逻辑：冻结 provider-independent retrieval context，并由 QueryBuilder 生成 topics/type priority。
- 输出：`MemoryRetrievalContext` / `MemoryQuery`。
- 失败处理：空 topics 使用 query text + mode priority 兜底。
- 可观测证据：`tests/test_phase36_memory_intelligence.py::test_tc_phase362_007_query_builder_excludes_runtime_metadata`。
- 验收映射：`ACPT-P3.6.2-01`。

#### F-P3.phase6.2-T01-02 Relevance Scoring

- 输入：MemoryQuery、MemoryObject、MemoryRetrievalContext。
- 处理逻辑：计算 topic_overlap、current_arc_match、user_intent_match。
- 输出：`RelevanceScore(score, components, reasons)`。
- 失败处理：无匹配时 relevance=0，但仍可被 importance 低权参与排序。
- 可观测证据：`tests/test_phase36_memory_intelligence.py::test_tc_phase362_006_memory_explainability`。
- 验收映射：`ACPT-P3.6.2-02`。

#### F-P3.phase6.2-T01-03 Importance / Relationship Weighting

- 输入：MemoryObject.importance + query priority + relationship_stage。
- 处理逻辑：ImportanceModel 将 emotional/relationship/technical/recurrence 加权；RelationshipWeight 增强长期关系相关 memory。
- 输出：importance_score / relationship_score。
- 失败处理：缺失 importance key 视为 0。
- 可观测证据：`tests/test_phase36_memory_intelligence.py::test_tc_phase362_001_relationship_recall_priority`。
- 验收映射：`ACPT-P3.6.2-03`。

#### F-P3.phase6.2-T01-04 CognitiveMemoryRanker

- 输入：MemoryRetrievalContext + MemoryObject list。
- 处理逻辑：final_score = relevance + importance*0.35 + relationship*0.25 + recurrence*0.15 + topic_overlap*0.25；输出 Top-K。
- 输出：ranked MemoryObject 或 RankedMemoryExplanation。
- 失败处理：limit<=0 返回空。
- 可观测证据：`tests/test_phase36_memory_intelligence.py::{test_tc_phase362_001_relationship_recall_priority,test_tc_phase362_002_technical_query_isolation,test_tc_phase362_003_conversation_aware_retrieval}`。
- 验收映射：`ACPT-P3.6.2-04`。

#### F-P3.phase6.2-T01-05 MemoryRuntime Facade

- 输入：MemoryRetrievalContext。
- 处理逻辑：`retrieve_for_context()` / `retrieve_with_explanations()` 从 MemoryStore 加载并使用 CognitiveMemoryRanker。
- 输出：Top-K memory / explanations。
- 失败处理：空 store 返回空。
- 可观测证据：`tests/test_phase36_memory_intelligence.py`。
- 验收映射：`ACPT-P3.6.2-05`。

#### F-P3.phase6.2-T01-06 Store Coverage + Noise Suppression

- 输入：relationship/episodic/semantic/working JSONL。
- 处理逻辑：MemoryStore 加载所有 typed memory files；低 importance noise 不进入 Top priority。
- 输出：完整候选集 + Top-K suppression。
- 失败处理：缺失文件忽略。
- 可观测证据：`tests/test_phase36_memory_intelligence.py::{test_tc_phase362_004_noise_suppression,test_tc_phase362_005_long_term_memory_reality}`。
- 验收映射：`ACPT-P3.6.2-06`。

### 3) 接口与契约

新增：

```text
runtime/memory/retrieval/retrieval_context.py
runtime/memory/retrieval/query_builder.py
runtime/memory/retrieval/relevance_scorer.py
runtime/memory/retrieval/memory_ranker.py
runtime/memory/weighting/importance_model.py
runtime/memory/weighting/relationship_weight.py
runtime/memory/weighting/__init__.py
```

升级：

```text
runtime/memory/retrieval/__init__.py
runtime/memory/memory_runtime.py
runtime/memory/memory_store.py
```

### 4) 数据模型与状态变更

```python
@dataclass(frozen=True)
class MemoryRetrievalContext:
    user_input: str
    active_topics: list[str]
    current_arc: str
    cognitive_mode: str
    relationship_stage: str

@dataclass(frozen=True)
class RankedMemoryExplanation:
    memory: MemoryObject
    score: float
    reason: list[str]
    components: dict[str, float]
```

### 5) 实现步骤

1. 新增 retrieval context/query builder。
2. 新增 relevance scorer 与 weighting models。
3. 新增 CognitiveMemoryRanker。
4. MemoryRuntime 增加 context-aware retrieve facade。
5. MemoryStore 加载 semantic/working JSONL。
6. 新增 Phase 3.6.2 单元测试并全量回归。

### 6) 测试设计与命令

```bash
python3 -m unittest tests.test_phase36_memory_intelligence
python3 -m unittest discover -s tests
```

预期：全部 OK。

### 7) 风险与回滚

风险：

- 公式权重可能需要后续调参。
- rule-based query builder 对复杂表达覆盖有限。
- relationship weight 过高会干扰技术查询。

缓解：

- TC-002 专门覆盖 technical isolation。
- `retrieve_with_explanations()` 输出 score components/reason 便于调参。
- 第一版不替换旧 `retrieve(query)`，只新增 context-aware facade。

回滚：

- 删除 `runtime/memory/weighting/` 与新增 retrieval 文件。
- `MemoryRuntime` 移除 `retrieve_for_context()` / `retrieve_with_explanations()`。
- `MemoryStore` 可回退 typed file 加载范围。

### 8) 验收映射

- `ACPT-P3.6.2-01` RetrievalContext 无 runtime metadata。
- `ACPT-P3.6.2-02` Relevance scoring 可解释。
- `ACPT-P3.6.2-03` relationship recall priority 成立。
- `ACPT-P3.6.2-04` technical query isolation 成立。
- `ACPT-P3.6.2-05` conversation-aware retrieval 成立。
- `ACPT-P3.6.2-06` noise suppression / long-term reality test 成立。
