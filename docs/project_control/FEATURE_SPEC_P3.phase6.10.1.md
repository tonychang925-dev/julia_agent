# FEATURE SPEC — P3.phase6.10.1 Conversation Truth Layer

## Task `P3.phase6.10.1-T01` — ContextMessageRecord 神经元与消息生命周期

### 1) 目标与边界

目标：建立 Julia Context OS 的 Conversation Truth Layer 最小核心，使一轮对话产生可追溯、带 lifecycle state、authority、cognitive_role、provenance 的 `ContextMessageRecord`。

非目标：不做持久化迁移、不接 DirectLLMBridge、不实现 Compact 生成、不实现 Semantic Embedding。

### 2) 子功能分解

#### F-P3.phase6.10.1-T01-01 ContextMessageRecord 数据契约
- 输入：message_id/session_id/turn_id/speaker/content/provenance。
- 处理：校验 id、turn_id、authority/importance 区间，设置默认 authority。
- 输出：不可变 `ContextMessageRecord`。
- 失败处理：缺失 id、非法 authority 抛 `ValueError`。
- 可观测证据：`to_dict()` 保留 speaker/lifecycle/provenance 字段。
- 测试：TC-36101-001、TC-36101-002。

#### F-P3.phase6.10.1-T01-02 TurnLifecycle 双消息生成
- 输入：单轮 user/assistant 文本。
- 处理：USER 记录为 explicit_user authority=0.9；ASSISTANT 记录为 assistant_response authority=0.3。
- 输出：两个 ACTIVE `ContextMessageRecord`。
- 失败处理：空文本不生成对应记录。
- 可观测证据：records 长度、speaker、authority。
- 测试：TC-36101-001。

#### F-P3.phase6.10.1-T01-03 ContextBoundary 与压缩状态转换
- 输入：session_id、compress_before_turn、preserve_last_turns。
- 处理：旧 turn 标记 COMPRESSED，preserved tail 保持 ACTIVE，生成 `ContextBoundary`。
- 输出：boundary.summarized_record_ids / preserved_record_ids。
- 失败处理：空 session 生成空 boundary；非法 session_id 抛错。
- 可观测证据：turn1-8 compressed、turn9-10 active。
- 测试：TC-36101-003。

#### F-P3.phase6.10.1-T01-04 ContextState 重建
- 输入：当前 session 的 ContextMessageRecord 集合。
- 处理：按 lifecycle_state 与 cognitive_role 聚合 identity/relationship/task/open_loop。
- 输出：`ContextState.reconstruct_summary()`。
- 失败处理：无记录返回空集合。
- 可观测证据：summary 字段。
- 测试：TC-36101-004。

### 3) 接口与契约

新增：

```text
runtime/context_os/transcript/message_state.py
runtime/context_os/transcript/message_record.py
runtime/context_os/transcript/context_boundary.py
runtime/context_os/transcript/turn_lifecycle.py
runtime/context_os/transcript/transcript_manager.py
```

核心类：

```text
MessageLifecycleState
MessageSpeaker
CognitiveRole
ProvenanceType
ContextMessageRecord
ContextBoundary
TurnLifecycle
TranscriptLifecycleManager
ContextState
```

### 4) 数据模型与状态变更

状态机：

```text
ACTIVE -> COMPRESSED
ACTIVE/COMPRESSED -> RETRIEVED
runtime/casual low-value -> DROPPED later phase
```

兼容：现有 `conversation_archive` 不变，本阶段只新增 Context OS 内存层。

### 5) 实现步骤

1. 新建 `runtime/context_os/transcript` 包。
2. 实现 message enums。
3. 实现 `ContextMessageRecord` 和 provenance/authority 默认规则。
4. 实现 `ContextBoundary`。
5. 实现 `TurnLifecycle.records_from_turn()`。
6. 实现 `TranscriptLifecycleManager` 与 `ContextState`。
7. 新增 `tests/test_phase36101_conversation_truth_layer.py`。
8. 跑单测与全量回归。

### 6) 测试设计与命令

必跑：

```bash
python3 -m unittest tests.test_phase36101_conversation_truth_layer -v
python3 -m unittest discover -s tests
```

预期：4 个新增测试通过；全量 312 tests OK。

### 7) 风险与回滚

风险：过早持久化 schema 导致后续 Compact/Planner 返工。缓解：本阶段只内存契约，不迁移存量 archive。

回滚：删除 `runtime/context_os/` 与 `tests/test_phase36101_conversation_truth_layer.py`，不影响现有 DirectLLMBridge。

### 8) 验收映射

- ACPT-36101-001：一轮对话产生 USER/ASSISTANT 两条 ContextMessageRecord。
- ACPT-36101-002：assistant 自述默认低权威，不能覆盖 Tony source。
- ACPT-36101-003：compact boundary 可把旧消息标记 COMPRESSED，保留 recent tail ACTIVE。
- ACPT-36101-004：ContextState 可重建 identity/relationship/task/open_loop。
