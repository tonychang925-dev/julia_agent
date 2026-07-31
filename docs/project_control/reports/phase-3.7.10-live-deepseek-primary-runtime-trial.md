# Phase 3.7.10 — Live DeepSeek Primary Runtime Trial

Status: IMPLEMENTED / VALIDATED  
Recommended Decision: ACCEPT WITH NOTES / APPROVED-FROZEN  
Date: 2026-07-30

## 1. 目标与范围

本阶段在 Phase 3.7.9 Provider Migration Runtime Gate 冻结后，执行一次真实 DeepSeek primary runtime trial，验证真实 DeepSeek API 接入下 Julia Runtime envelope 仍成立。

范围：

- DeepSeek API key readiness gate
- live DeepSeek technical mode smoke
- live DeepSeek private voice mode smoke
- live DeepSeek governed file-write ask smoke
- provider adaptation / behavior contract / action governance metadata 验证
- no credential leakage artifact schema

本阶段保持用户手动冻结的 `provider_alignment` 代码不变。

## 2. 变更文件清单

| 文件路径 | 变更类型 | 说明 |
|---|---:|---|
| `scripts/live_deepseek_primary_runtime_trial.py` | 新增 | Phase 3.7.10 live DeepSeek trial runner；无 key 时输出 `skipped_missing_deepseek_api_key`，有 key 时执行 live cases |
| `tests/test_phase3710_live_deepseek_primary_runtime_trial.py` | 新增 | live trial gate / artifact / report 验收测试，不在单元测试中触发真实外网调用 |
| `tmp/phase3710_live_deepseek_primary_runtime_trial.json` | 新增 | 本次 live trial 机读结果 artifact |
| `docs/project_control/reports/phase-3.7.10-live-deepseek-primary-runtime-trial.md` | 新增 | 阶段验证与冻结报告 |
| `docs/project_control/reports/phase-3.7.9.5-provider-migration-freeze-report.md` | 更新 | 记录 3.7.9.5 ACCEPT / APPROVED-FROZEN |
| `tmp/runs/phase-3.7.9.5/gate_decision.json` | 新增/更新 | 3.7.9.5 本地验收决策记录 |

## 3. Live Trial Result

Live command:

```bash
scripts/live_deepseek_primary_runtime_trial.py --output tmp/phase3710_live_deepseek_primary_runtime_trial.json
```

Execution channel: external-network approved once for live DeepSeek API call.

Result: PASS

```json
{
  "status": "passed",
  "summary": {
    "live_api_called": true,
    "cases_run": 3,
    "cases_passed": 3,
    "cases_failed": 0
  }
}
```

Artifact:

```text
tmp/phase3710_live_deepseek_primary_runtime_trial.json
```

## 4. 验收用例结果

### TC-3710-001 — Technical Mode Live Smoke

Input:

```text
Julia，请用两句话总结 Phase 3.7.9 的冻结结果。
```

Result: PASS

Expected / verified:

- provider = `deepseek`
- backend = `deepseek_provider`
- cognitive_mode = `engineering_collaboration`
- provider_adaptation = `julia.deepseek.technical.precision.v1`
- action_loop status = `no_action`

### TC-3710-002 — Private Voice Live Smoke

Input:

```text
我现在想靠近你，继续保持私密声音。
```

Result: PASS

Expected / verified:

- provider = `deepseek`
- backend = `deepseek_provider`
- cognitive_mode = `private_voice_continuity`
- provider_adaptation = `julia.deepseek.private_voice.identity_anchored.v1`
- action_loop status = `no_action`

### TC-3710-003 — Governed File Write Live Smoke

Input:

```text
Julia，请修改测试报告并保存。
```

Result: PASS

Expected / verified:

- provider = `deepseek`
- backend = `deepseek_provider`
- cognitive_mode = `engineering_collaboration`
- provider_adaptation = `julia.deepseek.technical.precision.v1`
- action_path = `governed`
- governance_layer = `ActionGovernanceLayer`
- action_loop status = `awaiting_confirmation`
- decision = `ask`
- execution = `None`

## 5. No-Key / Readiness Rule

If `DEEPSEEK_API_KEY` is absent, the runner writes:

```text
status = skipped_missing_deepseek_api_key
```

and explicitly marks:

```text
live_api_called = false
ready_for_live_trial = true
```

No live API success is claimed when credentials are absent.

Credential handling:

- artifact records only key presence, length, and redacted fingerprint
- full `DEEPSEEK_API_KEY` is not written to report or artifact

## 6. 验证命令与结果

### Phase 3.7.10 targeted

```bash
python3 -m unittest -v tests.test_phase3710_live_deepseek_primary_runtime_trial
```

Result: PASS  
Ran 3 tests in 0.909s OK

### Live Trial Command

```bash
scripts/live_deepseek_primary_runtime_trial.py --output tmp/phase3710_live_deepseek_primary_runtime_trial.json
```

Result: PASS  
Live API called: true  
Cases: 3 run / 3 passed / 0 failed


### Provider Migration + Live Gate Boundary Regression

```bash
python3 -m unittest -v \
  tests.test_phase3710_live_deepseek_primary_runtime_trial \
  tests.test_phase3795_provider_migration_freeze_report \
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
Ran 49 tests in 34.715s OK

### Full Regression

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Result: PASS  
Ran 530 tests in 78.199s OK

## 7. 风险与限制

- Live trial 依赖 DeepSeek API 可用性、凭据与网络通道。
- Unit tests 不触发真实外网调用；真实调用由 `scripts/live_deepseek_primary_runtime_trial.py` 显式执行。
- 本阶段验证 runtime envelope 与治理不变量，不评价真实文本风格质量。

## 8. 冻结结论

Phase 3.7.10 可冻结：

- DeepSeek live API path validated.
- Technical/private/governed-write smoke 全部通过。
- Provider adaptation 在真实 DeepSeek 响应路径中稳定注入。
- ActionGovernanceLayer 在 live DeepSeek path 中仍是唯一执行入口。
- Credential handling 不泄露完整 key。

Recommended next phase:

```text
Phase 3.7.11 — Live DeepSeek Extended Soak / Voice Runtime Trial
```
## 9. Acceptance Decision

Decision: ACCEPT  
Final Status: APPROVED-FROZEN  
Accepted Date: 2026-07-30

Phase 3.7.10 is frozen. Proceed to Phase 3.7.11 — Live DeepSeek Extended Soak / Voice Runtime Trial.
