# FEATURE_SPEC_P3.phase5.11 — Conversation Continuity Runtime

## Task `P3.phase5.11-T01` — 将离散 turn 编译为连续 Interaction Trajectory

### 1) 目标与边界

目标：新增 Conversation Continuity Runtime，将原始 conversation turns 转换为可进入 JuliaContext v4 的连续对话状态，使 Julia 能理解当前对话弧线、活跃话题、未关闭上下文与 session summary。

非目标：

- 不调用真实 LLM/Embedding/外部 API。
- 不修改 TTS/STT、Provider 调用协议或私密模式关键词规则。
- 不把 provider/backend/model/latency/session_id/turn_id 写入 ConversationContinuityContext。
- 不替代 Memory Runtime；Conversation Continuity 只覆盖分钟～session 级短期轨迹。

### 2) 子功能分解

#### F-P3.phase5.11-T01-01 ConversationTurn 事件契约

- 输入：turn_id、user_text、assistant_text、timestamp、topics、cognitive_mode、metadata。
- 处理逻辑：构造冻结的对话事件；`from_dict` 兼容旧 `{user,assistant}` turn；清理 runtime metadata。
- 输出：`ConversationTurn`。
- 失败处理：缺失字段使用空字符串/默认 turn_id；runtime metadata 被丢弃。
- 可观测证据：`tests/test_phase35_conversation_continuity.py::test_tc_phase3511_005_long_session_stability_caps_recent_turns_and_topics`。
- 验收映射：`ACPT-P3.5.11-01`。

#### F-P3.phase5.11-T01-02 ConversationContinuityContext 状态契约

- 输入：active_topics、open_loops、current_arc、recent_turns、session_summary。
- 处理逻辑：冻结 JuliaContext v4 所需的对话连续性视图。
- 输出：`ConversationContinuityContext` / `ConversationState`。
- 失败处理：空状态输出 `ongoing_conversation` 与 no established summary。
- 可观测证据：`tests/test_phase35_conversation_continuity.py::test_tc_phase3511_004_context_compiler_outputs_julia_context_v4`。
- 验收映射：`ACPT-P3.5.11-02`。

#### F-P3.phase5.11-T01-03 TopicTracker 与 Open Loop 管理

- 输入：当前输入、最近 turn topics、上一 ConversationState。
- 处理逻辑：维护 active_topics 上限、检测 project/health/followup open loops，并按 importance 合并。
- 输出：bounded active_topics + open_loops。
- 失败处理：未知文本保留上一 arc/topic，不扩大 active_topics。
- 可观测证据：`tests/test_phase35_conversation_continuity.py::{test_tc_phase3511_001_arc_continuity_tracks_project_pressure,test_tc_phase3511_002_pronoun_reference_uses_recent_active_topic,test_tc_phase3511_003_topic_switch_keeps_topics_bounded}`。
- 验收映射：`ACPT-P3.5.11-03`。

#### F-P3.phase5.11-T01-04 ContinuityManager 状态演化

- 输入：previous_state + new_turn 或 preview current_user_input。
- 处理逻辑：生成/更新 current_arc、recent_turns、session_summary，并限制 recent_turns / topics 数量。
- 输出：新的 `ConversationContinuityContext`。
- 失败处理：recent_turns 异常元素忽略；open loops 去重；长 session 自动裁剪。
- 可观测证据：`tests/test_phase35_conversation_continuity.py::test_tc_phase3511_005_long_session_stability_caps_recent_turns_and_topics`。
- 验收映射：`ACPT-P3.5.11-04`。

#### F-P3.phase5.11-T01-05 JuliaContext v4 集成

- 输入：ContextCompiler 的 conversation_context dict / previous state / recent_turns。
- 处理逻辑：ContextCompiler 先 preview ConversationContinuity，再进行 Arbitration，最后生成带 mode 的 continuity context。
- 输出：`JuliaContext.conversation_context: ConversationContinuityContext`。
- 失败处理：无 previous_state 时生成安全默认连续性状态。
- 可观测证据：`tests/test_phase35_conversation_continuity.py::test_tc_phase3511_004_context_compiler_outputs_julia_context_v4` 与 `tests/test_phase35_context_compiler.py`。
- 验收映射：`ACPT-P3.5.11-05`。

#### F-P3.phase5.11-T01-06 Bridge Trace 与 Projection 接入

- 输入：DirectLLMBridge session history 与 ConversationContinuityContext。
- 处理逻辑：Bridge 保存 session conversation state；Projection 渲染 session_summary/current_arc/active_topics/open_loops/recent_turns；trace 输出 conversation_continuity。
- 输出：模型可见 continuity view + runtime trace。
- 失败处理：provider 失败不写空 assistant turn；legacy path 可保持空 cognitive_mode。
- 可观测证据：`tests/test_phase33_direct_llm_bridge.py` 与 `tests/test_phase35_cognitive_rendering.py`。
- 验收映射：`ACPT-P3.5.11-06`。

### 3) 接口与契约

新增：

```text
runtime/conversation_state/conversation_turn.py
runtime/conversation_state/conversation_memory.py
runtime/conversation_state/topic_tracker.py
runtime/conversation_state/session_summary.py
runtime/conversation_state/unresolved_context.py
runtime/conversation_state/continuity_manager.py
runtime/conversation_state/__init__.py
```

升级：

```text
runtime/cognitive/context_compiler/julia_context.py
runtime/cognitive/context_compiler/context_compiler.py
runtime/cognitive/context_validation/validator.py
runtime/cognitive/rendering/projection.py
runtime/conversation_runtime/bridge/direct_llm_bridge.py
```

### 4) 数据模型与状态变更

```python
@dataclass(frozen=True)
class ConversationTurn:
    turn_id: int
    user_text: str
    assistant_text: str
    timestamp: str
    topics: list[str]
    cognitive_mode: str
    metadata: dict[str, object]

@dataclass(frozen=True)
class ConversationContinuityContext:
    active_topics: list[str]
    open_loops: list[dict[str, object]]
    current_arc: str
    recent_turns: list[ConversationTurn]
    session_summary: str
```

JuliaContext v4：

```python
conversation_context: ConversationContinuityContext
```

状态约束：

- `recent_turns <= 8`
- `active_topics <= 8`，长 session 可按 manager 配置进一步收紧
- metadata 禁止 provider/backend/model/latency/tts/stt/session_id/turn_id

### 5) 实现步骤

1. 新增 `runtime/conversation_state/*` 数据模型与 manager。
2. ContextCompiler 接入 ContinuityManager，生成 JuliaContext v4。
3. ContextValidator 增加 conversation continuity quality metrics。
4. CognitiveProjection 渲染 session_summary/current_arc/open_loops。
5. DirectLLMBridge 保存 per-session conversation state，并在 trace 输出 `conversation_continuity`。
6. 新增 `tests/test_phase35_conversation_continuity.py` 并回归相关 Phase 3.5 测试。

### 6) 测试设计与命令

测试文件：

```text
tests/test_phase35_conversation_continuity.py
```

必跑命令：

```bash
python3 -m unittest tests.test_phase35_conversation_continuity
python3 -m unittest tests.test_phase35_context_arbitration tests.test_phase35_context_compiler tests.test_phase35_context_validation tests.test_phase35_cognitive_rendering tests.test_phase33_direct_llm_bridge tests.test_phase35_conversation_continuity
python3 -m unittest discover -s tests
```

预期：全部 OK。

### 7) 风险与回滚

风险：

- Conversation Continuity 与 Memory Runtime 边界混淆。
- active_topics 无限增长导致 prompt 漂移。
- open_loops 错误长期保留，影响后续回应。

缓解：

- conversation state 仅保存 session-level trajectory。
- recent_turns 与 active_topics 均有上限。
- validator 检查 active_topics 过载与 runtime leakage。

回滚：

- 移除 `runtime/conversation_state/`。
- JuliaContext 回退到 v3 dict conversation_context。
- ContextCompiler 移除 ContinuityManager preview/update。
- Projection 回退到旧 recent_turns dict 渲染。

### 8) 验收映射

- `ACPT-P3.5.11-01` ConversationTurn 事件契约成立。
- `ACPT-P3.5.11-02` ConversationContinuityContext 成为 JuliaContext v4 字段。
- `ACPT-P3.5.11-03` active topics / open loops 可持续追踪。
- `ACPT-P3.5.11-04` long session 话题与 recent_turns 有界。
- `ACPT-P3.5.11-05` ContextCompiler 输出 JuliaContext v4。
- `ACPT-P3.5.11-06` Projection/Bridge trace 使用 continuity view 且无 runtime leakage。
