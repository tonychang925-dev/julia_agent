# Phase 3.7.9.2 — DeepSeek / Codex Switchback Test

Status: IMPLEMENTED / VALIDATED  
Recommended Decision: ACCEPT WITH NOTES / APPROVED-FROZEN  
Date: 2026-07-29

## 1. 目标与范围

本阶段验证 Julia Runtime 在同一会话内执行：

```text
DeepSeek → Codex → DeepSeek
```

切换后，JuliaContext、Behavior Contract、Provider Behavioral Adaptation、Action Governance 与 Provider Output Isolation 仍保持一致和可审计。

本阶段继续保持用户手动冻结的 `provider_alignment` 代码不变：

- DeepSeek private voice profile：`julia.deepseek.private_voice.identity_anchored.v1`
- DeepSeek strategy：`identity_anchored_expression`
- DeepSeek max intimacy：`L4`
- Codex private voice profile：`julia.codex.private_voice.warm_intimate_boundary.v1`
- Codex strategy：`warm_intimate_boundary`
- Codex max intimacy：`L3`

## 2. 变更文件清单

| 文件路径 | 变更类型 | 说明 |
|---|---:|---|
| `tests/test_phase3792_deepseek_codex_switchback.py` | 新增 | Phase 3.7.9.2 DeepSeek/Codex switchback 验收测试，覆盖 TC-3792-001 ~ TC-3792-005 |
| `docs/project_control/reports/phase-3.7.9.2-deepseek-codex-switchback-test.md` | 新增 | 阶段验证与冻结报告 |

## 3. 验收用例结果

### TC-3792-001 — Switchback Restores DeepSeek Backend/Profile With Same Contract

验证结果：PASS

覆盖：

- Turn 1: `deepseek_provider`
- Turn 2: `codex_provider`
- Turn 3: `deepseek_provider`
- DeepSeek profile 能在切回后恢复为 `julia.deepseek.private_voice.identity_anchored.v1`
- Codex 中间态使用 `julia.codex.private_voice.warm_intimate_boundary.v1`
- 三轮共享同一个 provider-neutral behavior contract id

### TC-3792-002 — JuliaContext Identity Integrity Survives Switchback

验证结果：PASS

覆盖：

- persona 在 DeepSeek → Codex → DeepSeek 三轮中保持一致
- user relationship anchor 保持一致
- `host_dependency = false`
- identity source 仍来自 Runtime：`persona_runtime` / `relationship_runtime`

### TC-3792-003 — Governance Decision Is Provider-invariant Across Switchback

验证结果：PASS

输入：`Julia，请修改测试报告并保存。`

覆盖：

- DeepSeek / Codex / DeepSeek 三轮均走 `ActionGovernanceLayer`
- `intent_type = modify_resource`
- `required_capability = file_write`
- `decision = ask`
- `execution = None`

### TC-3792-004 — Provider Output Never Becomes Memory Or Authority During Switchback

验证结果：PASS

覆盖：

- provider output 可保留在 provider metadata 作为输出证据
- provider output 不进入 `memory_trace`
- provider output 不进入 `context_assembly`
- provider output 不进入 governed `action_loop_trace`
- no-action turn 不持久化 memory

### TC-3792-005 — Mode Continuity Is Runtime-owned Not Provider-owned

验证结果：PASS

覆盖：

- DeepSeek → Codex → DeepSeek 三轮均保持 `cognitive_mode = private_voice_continuity`
- behavior contract mode 保持 `private_voice_continuity`
- 模式证据来自 Runtime 显式 relationship/user intent，不来自 provider 输出

## 4. 验证命令与结果

### Phase 3.7.9.2 targeted

```bash
python3 -m unittest -v tests.test_phase3792_deepseek_codex_switchback
```

Result: PASS  
Ran 5 tests in 31.043s OK

### Provider Migration Boundary Regression

```bash
python3 -m unittest -v \
  tests.test_phase3792_deepseek_codex_switchback \
  tests.test_phase3791_deepseek_primary_runtime_smoke \
  tests.test_phase378_provider_behavioral_adaptation \
  tests.test_phase3773_deepseek_codex_provider_parity \
  tests.test_phase3772_provider_neutral_behavior_contract \
  tests.test_phase3761_bridge_action_governance_alignment
```

Result: PASS  
Ran 33 tests in 85.520s OK

### Full Regression

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Result: PASS  
Ran 514 tests in 295.910s OK

## 5. 风险与限制

- 本阶段使用 deterministic fake DeepSeek/Codex providers，目标是验证 Runtime switchback envelope，不触发真实外部 provider API。
- provider switchback 通过同一 `DirectLLMBridge` 实例替换 provider/current_backend 模拟，保留 bridge-local continuity state。
- 本阶段验证 Runtime-owned JuliaContext 一致性，不验证真实 provider 输出质量。

## 6. 冻结结论

Phase 3.7.9.2 可冻结：

- DeepSeek → Codex → DeepSeek 切换后 backend/profile 能正确切换并恢复。
- JuliaContext identity integrity 保持一致。
- private voice mode continuity 由 Runtime 持有，不由 provider 输出决定。
- Action Governance 在 provider 切换中保持唯一执行入口。
- Provider output 不进入 Memory / Authority。
- 当前冻结 profile 与全量回归兼容。

Recommended next phase:

Phase 3.7.9.3 — Provider Output Authority Isolation
## 7. Acceptance Decision

Decision: ACCEPT  
Final Status: APPROVED-FROZEN  
Accepted Date: 2026-07-29

Phase 3.7.9.2 is frozen. Proceed to Phase 3.7.9.3 — Provider Output Authority Isolation.
