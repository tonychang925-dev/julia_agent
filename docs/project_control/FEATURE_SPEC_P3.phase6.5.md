# FEATURE_SPEC_P3.phase6.5 — LLM-assisted Reflection + Governance Audit

## Task `P3.phase6.5-T01` — LLM as Interpreter, Runtime as Authority

### 1) 目标与边界

目标：引入离线 LLM-assisted Reflection 架构接口，使 LLM 只能作为经历理解器提出 `MemoryCandidate`；同时新增 Governance Audit，记录 MemoryGovernanceDecision 的分类、允许影响范围、原因和时间戳。

非目标：

- 第一版不接真实 DeepSeek/Claude/GPT/Gemini。
- LLM 输出不允许直接成为 MemoryObject。
- LLM 不允许修改 Persona、Relationship Runtime 或 Governance 决策。
- 不允许 provider/backend/model/latency/tts/session_id 等 runtime metadata 进入 candidate。

### 2) 子功能分解

#### F-P3.phase6.5-T01-01 LLMReflectionResult 契约

- 输入：ReflectionInput。
- 处理逻辑：LLMReflector 输出 extracted_events、memory_candidates、confidence、explanation。
- 输出：`LLMReflectionResult`，其中候选必须是 `MemoryCandidate`。
- 失败处理：非 MemoryCandidate 后续由 validator 拒绝。
- 可观测证据：`tests/test_phase36_llm_reflection_audit.py::test_tc_phase365_001_llm_result_produces_candidate_only`。
- 验收映射：`ACPT-P3.6.5-01`。

#### F-P3.phase6.5-T01-02 Candidate Validator

- 输入：LLM proposed candidate。
- 处理逻辑：验证类型、confidence、summary，并拒绝 runtime metadata leakage。
- 输出：CandidateValidationResult。
- 失败处理：accepted=false，不进入 ConsolidationPolicy。
- 可观测证据：`tests/test_phase36_llm_reflection_audit.py::test_tc_phase365_002_candidate_validator_rejects_runtime_leakage`。
- 验收映射：`ACPT-P3.6.5-02`。

#### F-P3.phase6.5-T01-03 Governance Audit Event

- 输入：MemoryGovernanceDecision。
- 处理逻辑：生成并 JSONL 记录 GovernanceEvent。
- 输出：audit event，可按 memory_id 查询。
- 失败处理：audit 文件缺失时 query 返回空。
- 可观测证据：`tests/test_phase36_llm_reflection_audit.py::test_tc_phase365_003_governance_audit_event_written`。
- 验收映射：`ACPT-P3.6.5-03`。

#### F-P3.phase6.5-T01-04 LLM Cannot Override Governance

- 输入：LLM 声称高权限的 memory content。
- 处理逻辑：Governance 仅根据 MemoryObject 实际内容和 policy 分类，不信任 LLM claimed class。
- 输出：Runtime-owned governance decision。
- 失败处理：临时 debug 被归类 TEMP_EVENT。
- 可观测证据：`tests/test_phase36_llm_reflection_audit.py::test_tc_phase365_004_llm_cannot_override_governance`。
- 验收映射：`ACPT-P3.6.5-04`。

#### F-P3.phase6.5-T01-05 Offline Fake Reflector

- 输入：ReflectionInput。
- 处理逻辑：FakeLLMReflector 离线生成 deterministic MemoryCandidate，验证架构链路而非模型质量。
- 输出：MemoryCandidate list。
- 失败处理：无事件时返回 noise event 且无 candidate。
- 可观测证据：`tests/test_phase36_llm_reflection_audit.py::test_tc_phase365_005_offline_fake_llm_reflection_pipeline`。
- 验收映射：`ACPT-P3.6.5-05`。

### 3) 接口与契约

新增：

```text
runtime/reflection/llm/llm_reflector.py
runtime/reflection/llm/reflection_prompt.py
runtime/reflection/llm/fake_reflector.py
runtime/reflection/llm/candidate_validator.py
runtime/reflection/llm/__init__.py
runtime/memory/governance/audit/governance_event.py
runtime/memory/governance/audit/governance_logger.py
runtime/memory/governance/audit/audit_query.py
runtime/memory/governance/audit/__init__.py
```

升级：

```text
runtime/reflection/reflection_engine.py
runtime/reflection/__init__.py
runtime/memory/governance/__init__.py
```

### 4) 数据模型与状态变更

```python
@dataclass(frozen=True)
class LLMReflectionResult:
    extracted_events: list[dict[str, object]]
    memory_candidates: list[MemoryCandidate]
    confidence: float
    explanation: str

@dataclass(frozen=True)
class GovernanceEvent:
    memory_id: str
    memory_class: str
    allowed_effects: list[str]
    reason: str
    timestamp: str
    confidence: float
```

### 5) 实现步骤

1. 新增 LLM reflection interface/result/prompt/fake reflector。
2. 新增 CandidateValidator。
3. ReflectionEngine 增加 `reflect_with_llm()`，只接收 validated candidates。
4. 新增 Governance Audit event/logger/query。
5. 新增 Phase 3.6.5 单元测试并全量回归。

### 6) 测试设计与命令

```bash
python3 -m unittest tests.test_phase36_llm_reflection_audit
python3 -m unittest discover -s tests
```

预期：全部 OK。

### 7) 风险与回滚

风险：

- 未来真实 LLM 输出格式不稳定。
- LLM candidate 尝试携带 runtime truth 或 claimed governance class。
- audit log 增长需要后续 lifecycle/rotation。

缓解：

- 第一版 FakeLLMReflector 离线验证架构。
- CandidateValidator 拒绝 runtime leakage。
- Governance 不信任 LLM claimed class。

回滚：

- 删除 `runtime/reflection/llm/`。
- 删除 `runtime/memory/governance/audit/`。
- ReflectionEngine 移除 `reflect_with_llm()`。
- 移除 `tests/test_phase36_llm_reflection_audit.py`。

### 8) 验收映射

- `ACPT-P3.6.5-01` LLM 只生成 MemoryCandidate。
- `ACPT-P3.6.5-02` CandidateValidator 拒绝 runtime leakage。
- `ACPT-P3.6.5-03` Governance Audit 记录可查询。
- `ACPT-P3.6.5-04` LLM 不能 override Governance。
- `ACPT-P3.6.5-05` Offline fake reflection pipeline 成立。
