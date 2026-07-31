# FEATURE_SPEC_P3.phase7.4 — Action Reflection → Memory Integration

## Task `P3.phase7.4-T01` — ActionExecutionResult to MemoryCandidate Reflection

### 1) 目标与边界

目标：把已治理的行动结果转换为 `MemoryCandidate | None`，让 Julia 能从行动结果中形成可审计的候选记忆，并保持 Memory Runtime 的持久化主权。

非目标：

- 不直接写入 `MemoryObject`。
- 不直接修改 Persona / Relationship。
- 不把 provider/backend/model/latency/tts/stt/session_id/turn_id 写入认知候选记忆。
- 不把 ask/reject 的未执行路径沉淀为长期记忆噪声。

### 2) 子功能分解

#### F-P3.phase7.4-T01-01 ActionReflectionEngine Schema

- 输入：`ActionExecutionResult`。
- 处理逻辑：按 `executed/skipped/blocked/failed` 生命周期状态选择反思策略。
- 输出：`MemoryCandidate | None`。
- 失败处理：缺少 intent/decision 时返回 `None`。
- 可观测证据：`TC-PHASE374-001`, `TC-PHASE374-006`。
- 验收映射：`ACPT-P3.7.4-01`。

#### F-P3.phase7.4-T01-02 Successful Action Candidate

- 输入：status=executed 且 tool_result.ok=true。
- 处理逻辑：生成 episodic 候选记忆，记录 governed action + capability lifecycle。
- 输出：source=`action_reflection` 的 `MemoryCandidate`。
- 失败处理：非 ok 不走成功路径。
- 可观测证据：`TC-PHASE374-001`。
- 验收映射：`ACPT-P3.7.4-02`。

#### F-P3.phase7.4-T01-03 Noise Filtering

- 输入：decision=ask 导致 status=skipped。
- 处理逻辑：不生成长期候选记忆。
- 输出：`None`。
- 失败处理：保守过滤未执行行动。
- 可观测证据：`TC-PHASE374-002`。
- 验收映射：`ACPT-P3.7.4-03`。

#### F-P3.phase7.4-T01-04 Failure and Capability Gap Learning

- 输入：status=failed。
- 处理逻辑：识别未注册 capability 等执行失败，生成 capability gap 候选记忆。
- 输出：带 `capability_gap` reason 的 `MemoryCandidate`。
- 失败处理：未知失败归类为 `action_execution_failed`。
- 可观测证据：`TC-PHASE374-003`。
- 验收映射：`ACPT-P3.7.4-04`。

#### F-P3.phase7.4-T01-05 Governance Block Learning

- 输入：status=blocked 且 permission.allowed=false。
- 处理逻辑：生成 governance 候选记忆，记录 permission guard 的保护性边界。
- 输出：topics 包含 `Action Governance` 的 `MemoryCandidate`。
- 失败处理：缺少 permission evidence 时不生成候选。
- 可观测证据：`TC-PHASE374-004`。
- 验收映射：`ACPT-P3.7.4-05`。

#### F-P3.phase7.4-T01-06 Runtime Isolation

- 输入：包含运行时噪声的 ActionIntent reason。
- 处理逻辑：候选记忆只保留认知行动摘要，不复制 provider/session/voice 元数据。
- 输出：runtime-clean `MemoryCandidate`。
- 失败处理：禁止字段不进入 summary/reason/topics/source。
- 可观测证据：`TC-PHASE374-005`。
- 验收映射：`ACPT-P3.7.4-06`。

### 3) 接口与契约

新增/更新：

```text
runtime/action/action_reflection.py
runtime/action/__init__.py
tests/test_phase374_action_reflection_memory_integration.py
```

核心接口：

```python
@dataclass(frozen=True)
class ActionReflectionEngine:
    source: str = "action_reflection"

    def reflect(self, result: ActionExecutionResult) -> MemoryCandidate | None:
        ...
```

输出只允许：

```text
MemoryCandidate
None
```

### 4) 测试命令

```bash
python3 -m unittest tests.test_phase374_action_reflection_memory_integration
python3 -m unittest discover -s tests
```

预期结果：专项 6 tests OK；全量 254 tests OK。

### 5) 风险与回滚

风险：v1 反思摘要为确定性模板，尚未引入更细粒度的行动结果语义压缩。

缓解：仅生成候选，不持久化；Memory Governance 后续仍可拒绝/降权。

回滚：恢复 `runtime/action/action_reflection.py` 为 placeholder，移除 `ActionReflectionEngine` export，删除 `tests/test_phase374_action_reflection_memory_integration.py`。

### 6) 验收映射

- `ACPT-P3.7.4-01` ActionReflectionEngine 输出契约成立。
- `ACPT-P3.7.4-02` 成功行动可生成 MemoryCandidate。
- `ACPT-P3.7.4-03` ask/skipped 不产生长期噪声。
- `ACPT-P3.7.4-04` capability gap 可学习。
- `ACPT-P3.7.4-05` permission block 可学习治理边界。
- `ACPT-P3.7.4-06` 候选记忆不携带 provider/session/voice/runtime 元数据噪声。
