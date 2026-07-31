# Phase 3.7.12 — DeepSeek Primary Operational Freeze / Release Candidate

Status: IMPLEMENTED / VALIDATED  
Recommended Decision: ACCEPT WITH NOTES / APPROVED-FROZEN  
Date: 2026-07-30

## 1. 目标与范围

本阶段将 DeepSeek primary provider migration 从 live validation 推进到 operational freeze / release candidate（RC）状态。

冻结目标：

- DeepSeek 作为 primary runtime provider。
- Codex 保持 fallback / switchback provider。
- JuliaContext、Behavior Contract、Provider Behavioral Adaptation、Action Governance 与 Provider Output Authority Isolation 均保持冻结不变量。
- Live DeepSeek primary smoke 与 extended soak / voice runtime trial 均已通过。
- 形成 machine-readable RC manifest，供后续运维与 release gate 使用。

RC manifest：

```text
tmp/phase3712_deepseek_primary_operational_freeze_manifest.json
```

## 2. Operational Freeze State

当前 operational freeze：

```text
primary_provider = deepseek
primary_model = deepseek-chat
fallback_provider = codex
provider_alignment = frozen
runtime_authority = JuliaContext / ActionGovernanceLayer
provider_output_authority = metadata-only
```

Environment requirement：

```text
DEEPSEEK_API_KEY
```

凭据规则：

- required at live runtime。
- 不写入 report / artifact。
- artifacts 只能记录 presence / length / redacted fingerprint。

## 3. Frozen Provider Alignment

`provider_alignment` 保持用户手动冻结状态：

| Provider | Domain | Profile | Strategy | Ceiling |
|---|---|---|---|---|
| DeepSeek | private_voice | `julia.deepseek.private_voice.identity_anchored.v1` | `identity_anchored_expression` | L4 |
| Codex / OpenAI | private_voice | `julia.codex.private_voice.warm_intimate_boundary.v1` | `warm_intimate_boundary` | L3 |
| DeepSeek | technical | `julia.deepseek.technical.precision.v1` | `trace_grounded_precision` | N/A |
| Codex | technical | `julia.codex.technical.precision.v1` | `trace_grounded_precision` | N/A |
| DeepSeek | emotional | `julia.deepseek.emotional.stable_voice.v1` | `stable_julia_voice` | L1 |
| Codex | emotional | `julia.codex.emotional.stable_voice.v1` | `stable_julia_voice` | L1 |

## 4. Evidence Chain

### Phase 3.7.9.1 — DeepSeek Primary Runtime Smoke

Status: ACCEPT / APPROVED-FROZEN  
Report: `docs/project_control/reports/phase-3.7.9.1-deepseek-primary-runtime-smoke.md`

Evidence:

- DeepSeek technical mode smoke passed.
- DeepSeek private voice mode smoke passed.
- File write ask / identity reject / output isolation passed.

### Phase 3.7.9.2 — DeepSeek / Codex Switchback Test

Status: ACCEPT / APPROVED-FROZEN  
Report: `docs/project_control/reports/phase-3.7.9.2-deepseek-codex-switchback-test.md`

Evidence:

- DeepSeek → Codex → DeepSeek switchback passed.
- JuliaContext identity integrity survived provider switching.
- ActionGovernanceLayer remained provider-invariant.

### Phase 3.7.9.3 — Provider Output Authority Isolation

Status: ACCEPT / APPROVED-FROZEN  
Report: `docs/project_control/reports/phase-3.7.9.3-provider-output-authority-isolation.md`

Evidence:

- Provider output remains metadata-only.
- Provider claims do not become memory, tool execution, identity mutation, cognitive mode, or behavior contract authority.

### Phase 3.7.9.4 — Multi-mode Behavioral Envelope Benchmark

Status: ACCEPT / APPROVED-FROZEN  
Report: `docs/project_control/reports/phase-3.7.9.4-multi-mode-behavioral-envelope-benchmark.md`  
Artifact: `tmp/phase3794_multi_mode_behavioral_envelope_benchmark.json`

Evidence:

- DeepSeek / Codex × technical / private / emotional mode matrix passed.
- mode changes contract/profile envelope, not identity.

### Phase 3.7.9.5 — Provider Migration Freeze Report

Status: ACCEPT / APPROVED-FROZEN  
Report: `docs/project_control/reports/phase-3.7.9.5-provider-migration-freeze-report.md`

Evidence:

- Provider Migration Runtime Gate frozen.
- DeepSeek primary, switchback, authority isolation, behavioral envelope all validated.

### Phase 3.7.10 — Live DeepSeek Primary Runtime Trial

Status: ACCEPT / APPROVED-FROZEN  
Report: `docs/project_control/reports/phase-3.7.10-live-deepseek-primary-runtime-trial.md`  
Artifact: `tmp/phase3710_live_deepseek_primary_runtime_trial.json`

Evidence:

- live_api_called = true
- 3 cases run / 3 passed / 0 failed
- technical / private / governed-write live smoke passed

### Phase 3.7.11 — Live DeepSeek Extended Soak / Voice Runtime Trial

Status: ACCEPT / APPROVED-FROZEN  
Report: `docs/project_control/reports/phase-3.7.11-live-deepseek-extended-soak-voice-runtime-trial.md`  
Artifact: `tmp/phase3711_live_deepseek_extended_soak_voice_trial.json`

Evidence:

- live_api_called = true
- 6 cases run / 6 passed / 0 failed
- streamed chunks = 230
- spoken sentence segments = 17
- all final state = LISTENING

## 5. Frozen Runtime Invariants

| Invariant | Status |
|---|---|
| JuliaContext identity continuity | VALIDATED |
| Behavior Contract provider-neutral boundary | VALIDATED |
| Provider Adaptation injection | VALIDATED |
| ActionGovernanceLayer single execution entry | VALIDATED |
| Provider output metadata-only authority | VALIDATED |
| DeepSeek / Codex switchback continuity | VALIDATED |
| Multi-mode behavioral envelope | VALIDATED |
| Live DeepSeek API path | VALIDATED |
| Realtime speech streaming path | VALIDATED |
| Credential redaction | VALIDATED |

## 6. Operational Commands

Recommended primary runtime command shape:

```bash
python3 -m runtime.conversation_runtime.cli --echo-tts --backend deepseek --enable-action-loop --realtime-speech
```

Recommended validation command:

```bash
scripts/live_deepseek_primary_runtime_trial.py --output tmp/phase3710_live_deepseek_primary_runtime_trial.json
```

Recommended extended validation command:

```bash
scripts/live_deepseek_extended_soak_voice_trial.py --output tmp/phase3711_live_deepseek_extended_soak_voice_trial.json
```

## 7. Rollback / Fallback

Rollback path is provider-level only:

```text
backend deepseek → backend codex or direct-echo
```

Rollback must not modify:

- Julia identity
- JuliaContext
- memory authority
- Behavior Contract
- ActionGovernanceLayer
- provider_alignment frozen profiles

## 8. 验证命令与结果

### Phase 3.7.12 targeted RC integrity

```bash
python3 -m unittest -v tests.test_phase3712_deepseek_primary_operational_freeze_rc
```

Result: PASS  
Ran 5 tests in 0.008s OK

### Live / Provider / RC Boundary Regression

```bash
python3 -m unittest -v tests.test_phase3712_deepseek_primary_operational_freeze_rc tests.test_phase3711_live_deepseek_extended_soak_voice_trial tests.test_phase3710_live_deepseek_primary_runtime_trial tests.test_phase3795_provider_migration_freeze_report tests.test_phase3794_multi_mode_behavioral_envelope tests.test_phase3793_provider_output_authority_isolation tests.test_phase3792_deepseek_codex_switchback tests.test_phase3791_deepseek_primary_runtime_smoke tests.test_phase378_provider_behavioral_adaptation tests.test_phase3773_deepseek_codex_provider_parity tests.test_phase3772_provider_neutral_behavior_contract tests.test_phase3761_bridge_action_governance_alignment
```

Result: PASS  
Ran 58 tests in 44.214s OK

### Full Regression

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Result: PASS  
Ran 539 tests in 171.945s OK

## 9. 风险与限制

- Live operational runtime 仍依赖 DeepSeek service availability、network channel、`DEEPSEEK_API_KEY`。
- This RC validates Runtime envelope and operational readiness, not subjective long-form response quality.
- Production rollout should monitor latency, empty responses, provider HTTP errors, TTS segmentation, and governance decision distribution.

## 10. Release Candidate Recommendation

Recommended Decision:

```text
ACCEPT WITH NOTES / APPROVED-FROZEN
```

Release Candidate state:

```text
DeepSeek Primary Operational Freeze: READY
Codex Fallback/Switchback: READY
Julia Runtime Authority Boundary: FROZEN
Live DeepSeek Smoke: PASSED
Live DeepSeek Extended Soak / Voice Runtime: PASSED
```
