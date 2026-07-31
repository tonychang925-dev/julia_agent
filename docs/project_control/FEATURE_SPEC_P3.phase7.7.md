# FEATURE_SPEC_P3.phase7.7 — Controlled Action Loop Activation

## Task `P3.phase7.7-T01` — CLI Explicit Action Loop Enablement

### 1) 目标与边界

目标：为 `julia-conversation` 增加显式 CLI 开关 `--enable-action-loop`，允许真实运行时按需开启 bounded autonomous action loop trace。

非目标：

- 不默认开启 autonomous action loop。
- 不绕过 `ActionPolicy` / `CapabilityPermissionGuard`。
- 不引入递归 Agent Loop。
- 不要求真实 provider 网络调用作为单元验收前提。
- 不把 provider/backend/model/latency/tts/stt/session_id/turn_id 写入 action loop trace。

### 2) 子功能分解

#### F-P3.phase7.7-T01-01 CLI Flag Exposure

- 输入：`python3 -m runtime.conversation_runtime.cli --help`。
- 处理逻辑：argparse 注册 `--enable-action-loop`。
- 输出：help 中显示开关。
- 失败处理：无该 flag 时测试失败。
- 可观测证据：`TC-PHASE377-001`。
- 验收映射：`ACPT-P3.7.7-01`。

#### F-P3.phase7.7-T01-02 Default Disabled

- 输入：未设置 `enable_action_loop` 的 CLI args。
- 处理逻辑：`make_bridge()` 构造 DirectLLMBridge 时保持 `action_loop_enabled=False`。
- 输出：默认不创建 action loop。
- 失败处理：避免非显式自治行动。
- 可观测证据：`TC-PHASE377-002`。
- 验收映射：`ACPT-P3.7.7-02`。

#### F-P3.phase7.7-T01-03 DeepSeek Activation

- 输入：`backend=deepseek` + `enable_action_loop=True`。
- 处理逻辑：DirectLLMBridge.deepseek 传入 action_loop_enabled，bridge 初始化 bounded loop。
- 输出：`action_loop_enabled=True` 且 `action_loop != None`。
- 失败处理：未注入 capability 时只进入 failed trace，不执行外部动作。
- 可观测证据：`TC-PHASE377-003`。
- 验收映射：`ACPT-P3.7.7-03`。

#### F-P3.phase7.7-T01-04 Direct Echo Activation

- 输入：`backend=direct-echo` + `enable_action_loop=True`。
- 处理逻辑：DirectLLMBridge.echo 支持同样 action loop 参数。
- 输出：测试/本地路径也可开启 loop。
- 失败处理：兼容旧调用默认值。
- 可观测证据：`TC-PHASE377-004`。
- 验收映射：`ACPT-P3.7.7-04`。

#### F-P3.phase7.7-T01-05 Trace Safety Under CLI Activation

- 输入：开启 action loop 的 CLI bridge + fake provider。
- 处理逻辑：运行真实 ConversationLoop，检查 metadata.action_loop_trace。
- 输出：trace enabled 且 cognitive-safe。
- 失败处理：forbidden runtime/provider 字段不得进入 trace。
- 可观测证据：`TC-PHASE377-005`。
- 验收映射：`ACPT-P3.7.7-05`。

### 3) 接口与契约

更新：

```text
runtime/conversation_runtime/cli.py
runtime/conversation_runtime/bridge/direct_llm_bridge.py
tests/test_phase377_controlled_action_loop_activation.py
```

CLI：

```bash
./julia-conversation --backend deepseek --enable-action-loop --trace ...
```

默认：

```text
action_loop_enabled=False
```

显式开启：

```text
action_loop_enabled=True
action_loop=AutonomousCognitiveLoop(...)
```

### 4) 测试命令

```bash
python3 -m unittest tests.test_phase377_controlled_action_loop_activation
python3 -m unittest discover -s tests
```

预期结果：专项 5 tests OK；全量 270 tests OK。

### 5) 风险与回滚

风险：用户显式开启后，如果 capability router 未注册能力，会产生 `failed_with_reflection` trace。

缓解：默认关闭；failed trace 是治理结果，不代表未授权执行。

回滚：删除 CLI flag 与 bridge factory 参数，恢复 `DirectLLMBridge.echo/deepseek` 原签名，删除测试文件。

### 6) 验收映射

- `ACPT-P3.7.7-01` CLI help 暴露 enable flag。
- `ACPT-P3.7.7-02` 默认关闭。
- `ACPT-P3.7.7-03` DeepSeek bridge 可显式开启。
- `ACPT-P3.7.7-04` direct-echo bridge 可显式开启。
- `ACPT-P3.7.7-05` CLI 激活 trace 保持 cognitive-safe。
