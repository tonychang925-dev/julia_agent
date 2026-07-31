# FEATURE SPEC — P3.phase6.10.4 Structured Compact Runtime

## Task `P3.phase6.10.4-T01` — Source-grounded ExperienceCompactState

### 1) 目标与边界

目标：把 ContextMessageRecord 范围提炼为结构化、可追溯的 `ExperienceCompactState`，保留 decisions/failures/open_loops/next_actions/source_record_ids/source_evidence_ids。

非目标：不调用 LLM summarizer、不替换 Conversation Archive、不接 auto compact 阈值、不修改 provider prompt。

### 2) 子功能分解

#### F-P3.phase6.10.4-T01-01 ExperienceCompactState schema
- 输入：session_id、period、source_record_ids、结构化字段。
- 处理：校验 compact_id/session_id/source_record_ids/confidence。
- 输出：不可变 compact object。
- 失败处理：无 source_record_ids 抛 ValueError。
- 可观测证据：schema_version/to_dict/to_context_block_text。
- 测试：TC-36104-001。

#### F-P3.phase6.10.4-T01-02 StructuredCompactEngine 提炼
- 输入：ContextMessageRecord[]。
- 处理：按 role/terms 提取 decisions、known_failures、open_loops、next_actions。
- 输出：ExperienceCompactState。
- 失败处理：空 session records 抛 ValueError。
- 可观测证据：decisions/failures/open_loops 字段。
- 测试：TC-36104-002。

#### F-P3.phase6.10.4-T01-03 Source Evidence Traceability
- 输入：records.source_refs。
- 处理：去重收集 source_evidence_ids，保留 source_record_ids。
- 输出：compact 可回溯源记录和 evidence。
- 失败处理：无 evidence_refs 时 source_evidence_ids 为空但 source_record_ids 不为空。
- 可观测证据：to_context_block_text 包含 source record ids。
- 测试：TC-36104-003。

#### F-P3.phase6.10.4-T01-04 Authority-aware Confidence
- 输入：user-grounded vs assistant-heavy records。
- 处理：confidence 基于 average authority + explicit_user_ratio。
- 输出：assistant-heavy compact confidence 更低。
- 失败处理：confidence clamp 到 0~1。
- 可观测证据：metadata assistant_record_count。
- 测试：TC-36104-004。

#### F-P3.phase6.10.4-T01-05 Compact Store
- 输入：ExperienceCompactState。
- 处理：按 compact_id 保存、按 session 查询。
- 输出：InMemoryCompactStore。
- 失败处理：不存在返回 None。
- 可观测证据：get/list_for_session。
- 测试：TC-36104-005。

### 3) 接口与契约

新增：

```text
runtime/context_os/compact/compact_schema.py
runtime/context_os/compact/compact_engine.py
runtime/context_os/compact/compact_store.py
```

核心 API：

```python
StructuredCompactEngine().compact(session_id=str, records=list[ContextMessageRecord]) -> ExperienceCompactState
```

### 4) 数据模型与状态变更

无持久化迁移。CompactStore 为内存实现，后续 Session Resurrection 再接文件存储。

### 5) 实现步骤

1. 新建 `runtime/context_os/compact` 包。
2. 定义 `CompactDecision`、`CompactFailure`、`ExperienceCompactState`。
3. 实现 deterministic `StructuredCompactEngine`。
4. 实现 `InMemoryCompactStore`。
5. 新增 structured compact 单元测试。
6. 跑单测和全量回归。

### 6) 测试设计与命令

```bash
python3 -m unittest tests.test_phase36104_structured_compact_runtime -v
python3 -m unittest discover -s tests
```

预期：5 个新增测试通过；全量 329 tests OK。

### 7) 风险与回滚

风险：规则提炼不够智能。缓解：本阶段冻结 schema/source trace，LLM summarizer 后续只能填同一 schema，不能改变 provenance。

回滚：删除 `runtime/context_os/compact` 与测试，不影响 planner/budget/quality。

### 8) 验收映射

- ACPT-36104-001：compact 输出 structured schema 且 source_record_ids 不为空。
- ACPT-36104-002：decisions/failures/open_loops/next_actions 被结构化保留。
- ACPT-36104-003：source_evidence_ids 可追溯。
- ACPT-36104-004：assistant-heavy compact confidence 低于 user-grounded compact。
- ACPT-36104-005：compact store 可保存和按 session 查询。
