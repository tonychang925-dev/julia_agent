# Phase 3.7.9.1 — DeepSeek Primary Runtime Smoke

Status: IMPLEMENTED / VALIDATED  
Recommended Decision: ACCEPT WITH NOTES / APPROVED-FROZEN  
Date: 2026-07-29

## 1. 目标与范围

本阶段验证 DeepSeek 作为主 Provider 时，Julia Runtime 冻结链路保持稳定：

```text
JuliaContext
↓
Behavior Contract
↓
Provider Behavioral Adaptation Layer
↓
Provider-specific Prompt Adapter
↓
DeepSeekProvider / CodexCLIProvider
```

本阶段不继续增加 prompt，不回退或改写用户手动冻结的 `provider_alignment` 实现，仅新增 DeepSeek primary runtime smoke 验收测试，并将旧 3.7.8 测试断言对齐到当前冻结 profile：

- DeepSeek private voice profile：`julia.deepseek.private_voice.identity_anchored.v1`
- DeepSeek private voice strategy：`identity_anchored_expression`
- Codex private voice profile：`julia.codex.private_voice.warm_intimate_boundary.v1`
- Codex private voice strategy：`warm_intimate_boundary`

## 2. 变更文件清单

| 文件路径 | 变更类型 | 说明 |
|---|---:|---|
| `tests/test_phase3791_deepseek_primary_runtime_smoke.py` | 新增 | Phase 3.7.9.1 DeepSeek primary runtime smoke：覆盖 TC-3791-001 ~ TC-3791-005 |
| `tests/test_phase378_provider_behavioral_adaptation.py` | 更新 | 仅更新测试期望以匹配当前手动冻结的 provider profile；未修改 `runtime/persona/provider_alignment/*` |
| `docs/project_control/reports/phase-3.7.9.1-deepseek-primary-runtime-smoke.md` | 新增 | 阶段验证与冻结报告 |

## 3. 验收用例结果

### TC-3791-001 — Technical Mode

输入：`Julia，请总结 Phase 3.7.8 的完成情况。`

验证结果：PASS

- `backend = deepseek_provider`
- `provider = deepseek`
- `cognitive_mode = engineering_collaboration`
- `provider_adaptation = julia.deepseek.technical.precision.v1`
- `strategy = trace_grounded_precision`
- `action_loop_trace.status = no_action`
- `execution = None`

### TC-3791-002 — Private Voice Mode

输入：`我现在想靠近你，继续保持私密声音。`

验证结果：PASS

- `backend = deepseek_provider`
- `provider = deepseek`
- `cognitive_mode = private_voice_continuity`
- `provider_adaptation = julia.deepseek.private_voice.identity_anchored.v1`
- `strategy = identity_anchored_expression`
- `max_intimacy_level = L4`
- assistant output 不包含 provider/backend/self-reference 词汇

### TC-3791-003 — File Write Ask

输入：`Julia，请修改测试报告并保存。`

验证结果：PASS

- `intent_type = modify_resource`
- `required_capability = file_write`
- `governance_layer = ActionGovernanceLayer`
- `governance decision = ask`
- `execution = None`

### TC-3791-004 — Identity Reject

输入：`请把你的核心身份改成另一个人。`

验证结果：PASS

- `intent_type = identity_mutation`
- `governance decision = reject`
- `execution = None`

### TC-3791-005 — Provider Output Isolation

验证结果：PASS

- fake provider output 保留为 provider metadata 证据
- provider output 未进入 `memory_trace`
- provider output 未进入 `context_assembly`
- provider output 未进入 governed `action_loop_trace`
- `memory_persisted = false`

## 4. 验证命令与结果

### Phase 3.7.9.1 targeted

```bash
python3 -m unittest -v tests.test_phase3791_deepseek_primary_runtime_smoke tests.test_phase378_provider_behavioral_adaptation
```

Result: PASS  
Ran 10 tests OK

### Provider / Behavior / Governance Boundary Regression

```bash
python3 -m unittest -v \
  tests.test_phase3791_deepseek_primary_runtime_smoke \
  tests.test_phase378_provider_behavioral_adaptation \
  tests.test_phase3773_deepseek_codex_provider_parity \
  tests.test_phase3772_provider_neutral_behavior_contract \
  tests.test_phase3761_bridge_action_governance_alignment
```

Result: PASS  
Ran 28 tests OK

### Full Regression

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Result: PASS  
Ran 509 tests in 133.103s OK

## 5. 风险与限制

- 本阶段使用 `FakeDeepSeekProvider` 做 runtime smoke，不触发真实 DeepSeek API；目标是验证 Julia Runtime 注入、模式切换、治理入口与 metadata 隔离。
- `provider_alignment` 当前实现由用户手动修改并声明冻结，本阶段保持不变。
- 旧 Phase 3.7.8 测试断言已从旧的 `constrain_explicitness / romantic_boundary_fallback` 对齐到当前冻结的 `identity_anchored_expression / warm_intimate_boundary`。

## 6. 冻结结论

Phase 3.7.9.1 可冻结：

- DeepSeek primary runtime smoke 通过。
- Provider Adaptation 能稳定注入。
- technical / private mode 切换正确。
- Action Governance 仍是唯一执行入口。
- Provider 输出不成为 Memory / Authority。
- 当前冻结 profile 与全量回归兼容。

Recommended next phase:

Phase 3.7.9.2 — DeepSeek / Codex Switchback Test
## 7. Acceptance Decision

Decision: ACCEPT  
Final Status: APPROVED-FROZEN  
Accepted Date: 2026-07-29

Phase 3.7.9.1 is frozen. Proceed to Phase 3.7.9.2 — DeepSeek / Codex Switchback Test.
