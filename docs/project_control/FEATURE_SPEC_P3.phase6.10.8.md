# FEATURE SPEC — P3.phase6.10.8 Context Conflict Resolver

## Task `P3.phase6.10.8-T01` — Context Conflict Resolver

### 1) 目标与边界
- 目标：在 PreTurn Projection 后、Budget 前执行 Context Conflict Resolution。
- 目标：实现 authority ordering：current user intent/fact > governed memory > Tony archive > diary > compact/reflection > assistant response/model inference。
- 目标：被拒绝的 conflict loser 不进入 model-facing context，并在 budget_trace 中保留 resolution trace。
- 非目标：不做自然语言事实蕴含判断，不写长期 MemoryObject，不替代 Evidence Ranker。

### 2) 子功能分解

#### F-P3.phase6.10.8-T01-01 Conflict Item Contract
- 输入：ContextBlock 或显式 ConflictItem。
- 处理逻辑：提取 claim/source_type/authority/speaker/provenance/topic。
- 输出：`ConflictItem`。
- 失败处理：缺失 item_id/claim 或 authority 越界抛出 `ValueError`。
- 可观测证据：`TC-36108-001`, `TC-36108-002`。

#### F-P3.phase6.10.8-T01-02 Authority Policy
- 输入：ConflictItem。
- 处理逻辑：按 Cognitive Ownership authority model 计算 priority。
- 输出：可排序 priority。
- 失败处理：未知来源使用中性 fallback，不提升为高权威。
- 可观测证据：`TC-36108-001`, `TC-36108-003`。

#### F-P3.phase6.10.8-T01-03 Conflict Resolution
- 输入：同 topic 的 ConflictItem group。
- 处理逻辑：选择 highest policy priority winner，标记 rejected losers。
- 输出：`ConflictResolution`。
- 失败处理：无冲突 group 不产出 resolution。
- 可观测证据：`TC-36108-002`, `TC-36108-005`。

#### F-P3.phase6.10.8-T01-04 PreTurn Integration
- 输入：Projection/candidate ContextBlocks。
- 处理逻辑：PreTurnProcessor 在 Budget 前调用 resolver；BudgetManager 尊重上游 included=False。
- 输出：selected_blocks 不含 rejected losers；budget_trace.conflict_resolutions 可审计。
- 失败处理：被 resolver 排除的 block 保持 exclusion_reason。
- 可观测证据：`TC-36108-004`。

### 3) 接口与契约
- 新增包：`runtime/context_os/conflict/`。
- 主入口：`ContextConflictResolver.resolve_blocks(blocks) -> (blocks, resolutions)`。
- `PreTurnProcessor` 自动接入。
- `BudgetManager` 尊重 upstream `block.included=False`。

### 4) 数据模型与状态变更
- 新增 `ConflictItem`。
- 新增 `ConflictResolution`。
- 新增 `ConflictPolicy`。
- 不新增持久化。

### 5) 实现步骤
1. 定义 conflict schema。
2. 实现 detector/policy/resolver。
3. 接入 PreTurnProcessor。
4. 修正 BudgetManager 保留上游排除状态。
5. 编写 conflict resolver tests。
6. 执行单测与全量回归。

### 6) 测试设计与命令
- `TC-36108-001`：current user intent beats governed memory。
- `TC-36108-002`：Tony archive/source fact beats assistant historical claim。
- `TC-36108-003`：governed memory > diary > assistant。
- `TC-36108-004`：PreTurn trace 记录 conflict resolution 且 loser 不进入 selected context。
- `TC-36108-005`：无关 topic 不制造冲突。

必跑命令：
```bash
python3 -m unittest tests.test_phase36108_context_conflict_resolver -v
python3 -m unittest discover -s tests
```

### 7) 风险与回滚
- 风险：topic grouping v1 依赖 metadata；缓解：未知 topic 不强行冲突。
- 风险：语义冲突识别尚未做 NLI；缓解：本阶段只处理显式 conflict_topic。
- 回滚：删除 `runtime/context_os/conflict/`、PreTurn conflict integration、Budget included guard 与测试。

### 8) 验收映射
- `ACPT-36108-001`：冲突 evidence 可按 authority policy 裁决。
- `ACPT-36108-002`：assistant historical claim 不覆盖 Tony/source truth。
- `ACPT-36108-003`：冲突裁决进入 Execution trace/budget_trace。
- `ACPT-36108-004`：Budget 不重新 include 被 resolver 排除的 block。
