# FEATURE SPEC — P3.phase6.10.7.1 Context Execution Kernel

## Task `P3.phase6.10.7.1-T01` — Context Execution Kernel

### 1) 目标与边界
- 目标：实现 Julia Context OS 的最小 turn-level execution kernel，对齐 Claude `query.ts` 的核心语义：Pre Context → Provider → Post Context → Mutation → Trace。
- 目标：新增 `ContextTurn`、`ContextMutation`、`ExecutionTrace`、`PreTurnProcessor`、`PostTurnProcessor`、`ContextExecutionRuntime`。
- 非目标：不接真实 Provider Adapter，不做 Async Session Memory Worker，不做 Conflict Resolver，不创建长期 MemoryObject。

### 2) 子功能分解

#### F-P3.phase6.10.7.1-T01-01 ContextTurn Kernel
- 输入：session_id、user_input、ContextPlan、selected ContextBlocks。
- 处理逻辑：创建一次 cognitive turn 的稳定对象，记录 provider request、response、mutations、trace_id。
- 输出：`ContextTurn`。
- 失败处理：缺失 turn_id/session_id/user_input 抛出 `ValueError`。
- 可观测证据：`TC-361071-001`, `TC-361071-004`。

#### F-P3.phase6.10.7.1-T01-02 PreTurnProcessor
- 输入：user_input、cognitive_mode、candidate ContextBlocks。
- 处理逻辑：调用已有 Planner、Budget Manager、Quality Evaluator。
- 输出：ContextPlan、selected_blocks、ContextQuality、budget_trace、excluded_sources。
- 失败处理：预算排除由 Budget Manager 标记，不中断 turn。
- 可观测证据：`TC-361071-001`, `TC-361071-003`。

#### F-P3.phase6.10.7.1-T01-03 PostTurnProcessor Mutation
- 输入：ContextTurn 与 provider response。
- 处理逻辑：生成 working-context mutations，如 task progress、open loop、mode shift、evidence gap、quality warning。
- 输出：list[`ContextMutation`]。
- 失败处理：不写长期 MemoryObject；无 response 仍允许根据 quality 产生 evidence gap。
- 可观测证据：`TC-361071-002`, `TC-361071-005`。

#### F-P3.phase6.10.7.1-T01-04 ExecutionTrace
- 输入：turn、selected blocks、evidence refs、budget trace、quality、mutations、provider metadata。
- 处理逻辑：记录每轮“Julia 看见了什么、排除了什么、质量如何、产生什么 mutation”。
- 输出：`ExecutionTrace`，并挂回 `ContextTurn.trace_id`。
- 失败处理：provider_latency_ms < 0 抛出 `ValueError`。
- 可观测证据：`TC-361071-004`。

### 3) 接口与契约
- 新增包：`runtime/context_os/execution/`。
- 主入口：`ContextExecutionRuntime.run_turn(...) -> ContextTurn`。
- Provider 契约：`provider(user_input: str, context_blocks: list[ContextBlock]) -> str`。
- 幂等：同一 plan/block/provider 输出下，turn 结构稳定；id/timestamps 每次唯一。

### 4) 数据模型与状态变更
- 新增 `MutationType`：`current_arc_update/open_loop_created/open_loop_resolved/cognitive_mode_changed/task_progress_update/evidence_gap_found/quality_warning`。
- `ContextMutation` 是 working context mutation，不等价于 MemoryObject。
- `ExecutionTrace` 保留 budget/quality/evidence refs/excluded sources。

### 5) 实现步骤
1. 新增 `context_mutation.py`、`context_turn.py`、`execution_trace.py`。
2. 新增 `pre_turn_processor.py` 串联 Planner/Budget/Quality。
3. 新增 `post_turn_processor.py` 生成第一版 deterministic mutations。
4. 新增 `execution_runtime.py` 提供最小 turn lifecycle。
5. 编写 `tests/test_phase361071_context_execution_kernel.py`。
6. 执行单测与全量回归。

### 6) 测试设计与命令
- `TC-361071-001`：run_turn 在 provider 前重建 selected ContextBlocks。
- `TC-361071-002`：planning turn 后产生 task/open-loop mutations。
- `TC-361071-003`：runtime_trace 等 excluded block 不进入 provider context。
- `TC-361071-004`：trace 记录 blocks/evidence/budget/quality/mutations。
- `TC-361071-005`：高风险无证据 personal history turn 产生 evidence gap mutation。

必跑命令：
```bash
python3 -m unittest tests.test_phase361071_context_execution_kernel -v
python3 -m unittest discover -s tests
```

### 7) 风险与回滚
- 风险：PostTurnProcessor v1 规则过粗；缓解：仅生成 working mutation，不写 MemoryObject。
- 风险：Provider 仍是 callable 占位；缓解：本阶段验证 lifecycle，不迁移 provider 主链。
- 回滚：删除 `runtime/context_os/execution/`、export 与测试，不影响已有 Context OS 静态模块。

### 8) 验收映射
- `ACPT-361071-001`：一次 turn 可完整串起 pre/provider/post。
- `ACPT-361071-002`：post-turn 可生成 ContextMutation。
- `ACPT-361071-003`：execution trace 可审计上下文选择与排除。
- `ACPT-361071-004`：不直接写长期 MemoryObject。
