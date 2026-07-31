# FEATURE_SPEC_P3.phase7.6 — Action Loop Trace Integration

## Task `P3.phase7.6-T01` — DirectLLMBridge Action Loop Trace Metadata

### 1) 目标与边界

目标：将 Phase 3.7.5 的 `AutonomousCognitiveLoop` 以显式开关方式接入 `DirectLLMBridge` trace metadata，使真实对话 turn 可观测 action loop 状态。

非目标：

- 默认不启用 autonomous action execution。
- 不改变 LLM response generation 主路径。
- 不直接写入 MemoryObject。
- 不暴露 provider/backend/model/latency/tts/stt/session_id/turn_id 到 `action_loop_trace`。

### 2) 子功能分解

#### F-P3.phase7.6-T01-01 Default Disabled Trace

- 输入：未开启 `action_loop_enabled` 的 DirectLLMBridge。
- 处理逻辑：metadata 输出 `action_loop_trace={"enabled": false}`。
- 输出：可观测但不执行 action loop。
- 失败处理：默认关闭确保兼容。
- 可观测证据：`TC-PHASE376-001`。
- 验收映射：`ACPT-P3.7.6-01`。

#### F-P3.phase7.6-T01-02 Enabled Loop Trace

- 输入：`action_loop_enabled=True` 且注入 `AutonomousCognitiveLoop`。
- 处理逻辑：在 JuliaContext 编译后运行 `run_once()`，将 safe result 写入 metadata。
- 输出：`completed_with_reflection` 等状态。
- 失败处理：未配置 loop 时输出 unavailable。
- 可观测证据：`TC-PHASE376-002`。
- 验收映射：`ACPT-P3.7.6-02`。

#### F-P3.phase7.6-T01-03 No-action Trace

- 输入：情绪支持语境。
- 处理逻辑：Planner 返回 None，trace 标记 `no_action`，不调用 capability。
- 输出：execution=None。
- 失败处理：不生成候选记忆。
- 可观测证据：`TC-PHASE376-003`。
- 验收映射：`ACPT-P3.7.6-03`。

#### F-P3.phase7.6-T01-04 Cognitive-safe Trace

- 输入：真实 bridge metadata。
- 处理逻辑：只输出 loop safe summary，不输出原始 CapabilityRequest runtime payload。
- 输出：不含 provider/backend/model/latency/tts/stt/session_id/turn_id 的 trace。
- 失败处理：forbidden 字段不得进入 action_loop_trace。
- 可观测证据：`TC-PHASE376-004`。
- 验收映射：`ACPT-P3.7.6-04`。

### 3) 接口与契约

更新：

```text
runtime/conversation_runtime/bridge/direct_llm_bridge.py
tests/test_phase376_action_loop_trace_integration.py
```

新增 DirectLLMBridge 参数：

```python
action_loop_enabled: bool = False
action_loop: AutonomousCognitiveLoop | None = None
```

metadata 契约：

```text
action_loop_trace.enabled == False
# or
action_loop_trace.enabled == True
action_loop_trace.status in loop status set
```

### 4) 测试命令

```bash
python3 -m unittest tests.test_phase376_action_loop_trace_integration
python3 -m unittest discover -s tests
```

预期结果：专项 4 tests OK；全量 265 tests OK。

### 5) 风险与回滚

风险：启用 action loop 可能在未注册 capability 时产生 failed_with_reflection trace。

缓解：默认关闭；真实启用必须显式注入 loop/capability router。

回滚：移除 DirectLLMBridge 的 `action_loop_enabled/action_loop` 字段与 `_action_loop_trace()`，删除测试文件。

### 6) 验收映射

- `ACPT-P3.7.6-01` 默认关闭但可观测。
- `ACPT-P3.7.6-02` 启用后写入 completed loop trace。
- `ACPT-P3.7.6-03` no_action 不执行 capability。
- `ACPT-P3.7.6-04` action_loop_trace cognitive-safe。
