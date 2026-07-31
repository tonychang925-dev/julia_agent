# FEATURE SPEC — P3.phase6.10.7.3 Context Mutation & State Transition Runtime

## Task `P3.phase6.10.7.3-T01` — Context Mutation & State Transition Runtime

### 1) 目标与边界
- 目标：将 PostTurn event logging 升级为 Runtime-authorized Context State Transition。
- 目标：新增 Current Arc、Open Loop、Task Progress、Cognitive Mode、Evidence Gap、Quality Warning 的 mutation detection/policy/apply 链路。
- 目标：保持 Runtime = Authority；LLM response 只能作为输入信号，不能直接修改 identity/relationship/persona 等 protected fields。
- 非目标：不写长期 MemoryObject，不做 Async Session Memory Worker，不做完整 Conflict Resolver。

### 2) 子功能分解

#### F-P3.phase6.10.7.3-T01-01 Mutation Event Contract
- 输入：turn_id、mutation_type、reason、evidence_refs、confidence。
- 处理逻辑：创建 `ContextMutationEvent`，作为状态转换候选。
- 输出：可审计 mutation event。
- 失败处理：缺失 event_id/source_turn_id/reason 或 confidence 越界抛出 `ValueError`。
- 可观测证据：`TC-361073-005`, `TC-361073-006`。

#### F-P3.phase6.10.7.3-T01-02 Trackers
- 输入：ContextTurn user_input/response/quality/plan。
- 处理逻辑：ArcTracker、OpenLoopTracker、TaskProgressTracker 产生候选事件。
- 输出：current_arc/task/open_loop/mode/evidence_gap events。
- 失败处理：无法识别时不产生事件，不编造状态。
- 可观测证据：`TC-361073-001` 至 `TC-361073-004`。

#### F-P3.phase6.10.7.3-T01-03 Mutation Policy
- 输入：ContextWorkingState 与 ContextMutationEvent。
- 处理逻辑：执行 confidence threshold 与 protected_fields 拒绝策略。
- 输出：`MutationDecision(accepted/reason/state_changes)`。
- 失败处理：protected identity/relationship/persona 修改被拒绝。
- 可观测证据：`TC-361073-005`。

#### F-P3.phase6.10.7.3-T01-04 State Transition
- 输入：accepted MutationDecision list。
- 处理逻辑：更新 current_arc/current_task/open_loops/cognitive_mode/evidence_gaps/quality_warnings。
- 输出：新的 `ContextWorkingState`。
- 失败处理：未接受决策不改变 state。
- 可观测证据：`TC-361073-001` 至 `TC-361073-006`。

### 3) 接口与契约
- 新增包：`runtime/context_os/mutation/`。
- 主入口：`ContextMutationRuntime.process_turn(state, turn) -> MutationRuntimeResult`。
- 可选接入：`ContextExecutionRuntime.run_turn(..., working_state=...)` 会在 turn metadata 写入 `mutation_state_transition`。
- `ContextMutationRuntime` 不写 MemoryObject。

### 4) 数据模型与状态变更
- 新增 `ContextWorkingState`：current_arc/current_task/cognitive_mode/open_loops/mode_transition_history/evidence_gaps/quality_warnings/protected_fields。
- 新增 `OpenLoopState`。
- 新增 `ContextMutationEvent`、`MutationDecision`、`MutationRuntimeResult`。

### 5) 实现步骤
1. 新增 mutation event/state/decision/policy schema。
2. 新增 arc/open-loop/task trackers。
3. 新增 state transition engine。
4. 新增 ContextMutationRuntime。
5. 可选接入 ExecutionRuntime working_state。
6. 编写 mutation state transition 单测。
7. 执行单测与全量回归。

### 6) 测试设计与命令
- `TC-361073-001`：Context OS 连续讨论后 current_arc 更新。
- `TC-361073-002`：下一步研究 Claude compact 创建 open loop。
- `TC-361073-003`：完成分析后 open loop resolved。
- `TC-361073-004`：engineering/emotional/engineering 记录 mode transition。
- `TC-361073-005`：protected identity mutation 被拒绝。
- `TC-361073-006`：ExecutionRuntime 在提供 working_state 时嵌入 state transition trace。

必跑命令：
```bash
python3 -m unittest tests.test_phase361073_context_mutation_state_transition -v
python3 -m unittest discover -s tests
```

### 7) 风险与回滚
- 风险：tracker v1 为 deterministic rule-based；缓解：仅更新 working state，不写长期 memory。
- 风险：ExecutionRuntime 接入 working_state 后 metadata 变大；缓解：仅在显式传入 working_state 时写入。
- 回滚：删除 `runtime/context_os/mutation/`、ExecutionRuntime working_state 参数与测试。

### 8) 验收映射
- `ACPT-361073-001`：每轮后可产生 ContextMutationEvent。
- `ACPT-361073-002`：MutationPolicy 拒绝 protected state 修改。
- `ACPT-361073-003`：StateTransition 更新 working context。
- `ACPT-361073-004`：ExecutionRuntime 可审计 previous_state/next_state。
