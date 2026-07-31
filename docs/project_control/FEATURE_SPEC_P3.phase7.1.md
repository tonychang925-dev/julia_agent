# FEATURE_SPEC_P3.phase7.1 — Action Intent Layer

## Task `P3.phase7.1-T01` — Cognitive State to ActionIntent Boundary

### 1) 目标与边界

目标：新增 Action Intent Layer，使 JuliaContext 能生成可解释 ActionIntent，但不执行工具、不调用 Capability、不产生 shell/file/API 命令。

非目标：

- 不接 ClaudeCodeTool / shell / external API。
- 不执行任何 action。
- 不做 Action Governance allow/ask/reject。
- 不让 provider/backend/model/latency/tts/session_id 等 RuntimeEnvelope 信息进入 ActionIntent。

### 2) 子功能分解

#### F-P3.phase7.1-T01-01 ActionIntent Schema

- 输入：intent_type、goal、target、risk_level、required_capability、reason、confidence。
- 处理逻辑：冻结 cognitive action proposal schema。
- 输出：ActionIntent。
- 失败处理：无行动需求时返回 None。
- 可观测证据：`tests/test_phase37_action_intent.py::test_tc_phase371_001_technical_request_inspect_repository`。
- 验收映射：`ACPT-P3.7.1-01`。

#### F-P3.phase7.1-T01-02 ActionContext Schema

- 输入：SituationContext、CognitiveModeContext、ConversationContinuityContext、RelationshipContext、user_input。
- 处理逻辑：隔离 Julia-facing action planning context。
- 输出：ActionContext。
- 失败处理：缺失上下文由 ContextCompiler 兜底。
- 可观测证据：`tests/test_phase37_action_intent.py`。
- 验收映射：`ACPT-P3.7.1-02`。

#### F-P3.phase7.1-T01-03 ActionPlanner

- 输入：JuliaContext。
- 处理逻辑：deterministic/context-aware planning，输出 inspect_repository / diagnose_issue / create_plan / None。
- 输出：ActionIntent | None。
- 失败处理：emotional/private non-technical context 返回 None。
- 可观测证据：`tests/test_phase37_action_intent.py::{test_tc_phase371_001_technical_request_inspect_repository,test_tc_phase371_002_bug_report_diagnose_issue,test_tc_phase371_003_planning_request_create_plan,test_tc_phase371_004_emotional_conversation_no_action}`。
- 验收映射：`ACPT-P3.7.1-03`。

#### F-P3.phase7.1-T01-04 Runtime Isolation

- 输入：JuliaContext with RuntimeEnvelope。
- 处理逻辑：ActionIntent 只包含 cognitive proposal，不包含 provider/backend/model/latency/tts/session_id/turn_id。
- 输出：runtime-clean ActionIntent。
- 失败处理：forbidden metadata 不进入 schema。
- 可观测证据：`tests/test_phase37_action_intent.py::test_tc_phase371_005_runtime_isolation`。
- 验收映射：`ACPT-P3.7.1-04`。

#### F-P3.phase7.1-T01-05 Intent is not Command

- 输入：technical action request。
- 处理逻辑：ActionIntent 不包含 shell/file/API commands；命令生成留给 Capability Layer。
- 输出：intent only。
- 失败处理：命令 token 不允许出现。
- 可观测证据：`tests/test_phase37_action_intent.py::test_tc_phase371_006_action_intent_is_not_command`。
- 验收映射：`ACPT-P3.7.1-05`。

### 3) 接口与契约

新增：

```text
runtime/action/action_intent.py
runtime/action/action_context.py
runtime/action/action_planner.py
runtime/action/action_policy.py
runtime/action/action_decision.py
runtime/action/action_executor.py
runtime/action/action_reflection.py
runtime/action/__init__.py
```

### 4) 测试命令

```bash
python3 -m unittest tests.test_phase37_action_intent
python3 -m unittest discover -s tests
```

### 5) 风险与回滚

风险：intent planning 规则第一版覆盖有限；后续 Action Governance 未完成前不能执行 capability。

回滚：删除 `runtime/action/` 与 `tests/test_phase37_action_intent.py`。

### 6) 验收映射

- `ACPT-P3.7.1-01` ActionIntent schema 成立。
- `ACPT-P3.7.1-02` ActionContext schema 成立。
- `ACPT-P3.7.1-03` Planner 输出正确 intent/no_action。
- `ACPT-P3.7.1-04` Runtime metadata 隔离。
- `ACPT-P3.7.1-05` Intent 不等于执行命令。
