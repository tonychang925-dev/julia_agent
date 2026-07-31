# FEATURE_SPEC_P3.phase7.3 — Capability Invocation Lifecycle

## Task `P3.phase7.3-T01` — Governed ActionDecision to CapabilityRequest Lifecycle

### 1) 目标与边界

目标：将 ActionPolicy 允许的 ActionDecision 转换为 CapabilityRequest，经 CapabilityPermissionGuard 二次门禁后交给 CapabilityRouter，并生成 ToolReflection。

非目标：

- 不让 LLM 生成命令。
- 不绕过 ActionGovernance。
- 不执行 ask/reject 决策。
- 不把 provider/backend/model/tts/stt 写入 CapabilityRequest。

### 2) 子功能分解

#### F-P3.phase7.3-T01-01 ActionExecutionResult Schema

- 输入：intent、decision、request、permission、tool_result、reflection。
- 处理逻辑：记录执行生命周期证据。
- 输出：ActionExecutionResult。
- 失败处理：无 intent/decision 时 status=blocked。
- 可观测证据：`TC-PHASE373-006`。
- 验收映射：`ACPT-P3.7.3-01`。

#### F-P3.phase7.3-T01-02 Allow Path Invocation

- 输入：decision=allow 的 low-risk known capability。
- 处理逻辑：ActionIntent → CapabilityRequest → PermissionGuard → Router.invoke。
- 输出：status=executed。
- 失败处理：router 未注册 capability 时 status=failed。
- 可观测证据：`TC-PHASE373-001`, `TC-PHASE373-005`。
- 验收映射：`ACPT-P3.7.3-02`。

#### F-P3.phase7.3-T01-03 Ask/Reject Non-execution

- 输入：decision=ask/reject。
- 处理逻辑：不生成 CapabilityRequest，不调用 Router。
- 输出：ask -> skipped；reject -> blocked。
- 失败处理：保守不执行。
- 可观测证据：`TC-PHASE373-002`, `TC-PHASE373-003`。
- 验收映射：`ACPT-P3.7.3-03`。

#### F-P3.phase7.3-T01-04 Permission Defense-in-depth

- 输入：ActionPolicy allow 但 CapabilityRequest payload 含 destructive signal。
- 处理逻辑：CapabilityPermissionGuard 阻断。
- 输出：status=blocked + ToolReflection。
- 失败处理：不调用 provider。
- 可观测证据：`TC-PHASE373-004`。
- 验收映射：`ACPT-P3.7.3-04`。

#### F-P3.phase7.3-T01-05 Runtime Isolation

- 输入：ActionIntent/ActionDecision。
- 处理逻辑：CapabilityRequest 不包含 provider/backend/model/tts/stt。
- 输出：runtime-clean request。
- 失败处理：forbidden metadata 不进入 request。
- 可观测证据：`TC-PHASE373-007`。
- 验收映射：`ACPT-P3.7.3-05`。

### 3) 接口与契约

新增/更新：

```text
runtime/action/action_executor.py
runtime/action/__init__.py
```

Capability map v1:

```text
code_inspection -> claude_code_tool / handoff
diagnostics -> claude_code_tool / handoff
read_context -> claude_code_tool / handoff
planning -> planning_tool / create_plan
```

### 4) 测试命令

```bash
python3 -m unittest tests.test_phase373_capability_invocation_lifecycle
python3 -m unittest discover -s tests
```

### 5) 风险与回滚

风险：v1 capability map 保守且有限；planning_tool 尚未实现时会返回 failed。

回滚：恢复 `runtime/action/action_executor.py` 为 placeholder，删除 `tests/test_phase373_capability_invocation_lifecycle.py`。

### 6) 验收映射

- `ACPT-P3.7.3-01` ActionExecutionResult schema。
- `ACPT-P3.7.3-02` allow path invokes capability。
- `ACPT-P3.7.3-03` ask/reject never execute。
- `ACPT-P3.7.3-04` permission guard blocks destructive payload。
- `ACPT-P3.7.3-05` runtime isolation。
