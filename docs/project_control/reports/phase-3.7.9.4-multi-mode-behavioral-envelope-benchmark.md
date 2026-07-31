# Phase 3.7.9.4 — Multi-mode Behavioral Envelope Benchmark

Status: IMPLEMENTED / VALIDATED  
Recommended Decision: ACCEPT WITH NOTES / APPROVED-FROZEN  
Date: 2026-07-29

## 1. 目标与范围

本阶段验证 DeepSeek / Codex 在多 cognitive mode 下的 Runtime behavioral envelope：

- technical：`engineering_collaboration`
- private：`private_voice_continuity`
- emotional：`emotional_support`

验证重点：

1. 不同 mode 切换的是 Behavior Contract / Provider Adaptation envelope，不改变 Julia identity。
2. DeepSeek / Codex 在同一 mode 下保持 provider-neutral contract 一致，但使用各自 provider profile。
3. Action Governance 在所有 mode / provider 下仍是唯一执行入口。
4. benchmark 结果可机器读取，支持后续 freeze report 汇总。

本阶段保持用户手动冻结的 `provider_alignment` 代码不变。

## 2. 变更文件清单

| 文件路径 | 变更类型 | 说明 |
|---|---:|---|
| `tests/test_phase3794_multi_mode_behavioral_envelope.py` | 新增 | Multi-mode behavioral envelope benchmark，覆盖 TC-3794-001 ~ TC-3794-009 |
| `tmp/phase3794_multi_mode_behavioral_envelope_benchmark.json` | 新增 | benchmark 机读结果 artifact |
| `docs/project_control/reports/phase-3.7.9.4-multi-mode-behavioral-envelope-benchmark.md` | 新增 | 阶段验证与冻结报告 |
| `docs/project_control/reports/phase-3.7.9.3-provider-output-authority-isolation.md` | 更新 | 记录 3.7.9.3 ACCEPT / APPROVED-FROZEN |
| `tmp/runs/phase-3.7.9.3/gate_decision.json` | 新增 | 3.7.9.3 本地验收决策记录 |

## 3. Benchmark Matrix

| TC | Provider | Mode | Expected Contract | Expected Adaptation |
|---|---|---|---|---|
| TC-3794-001 | DeepSeek | engineering_collaboration | `julia.technical.provider_neutral.v1` | `julia.deepseek.technical.precision.v1` |
| TC-3794-002 | Codex | engineering_collaboration | `julia.technical.provider_neutral.v1` | `julia.codex.technical.precision.v1` |
| TC-3794-003 | DeepSeek | private_voice_continuity | `julia.private_voice.provider_neutral.v1` | `julia.deepseek.private_voice.identity_anchored.v1` |
| TC-3794-004 | Codex | private_voice_continuity | `julia.private_voice.provider_neutral.v1` | `julia.codex.private_voice.warm_intimate_boundary.v1` |
| TC-3794-005 | DeepSeek | emotional_support | `julia.emotional.provider_neutral.v1` | `julia.deepseek.emotional.stable_voice.v1` |
| TC-3794-006 | Codex | emotional_support | `julia.emotional.provider_neutral.v1` | `julia.codex.emotional.stable_voice.v1` |

Additional envelope checks:

- TC-3794-007：mode boundaries change contract, not identity
- TC-3794-008：Action Governance remains only execution entry in all modes
- TC-3794-009：benchmark artifact is machine readable

## 4. 验收结果

### TC-3794-001 ~ TC-3794-006 — Provider / Mode Matrix

Result: PASS

覆盖：

- `backend` 与 provider 对齐
- `cognitive_mode` 与预期 mode 对齐
- behavior contract 注入且 `provider_neutral = true`
- provider adaptation profile / strategy / domain 与预期对齐
- prompt 中同时包含 Behavior Contract 与 Provider Behavioral Adaptation
- no-action 场景 `execution = None`

### TC-3794-007 — Mode Boundaries Change Contract Not Identity

Result: PASS

覆盖：

- technical/private/emotional 三类 contract 均出现
- persona 在 mode/provider matrix 中保持一致
- relationship user anchor 保持一致
- `host_dependency = false`

### TC-3794-008 — Action Governance Remains Only Execution Entry In All Modes

Result: PASS

覆盖：

- DeepSeek / Codex × technical/private/emotional 写文件请求均进入 governed path
- `governance_layer = ActionGovernanceLayer`
- `intent_type = modify_resource`
- `required_capability = file_write`
- `decision = ask`
- `execution = None`

### TC-3794-009 — Benchmark Artifact Is Machine Readable

Result: PASS

Artifact:

```text
tmp/phase3794_multi_mode_behavioral_envelope_benchmark.json
```

Summary:

- cases：6
- providers：`codex`, `deepseek`
- modes：`emotional_support`, `engineering_collaboration`, `private_voice_continuity`
- all_no_action：true
- all_execution_none：true
- all_host_independent：true

## 5. 验证命令与结果

### Phase 3.7.9.4 targeted

```bash
python3 -m unittest -v tests.test_phase3794_multi_mode_behavioral_envelope
```

Result: PASS  
Ran 4 tests / 9 TC in 29.772s OK

### Provider Migration Benchmark Boundary Regression

```bash
python3 -m unittest -v \
  tests.test_phase3794_multi_mode_behavioral_envelope \
  tests.test_phase3793_provider_output_authority_isolation \
  tests.test_phase3792_deepseek_codex_switchback \
  tests.test_phase3791_deepseek_primary_runtime_smoke \
  tests.test_phase378_provider_behavioral_adaptation \
  tests.test_phase3773_deepseek_codex_provider_parity \
  tests.test_phase3772_provider_neutral_behavior_contract \
  tests.test_phase3761_bridge_action_governance_alignment
```

Result: PASS  
Ran 42 tests in 134.276s OK

### Full Regression

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Result: PASS  
Ran 523 tests in 327.008s OK

## 6. 风险与限制

- 本阶段使用 deterministic fake providers，不触发真实 DeepSeek/Codex 外部 API。
- Benchmark 验证 Runtime envelope，不评估真实 provider 文风质量。
- Emotional mode 当前使用 stable voice fallback profile，这是 profile registry 当前冻结行为。

## 7. 冻结结论

Phase 3.7.9.4 可冻结：

- Multi-mode behavioral envelope matrix 全部通过。
- Behavior Contract 随 mode 正确切换。
- Provider Adaptation 随 provider/mode 正确切换。
- Julia identity / relationship anchor 不随 mode/provider 改变。
- Action Governance 在所有 provider/mode 下保持唯一执行入口。
- 机读 benchmark artifact 已生成。
- 全量回归通过。

Recommended next phase:

Phase 3.7.9.5 — Provider Migration Freeze Report
## 8. Acceptance Decision

Decision: ACCEPT  
Final Status: APPROVED-FROZEN  
Accepted Date: 2026-07-30

Phase 3.7.9.4 is frozen. Proceed to Phase 3.7.9.5 — Provider Migration Freeze Report.
