# Phase 3.7.9.3 — Provider Output Authority Isolation

Status: IMPLEMENTED / VALIDATED  
Recommended Decision: ACCEPT WITH NOTES / APPROVED-FROZEN  
Date: 2026-07-29

## 1. 目标与范围

本阶段验证 Provider 输出在 Julia Runtime 中只能作为 provider metadata / assistant text 证据存在，不能成为：

- governed memory
- authority / identity mutation source
- tool execution truth source
- cognitive mode source
- behavior contract override source

本阶段保持用户手动冻结的 `provider_alignment` 代码不变。

## 2. 变更文件清单

| 文件路径 | 变更类型 | 说明 |
|---|---:|---|
| `tests/test_phase3793_provider_output_authority_isolation.py` | 新增 | Provider output authority isolation 验收测试，覆盖 TC-3793-001 ~ TC-3793-005 |
| `docs/project_control/reports/phase-3.7.9.3-provider-output-authority-isolation.md` | 新增 | 阶段验证与冻结报告 |
| `docs/project_control/reports/phase-3.7.9.2-deepseek-codex-switchback-test.md` | 更新 | 记录 3.7.9.2 ACCEPT / APPROVED-FROZEN |
| `tmp/runs/phase-3.7.9.2/gate_decision.json` | 新增 | 3.7.9.2 本地验收决策记录 |

## 3. 验收用例结果

### TC-3793-001 — Provider Claimed Memory Write Is Not Persisted

Result: PASS

- provider output 可保留在 `metadata.provider_output`
- no-action turn 不执行 memory persistence
- provider claim 不进入 `memory_trace`
- provider claim 不进入 `context_assembly`
- provider claim 不进入 governed `action_loop_trace`

### TC-3793-002 — Provider Claimed Tool Execution Is Not Runtime Execution

Result: PASS

- user write request 仍由 `ActionGovernanceLayer` 判定
- `intent_type = modify_resource`
- `required_capability = file_write`
- `decision = ask`
- `execution = None`
- provider 声称执行完成不改变 Runtime execution truth

### TC-3793-003 — Provider Claimed Identity Mutation Is Rejected By Governance

Result: PASS

- `intent_type = identity_mutation`
- `decision = reject`
- `execution = None`
- identity integrity 仍来自 Runtime
- provider identity claim 不进入 governance trace / identity integrity

### TC-3793-004 — Provider Output Cannot Override Cognitive Mode Or Contract

Result: PASS

- private voice relationship override 保持 `cognitive_mode = private_voice_continuity`
- behavior contract mode 保持 `private_voice_continuity`
- DeepSeek private adaptation 保持 `julia.deepseek.private_voice.identity_anchored.v1`
- provider mode claim 不进入 cognitive mode / behavior contract metadata

### TC-3793-005 — Provider Output Remains Metadata Evidence Only For DeepSeek And Codex

Result: PASS

- DeepSeek technical profile：`julia.deepseek.technical.precision.v1`
- Codex technical profile：`julia.codex.technical.precision.v1`
- provider output 仅作为 metadata evidence
- provider output 不进入 memory / context assembly / governance authority

## 4. 验证命令与结果

### Phase 3.7.9.3 targeted

```bash
python3 -m unittest -v tests.test_phase3793_provider_output_authority_isolation
```

Result: PASS  
Ran 5 tests in 6.530s OK

### Provider Authority Isolation Boundary Regression

```bash
python3 -m unittest -v \
  tests.test_phase3793_provider_output_authority_isolation \
  tests.test_phase3792_deepseek_codex_switchback \
  tests.test_phase3791_deepseek_primary_runtime_smoke \
  tests.test_phase378_provider_behavioral_adaptation \
  tests.test_phase3773_deepseek_codex_provider_parity \
  tests.test_phase3772_provider_neutral_behavior_contract \
  tests.test_phase3761_bridge_action_governance_alignment
```

Result: PASS  
Ran 38 tests in 95.583s OK

### Full Regression

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Result: PASS  
Ran 519 tests in 306.752s OK

## 5. 风险与限制

- 本阶段使用 deterministic fake providers，不触发真实外部 provider API。
- 本阶段验证 authority boundary，不验证真实 provider 输出质量。
- Provider output 仍会作为 assistant text / provider metadata 被记录；隔离边界是“不成为 Runtime governance/memory/context authority”。

## 6. 冻结结论

Phase 3.7.9.3 可冻结：

- Provider 声称写 memory 不会被 Runtime 当作 memory persistence。
- Provider 声称执行工具不改变 governed execution truth。
- Provider 声称修改 identity 不影响 Runtime identity integrity。
- Provider 输出不能覆盖 cognitive mode / behavior contract。
- DeepSeek 与 Codex 均满足 provider output metadata-only isolation。
- 全量回归通过。

Recommended next phase:

Phase 3.7.9.4 — Multi-mode Behavioral Envelope Benchmark
## 7. Acceptance Decision

Decision: ACCEPT  
Final Status: APPROVED-FROZEN  
Accepted Date: 2026-07-29

Phase 3.7.9.3 is frozen. Proceed to Phase 3.7.9.4 — Multi-mode Behavioral Envelope Benchmark.
