# FEATURE SPEC — P3.phase6.10.5 Semantic Evidence Integration

## Task `P3.phase6.10.5-T01` — Semantic Evidence Integration for Context OS

### 1) 目标与边界
- 目标：将 `ContextPlan.evidence_intents` 转换为可进入 `ContextBudgetManager` 的 `semantic_evidence` ContextBlock。
- 目标：复用现有 `SemanticContextRetriever`，保留 evidence id、source ref、authority、ranker trace、provenance。
- 目标：当 `excluded_blocks` 包含 `assistant_generated_claims` 时，过滤 Julia/assistant 过去回答产生的低可信事实，避免错误回答污染 Context。
- 非目标：不重写 Evidence Store、不引入新 embedding 后端、不实现 Compact/Resurrection。

### 2) 子功能分解

#### F-P3.phase6.10.5-T01-01 证据意图到 ContextBlock 转换
- 输入：`ContextPlan(query, evidence_intents, required_blocks, excluded_blocks)`。
- 处理逻辑：调用 retriever，读取 `RankedEvidence`，格式化为 authority-ranked evidence prompt block。
- 输出：`ContextBlock(block_type="semantic_evidence")`，包含 `evidence_ids/source_refs/authority_score/metadata.sources`。
- 失败处理：无 evidence 时输出 no-invention guard block，authority=0。
- 可观测证据：`TC-36105-001`, `TC-36105-003`。

#### F-P3.phase6.10.5-T01-02 Assistant Generated Claim Filtering
- 输入：`ContextPlan.excluded_blocks=["assistant_generated_claims"]` 与混合 speaker evidence。
- 处理逻辑：根据 `speaker` 与 `provenance.origin/provenance_type/source` 过滤 assistant/model 生成内容。
- 输出：仅保留 Tony/governed/diary 等高可信 source evidence。
- 失败处理：过滤后为空时退回 no-invention guard block。
- 可观测证据：`TC-36105-002`。

#### F-P3.phase6.10.5-T01-03 Ranker Trace 与 Provenance 保真
- 输入：`RankedEvidence` 的 similarity、authority、importance、recency、final_score、reason 与 `EvidenceChunk.provenance`。
- 处理逻辑：逐项写入 block metadata，不压扁为无来源摘要。
- 输出：可审计 sources trace。
- 失败处理：缺失 source_path 时退回 session_id/id source ref。
- 可观测证据：`TC-36105-004`。

#### F-P3.phase6.10.5-T01-04 Budget Manager 兼容
- 输入：semantic evidence block + `ContextBudgetManager.allocate`。
- 处理逻辑：保持 block_type、priority、token_count 字段兼容预算分配。
- 输出：semantic evidence 可被纳入 Context OS allocation。
- 失败处理：预算不足由 Budget Manager 按既有规则 exclude/clip。
- 可观测证据：`TC-36105-005`。

### 3) 接口与契约
- 新增：`runtime/context_os/evidence/SemanticEvidenceIntegration`。
- 方法：`build_blocks(plan: ContextPlan, limit: int | None = None) -> list[ContextBlock]`。
- 约束：`project_root` 或 `retriever` 必须存在；`default_limit > 0`。
- 幂等：同一 retriever 结果与 plan 输入下输出稳定。
- 超时：本阶段不新增超时控制，沿用 retriever 调用路径。

### 4) 数据模型与状态变更
- 新增包：`runtime/context_os/evidence/`。
- 不新增持久化表，不修改 Memory/Evidence 存储。
- `ContextBlock.metadata.sources[]` 保存 evidence provenance 和 scorer trace。

### 5) 实现步骤
1. 新增 `SemanticEvidenceIntegration` adapter。
2. 实现 assistant-generated evidence filter。
3. 实现 empty evidence no-invention guard block。
4. 编写 `tests/test_phase36105_semantic_evidence_integration.py`。
5. 执行单测与全量回归。

### 6) 测试设计与命令
- `TC-36105-001`：小红书 personal_history plan 构造 grounded semantic_evidence block。
- `TC-36105-002`：assistant-generated claim 被排除。
- `TC-36105-003`：无 evidence 时返回 no-invention guard。
- `TC-36105-004`：metadata 保留 ranker trace/provenance。
- `TC-36105-005`：semantic evidence block 可进入 Budget Manager。

必跑命令：
```bash
python3 -m unittest tests.test_phase36105_semantic_evidence_integration -v
python3 -m unittest discover -s tests
```

### 7) 风险与回滚
- 风险：过滤规则过宽导致 Julia evidence 不足；缓解：只在 plan 显式 exclude assistant claims 时启用。
- 风险：retriever 返回低相关 evidence；缓解：metadata 暴露 score，后续 Context Quality 可判定风险。
- 回滚：删除 `runtime/context_os/evidence/` 与对应测试/feature artifacts，不影响现有主链路。

### 8) 验收映射
- `ACPT-36105-001`：planner evidence intents 可生成 ContextBlock。
- `ACPT-36105-002`：assistant-generated claims 不作为个人历史主证据。
- `ACPT-36105-003`：无证据时禁止编造。
- `ACPT-36105-004`：所有 evidence 可追溯 source/provenance/ranker trace。
- `ACPT-36105-005`：ContextBudgetManager 可消费 semantic_evidence block。
