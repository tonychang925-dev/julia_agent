# FEATURE_SPEC_P3.phase5.10 — Cognitive Mode Arbitration Runtime

## Task `P3.phase5.10-T01` — Runtime-owned Cognitive Mode Arbitration

### 1) 目标与边界

目标：将 Julia 当前交互模式从固定 session/provider 配置升级为 Runtime 可解释决策。Context Arbitration 根据显式意图、活动任务、会话连续性、关系上下文和历史偏好选择 Cognitive Mode，并注入 JuliaContext v3。

非目标：

- 不新增 TTS/STT 修复。
- 不新增本地私密模式关键词匹配。
- 不让 Provider/Backend/Session 配置拥有 Cognitive Mode。
- 不修改 Persona 身份；Mode 只影响表达策略。

### 2) 子功能分解

#### F-P3.phase5.10-T01-01 CognitiveMode 契约

- 输入：模式名称、表达风格、推理风格、交互目标、禁止漂移项。
- 处理逻辑：冻结稳定模式对象：engineering/debugging/emotional/learning/planning/private。
- 输出：`CognitiveMode`。
- 可观测证据：`tests/test_phase35_context_arbitration.py::test_tc_phase3510_001_explicit_user_intent_has_highest_priority`。
- 验收映射：`ACPT-P3.5.10-01`。

#### F-P3.phase5.10-T01-02 Explainable Arbitration Result

- 输入：`ArbitrationContext`。
- 处理逻辑：输出 mode/confidence/evidence/reason。
- 输出：`CognitiveModeContext` / `ArbitrationResult`。
- 可观测证据：`tests/test_phase35_context_arbitration.py::test_tc_phase3510_005_context_compiler_outputs_julia_context_v3`。
- 验收映射：`ACPT-P3.5.10-02`。

#### F-P3.phase5.10-T01-03 Priority Arbitration

- 输入：relationship/situation/conversation/recent_turns/user_intent。
- 处理逻辑：优先级为 Explicit User Intent > Active Task Situation > Conversation Continuity > Relationship Context > Default。
- 输出：稳定 CognitiveMode 决策。
- 可观测证据：`tests/test_phase35_context_arbitration.py::{test_tc_phase3510_001_explicit_user_intent_has_highest_priority,test_tc_phase3510_002_active_task_overrides_relationship_mode,test_tc_phase3510_003_conversation_continuity_overrides_relationship_fallback,test_tc_phase3510_004_relationship_context_is_fallback_not_persona_change}`。
- 验收映射：`ACPT-P3.5.10-03`。

#### F-P3.phase5.10-T01-04 JuliaContext v3

- 输入：Persona/Relationship/Memory/Situation/Conversation + arbitration result。
- 处理逻辑：ContextCompiler 先仲裁 mode，再生成对应 SituationContext，并输出 JuliaContext v3。
- 输出：包含 `cognitive_mode` 的 JuliaContext。
- 可观测证据：`tests/test_phase35_context_compiler.py`、`tests/test_phase35_context_validation.py`。
- 验收映射：`ACPT-P3.5.10-04`。

#### F-P3.phase5.10-T01-05 Cognitive Projection 使用 Mode

- 输入：JuliaContext v3。
- 处理逻辑：Projection 根据 `cognitive_mode` 选择模型视图表达策略，不让 provider/backend 泄漏。
- 输出：Provider-neutral CognitivePromptPackage。
- 可观测证据：`tests/test_phase35_cognitive_rendering.py`。
- 验收映射：`ACPT-P3.5.10-05`。

#### F-P3.phase5.10-T01-06 清理固定 private voice 路由

- 输入：CLI/Bridge session args。
- 处理逻辑：real_voice + deepseek 不再自动设为 private_voice_continuity；仅显式 override 作为调试/迁移入口进入 arbitration。
- 输出：session 配置不再拥有默认 Cognitive Mode。
- 可观测证据：`tests/test_phase33_cli.py::test_tc_phase3510_025_cli_real_voice_deepseek_does_not_default_fixed_relationship_mode`。
- 验收映射：`ACPT-P3.5.10-06`。

### 3) 接口与契约

新增：

```text
runtime/cognitive/arbitration/cognitive_mode.py
runtime/cognitive/arbitration/arbitration_context.py
runtime/cognitive/arbitration/arbitration_result.py
runtime/cognitive/arbitration/context_arbitrator.py
runtime/cognitive/arbitration/rules/*.py
```

升级：

```text
runtime/cognitive/context_compiler/julia_context.py
runtime/cognitive/context_compiler/context_compiler.py
runtime/cognitive/context_validation/validator.py
runtime/cognitive/rendering/projection.py
runtime/conversation_runtime/bridge/direct_llm_bridge.py
runtime/conversation_runtime/cli.py
```

### 4) 测试命令

```bash
python3 -m unittest tests.test_phase35_context_arbitration tests.test_phase35_context_compiler tests.test_phase35_context_validation tests.test_phase35_cognitive_rendering tests.test_phase33_cli tests.test_phase33_direct_llm_bridge
```

### 5) 回滚

- 删除 `runtime/cognitive/arbitration/`。
- 从 `JuliaContext` 移除 `cognitive_mode` 字段。
- ContextCompiler 回退到 v2 编译路径。
- Projection 回退到 situation/relationship 直接选择表达策略。
- CLI 可恢复旧 relationship-mode 默认逻辑，但该路径不符合 Phase 3.5.10 冻结原则。
