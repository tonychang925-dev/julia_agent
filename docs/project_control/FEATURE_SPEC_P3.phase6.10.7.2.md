# FEATURE SPEC — P3.phase6.10.7.2 Context Projection Runtime

## Task `P3.phase6.10.7.2-T01` — Context Projection Runtime

### 1) 目标与边界
- 目标：将 `candidate_blocks` 占位升级为 authority-aware cognitive world projection。
- 目标：在 PreTurn 阶段自动投影 identity、relationship、task、compact、session restore、recent tail、semantic evidence。
- 目标：输出 explainable projection trace，说明 included blocks、source refs、evidence refs。
- 非目标：不实现 Conflict Resolver，不实现 Session/Task State 持久化，不迁移真实 Provider 主链。

### 2) 子功能分解

#### F-P3.phase6.10.7.2-T01-01 ProjectionBlock Contract
- 输入：projection source content、source_refs、authority、priority。
- 处理逻辑：封装为 `ContextProjectionBlock`，再转换为 `ContextBlock`。
- 输出：Budget/Quality 可消费的 ContextBlock。
- 失败处理：缺失 block_id/block_type 或 authority 越界抛出 `ValueError`。
- 可观测证据：`TC-361072-001`, `TC-361072-005`。

#### F-P3.phase6.10.7.2-T01-02 Core Cognitive Projection
- 输入：identity、relationship、current_task、compact state、recent records。
- 处理逻辑：分别生成 core_identity、relationship_anchor、active_task、compact_state、recent_turns。
- 输出：ContextProjectionResult.blocks。
- 失败处理：缺失 source 时跳过，不编造。
- 可观测证据：`TC-361072-001`, `TC-361072-002`, `TC-361072-005`。

#### F-P3.phase6.10.7.2-T01-03 Semantic Evidence Projection
- 输入：ContextPlan.evidence_intents 与 SemanticEvidenceIntegration。
- 处理逻辑：调用 evidence integration，保留 authority/provenance/source refs，并过滤 assistant-generated claims。
- 输出：semantic_evidence ContextBlock。
- 失败处理：无证据时由 integration 输出 no-invention guard。
- 可观测证据：`TC-361072-003`。

#### F-P3.phase6.10.7.2-T01-04 PreTurn Integration
- 输入：ProjectionInputs + optional candidate_blocks。
- 处理逻辑：PreTurnProcessor 先 plan，再 project，再 budget/quality。
- 输出：selected_blocks + budget_trace.context_projection。
- 失败处理：budget 不足时按 required/priority 裁剪。
- 可观测证据：`TC-361072-004`。

### 3) 接口与契约
- 新增包：`runtime/context_os/projection/`。
- 主入口：`ContextProjector.project(plan, inputs) -> ContextProjectionResult`。
- 新增：`ContextProjectionInputs`，承载 identity/relationship/current_task/compacts/session_snapshot/recent_records/semantic_evidence/extra_blocks。
- `ContextExecutionRuntime.run_turn(..., projection_inputs=...)` 接入 projection。

### 4) 数据模型与状态变更
- 新增 `ContextProjectionBlock`，它不是持久 Memory，而是 model-facing context projection。
- `ContextProjectionResult.trace` 记录 included/source_refs/evidence_refs/reason。
- 不新增持久化。

### 5) 实现步骤
1. 新增 projection package 与各 projection adapters。
2. 接入 `PreTurnProcessor.projection_inputs`。
3. 接入 `ContextExecutionRuntime.run_turn(projection_inputs=...)`。
4. 编写 projection behavior tests。
5. 执行单测与全量回归。

### 6) 测试设计与命令
- `TC-361072-001`：Identity/Relationship 在身份问题中必定投影。
- `TC-361072-002`：技术问题不强制引入无关个人故事。
- `TC-361072-003`：Tony source evidence 压过 Julia 历史 hallucination。
- `TC-361072-004`：预算紧张时保留 required identity/relationship。
- `TC-361072-005`：projection trace 可解释 included/source/evidence。

必跑命令：
```bash
python3 -m unittest tests.test_phase361072_context_projection_runtime -v
python3 -m unittest discover -s tests
```

### 7) 风险与回滚
- 风险：Projection 规则 v1 仍较粗；缓解：只产出 ContextBlock，不写 MemoryObject。
- 风险：Session/Task State 仍未独立持久化；缓解：本阶段只提供 projection adapter，后续 3.6.10.9 实现 state runtime。
- 回滚：删除 `runtime/context_os/projection/`、PreTurn/ExecutionRuntime projection_inputs 参数与测试。

### 8) 验收映射
- `ACPT-361072-001`：ContextProjection 能生成核心认知世界投影。
- `ACPT-361072-002`：Projection 结果可进入 Budget/Quality/Provider 链路。
- `ACPT-361072-003`：Evidence Projection 保持 authority/provenance 优先。
- `ACPT-361072-004`：Projection Trace 可解释 Julia 为什么看到这些信息。
