# FEATURE_SPEC_P3.phase6.4 — Memory Governance Runtime

## Task `P3.phase6.4-T01` — Memory Influence Classification & Protection

### 1) 目标与边界

目标：新增 Memory Governance Runtime，定义不同 MemoryObject 对 Julia Identity、Relationship、Behavior、Project Continuity、Future Context 的允许影响范围，形成 Cognitive Ownership Principle 的长期状态防线。

非目标：

- 不让 LLM 决定 memory 是否改变 Julia。
- 不修改 Persona/Relationship Runtime 状态文件。
- 不改变 lifecycle action 逻辑；Governance 只决定 allowed influence。
- 不让 provider/backend/model/latency/tts/session_id 等 RuntimeEnvelope 信息进入治理判断。

### 2) 子功能分解

#### F-P3.phase6.4-T01-01 Memory Classification

- 输入：MemoryObject。
- 处理逻辑：分类为 CORE_IDENTITY / RELATIONSHIP_FOUNDATION / PROJECT_MILESTONE / BEHAVIOR_PREFERENCE / NORMAL_EPISODE / TEMP_EVENT / ARCHIVAL。
- 输出：MemoryClass。
- 失败处理：未知 memory 默认为 NORMAL_EPISODE。
- 可观测证据：`tests/test_phase36_memory_governance.py::{test_tc_phase364_001_core_identity_protection,test_tc_phase364_002_project_milestone_classification,test_tc_phase364_003_behavior_preference_classification,test_tc_phase364_004_temp_event_classification}`。
- 验收映射：`ACPT-P3.6.4-01`。

#### F-P3.phase6.4-T01-02 Protection Policy

- 输入：MemoryClass。
- 处理逻辑：映射 protection_level：immutable_permanent / strong_protection / long_term_protection / updateable_preference / normal_lifecycle / low_protection / archived_inactive。
- 输出：protection_level。
- 失败处理：分类失败走 normal_lifecycle。
- 可观测证据：`tests/test_phase36_memory_governance.py::test_tc_phase364_001_core_identity_protection`。
- 验收映射：`ACPT-P3.6.4-02`。

#### F-P3.phase6.4-T01-03 Retention Policy

- 输入：MemoryClass。
- 处理逻辑：映射 retention_policy：permanent_no_decay_archive / long_term_protected / long_term_reinforce_merge / reinforce_or_update / normal_decay / fast_archive / inactive_archive。
- 输出：retention_policy。
- 失败处理：分类失败走 normal_decay。
- 可观测证据：`tests/test_phase36_memory_governance.py::test_tc_phase364_004_temp_event_classification`。
- 验收映射：`ACPT-P3.6.4-03`。

#### F-P3.phase6.4-T01-04 Allowed Effects

- 输入：MemoryClass。
- 处理逻辑：限制 memory 可影响的 JuliaContext 层，例如 core_identity 可影响 identity_context，project_milestone 不可影响 identity_context。
- 输出：allowed_effects list。
- 失败处理：NORMAL_EPISODE 仅允许 memory_retrieval。
- 可观测证据：`tests/test_phase36_memory_governance.py::test_tc_phase364_005_allowed_effects_are_scoped_by_class`。
- 验收映射：`ACPT-P3.6.4-04`。

#### F-P3.phase6.4-T01-05 Governance Decision Explainability

- 输入：MemoryObject。
- 处理逻辑：生成 `MemoryGovernanceDecision(memory_id, memory_class, protection_level, allowed_effects, retention_policy, reason, confidence)`。
- 输出：可解释治理决策。
- 失败处理：confidence 低但仍必须有 reason。
- 可观测证据：`tests/test_phase36_memory_governance.py::test_tc_phase364_006_governance_explainability`。
- 验收映射：`ACPT-P3.6.4-05`。

#### F-P3.phase6.4-T01-06 MemoryRuntime Governance Facade

- 输入：MemoryObject 或 store 中全部 memories。
- 处理逻辑：MemoryRuntime 暴露 `govern_memory()` / `govern_all()`。
- 输出：MemoryGovernanceDecision list。
- 失败处理：空 store 返回空 list。
- 可观测证据：`tests/test_phase36_memory_governance.py::test_tc_phase364_007_memory_runtime_governance_facade`。
- 验收映射：`ACPT-P3.6.4-06`。

### 3) 接口与契约

新增：

```text
runtime/memory/governance/memory_classification.py
runtime/memory/governance/protection_policy.py
runtime/memory/governance/retention_policy.py
runtime/memory/governance/governance_decision.py
runtime/memory/governance/governance_manager.py
runtime/memory/governance/__init__.py
```

升级：

```text
runtime/memory/memory_runtime.py
```

### 4) 数据模型与状态变更

```python
class MemoryClass(Enum):
    CORE_IDENTITY = "core_identity"
    RELATIONSHIP_FOUNDATION = "relationship_foundation"
    PROJECT_MILESTONE = "project_milestone"
    BEHAVIOR_PREFERENCE = "behavior_preference"
    NORMAL_EPISODE = "normal_episode"
    TEMP_EVENT = "temp_event"
    ARCHIVAL = "archival"

@dataclass(frozen=True)
class MemoryGovernanceDecision:
    memory_id: str
    memory_class: str
    protection_level: str
    allowed_effects: list[str]
    retention_policy: str
    reason: str
    confidence: float
```

### 5) 实现步骤

1. 新增 MemoryClass enum。
2. 新增 ProtectionPolicy / RetentionPolicy。
3. 新增 GovernanceDecision DTO。
4. 新增 GovernanceManager classify/decide/decide_many。
5. MemoryRuntime 接入 governance facade。
6. 新增 Phase 3.6.4 单元测试并全量回归。

### 6) 测试设计与命令

```bash
python3 -m unittest tests.test_phase36_memory_governance
python3 -m unittest discover -s tests
```

预期：全部 OK。

### 7) 风险与回滚

风险：

- classification 规则过宽，导致普通 memory 获得过高 influence。
- relationship memory 全部保护，造成膨胀。
- LLM-assisted Reflection 后候选过强，需要 Governance gate 继续兜底。

缓解：

- relationship protection 只保护 core/foundation，不保护普通 relationship event。
- allowed_effects 明确禁止 Project Milestone / Normal Episode 改写 identity。
- 测试覆盖各类 class 与 explainability。

回滚：

- 删除 `runtime/memory/governance/`。
- `MemoryRuntime` 移除 governance facade。
- 移除 `tests/test_phase36_memory_governance.py`。

### 8) 验收映射

- `ACPT-P3.6.4-01` Memory classification 成立。
- `ACPT-P3.6.4-02` Core identity immutable protection 成立。
- `ACPT-P3.6.4-03` Retention policy 成立。
- `ACPT-P3.6.4-04` Allowed effects scoped by class。
- `ACPT-P3.6.4-05` Governance decisions explainable。
- `ACPT-P3.6.4-06` MemoryRuntime facade 可用。
