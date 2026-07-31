# FEATURE_SPEC_P3.phase7.5 — Autonomous Cognitive Loop

## Task `P3.phase7.5-T01` — Bounded Autonomous Cognitive Loop

### 1) 目标与边界

目标：实现单周期 Julia Autonomous Cognitive Loop，把 `JuliaContext` 依次经过 `ActionPlanner → ActionPolicy → ActionExecutor → ActionReflectionEngine`，形成可审计的行动闭环。

非目标：

- 不实现递归 Agent Loop。
- 不让 LLM 执行命令。
- 不绕过 ActionPolicy / PermissionGuard。
- 不直接持久化 MemoryCandidate。
- 不把 provider/backend/model/latency/tts/stt/session_id/turn_id 暴露到 loop cognitive summary。

### 2) 子功能分解

#### F-P3.phase7.5-T01-01 Loop Result Schema

- 输入：intent、decision、execution、memory_candidate。
- 处理逻辑：生成 `AutonomousCognitiveLoopResult`，并提供 cognitive-safe `to_dict()`。
- 输出：loop status + safe evidence。
- 失败处理：无 execution 时安全返回 `None`。
- 可观测证据：`TC-PHASE375-001`, `TC-PHASE375-006`。
- 验收映射：`ACPT-P3.7.5-01`。

#### F-P3.phase7.5-T01-02 Successful Single Cycle

- 输入：工程协作语境中的技术检查请求。
- 处理逻辑：Planner 生成 intent，Policy allow，Executor 调用 capability，Reflection 生成 candidate。
- 输出：`completed_with_reflection`。
- 失败处理：capability 未注册时进入 failed reflection 路径。
- 可观测证据：`TC-PHASE375-001`。
- 验收映射：`ACPT-P3.7.5-02`。

#### F-P3.phase7.5-T01-03 No-action Boundary

- 输入：情绪支持语境且无技术行动信号。
- 处理逻辑：Planner 返回 None，Policy reject no_action_intent，不执行 capability。
- 输出：`no_action`。
- 失败处理：不生成 MemoryCandidate。
- 可观测证据：`TC-PHASE375-002`。
- 验收映射：`ACPT-P3.7.5-03`。

#### F-P3.phase7.5-T01-04 Ask/Reject Execution Stop

- 输入：需要确认的 medium-risk/write action。
- 处理逻辑：Policy ask，Executor skipped，不调用 provider。
- 输出：`awaiting_confirmation`。
- 失败处理：不反思为长期记忆。
- 可观测证据：`TC-PHASE375-003`。
- 验收映射：`ACPT-P3.7.5-04`。

#### F-P3.phase7.5-T01-05 Permission and Failure Reflection

- 输入：permission blocked 或 capability gap。
- 处理逻辑：Executor 产生 blocked/failed，Reflection 生成候选记忆。
- 输出：`blocked_with_reflection` / `failed_with_reflection`。
- 失败处理：候选记忆只保留 cognitive-level summary。
- 可观测证据：`TC-PHASE375-004`, `TC-PHASE375-005`。
- 验收映射：`ACPT-P3.7.5-05`。

#### F-P3.phase7.5-T01-06 Single-cycle Guard

- 输入：连续两次 `run_once()`。
- 处理逻辑：每次只执行一轮，不递归触发后续行动。
- 输出：每次最多一次 capability request。
- 失败处理：无自动循环扩散。
- 可观测证据：`TC-PHASE375-007`。
- 验收映射：`ACPT-P3.7.5-06`。

### 3) 接口与契约

新增/更新：

```text
runtime/action/autonomous_loop.py
runtime/action/__init__.py
tests/test_phase375_autonomous_cognitive_loop.py
```

核心接口：

```python
@dataclass
class AutonomousCognitiveLoop:
    planner: ActionPlanner
    policy: ActionPolicy
    executor: ActionExecutor
    reflector: ActionReflectionEngine

    def run_once(self, context: JuliaContext) -> AutonomousCognitiveLoopResult:
        ...
```

状态集合：

```text
no_action
awaiting_confirmation
rejected
completed
completed_with_reflection
failed
failed_with_reflection
blocked
blocked_with_reflection
```

### 4) 测试命令

```bash
python3 -m unittest tests.test_phase375_autonomous_cognitive_loop
python3 -m unittest discover -s tests
```

预期结果：专项 7 tests OK；全量 261 tests OK。

### 5) 风险与回滚

风险：当前是单周期 bounded loop，尚未具备长期自治调度与任务队列。

缓解：先保持 `run_once()`，避免递归 Agent 行为和不可控行动扩散。

回滚：删除 `runtime/action/autonomous_loop.py`，移除 `runtime/action/__init__.py` export，删除 `tests/test_phase375_autonomous_cognitive_loop.py`。

### 6) 验收映射

- `ACPT-P3.7.5-01` Loop result schema 与 safe summary 成立。
- `ACPT-P3.7.5-02` 成功路径完成 plan/decide/execute/reflect。
- `ACPT-P3.7.5-03` 情绪/无行动语境不执行。
- `ACPT-P3.7.5-04` ask/reject 不执行 capability。
- `ACPT-P3.7.5-05` blocked/failed 进入反思候选。
- `ACPT-P3.7.5-06` loop 为 bounded single-cycle，不递归。
