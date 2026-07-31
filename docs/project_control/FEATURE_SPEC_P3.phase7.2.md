# FEATURE_SPEC_P3.phase7.2 — Action Governance Runtime

## Task `P3.phase7.2-T01` — ActionIntent Governance Boundary

### 1) 目标与边界

目标：新增 Runtime-owned Action Governance，对 ActionIntent 输出 `allow / ask / reject` 决策，并提供可解释 reason/evidence。

非目标：

- 不执行 Capability。
- 不调用 shell/file/API。
- 不接 ClaudeCodeTool。
- 不把 provider/backend/model/latency/session/tts/stt 写入 ActionDecision。

### 2) 子功能分解

#### F-P3.phase7.2-T01-01 ActionDecision Schema

- 输入：policy decision、intent_type、risk_level、capability、reason、confidence、evidence。
- 处理逻辑：冻结 Runtime governance decision schema。
- 输出：ActionDecision。
- 失败处理：intent=None 输出 reject/no_action_intent。
- 可观测证据：`TC-PHASE372-008`。
- 验收映射：`ACPT-P3.7.2-01`。

#### F-P3.phase7.2-T01-02 Low-risk Allow

- 输入：low risk ActionIntent + known capability。
- 处理逻辑：允许进入后续 Capability Routing 阶段，但不执行。
- 输出：decision=allow。
- 失败处理：未知 capability 降级为 ask。
- 可观测证据：`TC-PHASE372-001`。
- 验收映射：`ACPT-P3.7.2-02`。

#### F-P3.phase7.2-T01-03 Ask / Reject Gate

- 输入：medium/high risk、unknown/prohibited capability、low confidence intent。
- 处理逻辑：medium/unknown → ask；high/prohibited/low-confidence → reject。
- 输出：ActionDecision。
- 失败处理：保守拒绝或请求确认。
- 可观测证据：`TC-PHASE372-002` 到 `TC-PHASE372-005`。
- 验收映射：`ACPT-P3.7.2-03`。

#### F-P3.phase7.2-T01-04 Runtime Isolation

- 输入：ActionIntent。
- 处理逻辑：ActionDecision 只包含 governance fields，不包含 RuntimeEnvelope/provider/TTS/STT metadata。
- 输出：runtime-clean decision。
- 失败处理：禁止字段不进入 schema。
- 可观测证据：`TC-PHASE372-006`。
- 验收映射：`ACPT-P3.7.2-04`。

#### F-P3.phase7.2-T01-05 Decision is not Execution

- 输入：allowed ActionIntent。
- 处理逻辑：decision=allow 也不生成 execution_id，不生成 command。
- 输出：execution_id=None。
- 失败处理：后续 Capability Layer 未接入前不可执行。
- 可观测证据：`TC-PHASE372-007`。
- 验收映射：`ACPT-P3.7.2-05`。

### 3) 接口与契约

新增/更新：

```text
runtime/action/action_decision.py
runtime/action/action_policy.py
runtime/action/__init__.py
```

Decision values:

```text
allow
ask
reject
```

### 4) 测试命令

```bash
python3 -m unittest tests.test_phase372_action_governance
python3 -m unittest discover -s tests
```

### 5) 风险与回滚

风险：第一版 policy 保守，可能对未来可执行 intent 过多 ask/reject。

回滚：恢复 `runtime/action/action_policy.py` / `action_decision.py` 为 placeholder，并删除 `tests/test_phase372_action_governance.py`。

### 6) 验收映射

- `ACPT-P3.7.2-01` ActionDecision schema 成立。
- `ACPT-P3.7.2-02` low-risk known capability allow。
- `ACPT-P3.7.2-03` medium/unknown ask；high/low-confidence reject。
- `ACPT-P3.7.2-04` runtime isolation。
- `ACPT-P3.7.2-05` decision not execution。
