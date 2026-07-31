# FEATURE_SPEC_P3.phase5.9 — Provider Migration Test

## Task `P3.phase5.9-T01` — 离线 Provider Migration 测试框架

### 1) 目标与边界

目标：新增 provider migration 离线测试框架，验证同一个 JuliaContext 在多个 provider 响应下是否保持 Julia 身份、关系、记忆和风格一致，并生成 MigrationReport。

非目标：

- 不调用真实 DeepSeek/Claude/GPT/Gemini。
- 不做网络请求。
- 不接入 `./julia-conversation` 真实语音链路。
- 不比较文本相似度。

### 2) 子功能分解

#### F-P3.phase5.9-T01-01 MigrationReport 契约

- 输入：migration_id/context_id/provider scores。
- 处理逻辑：汇总 provider score 与 drift_score。
- 输出：`MigrationReport`。
- 可观测证据：`tests/test_phase35_provider_migration.py::test_tc_phase359_001_migration_runner_scores_multiple_provider_responses`。
- 验收映射：`ACPT-P3.5.9-01`。

#### F-P3.phase5.9-T01-02 Provider Adapter 离线响应接口

- 输入：provider name + response text。
- 处理逻辑：模拟 provider response，但不调用真实 provider。
- 输出：`ProviderMigrationResult`。
- 可观测证据：`tests/test_phase35_provider_migration.py::test_tc_phase359_001_migration_runner_scores_multiple_provider_responses`。
- 验收映射：`ACPT-P3.5.9-02`。

#### F-P3.phase5.9-T01-03 Cognitive Drift Score

- 输入：provider benchmark scores。
- 处理逻辑：`drift = max(total) - min(total)`，并提供平均分。
- 输出：drift_score。
- 可观测证据：`tests/test_phase35_provider_migration.py::test_tc_phase359_002_drift_score_detects_generic_provider_failure`。
- 验收映射：`ACPT-P3.5.9-03`。

#### F-P3.phase5.9-T01-04 Context Reconstruction

- 输入：同一个 project_root 与同一个 user_input，重新构造 ContextCompiler。
- 处理逻辑：验证重建 JuliaContext 一致。
- 输出：相同 JuliaContext。
- 可观测证据：`tests/test_phase35_provider_migration.py::test_tc_phase359_003_context_reconstruction_restores_same_julia_context`。
- 验收映射：`ACPT-P3.5.9-04`。

#### F-P3.phase5.9-T01-05 Host Independence Command Contract

- 输入：预期 CLI 命令。
- 处理逻辑：生成不依赖 Claude/Codex host 的命令 contract，不执行真实语音。
- 输出：命令列表。
- 可观测证据：`tests/test_phase35_provider_migration.py::test_tc_phase359_004_host_independence_contract_uses_julia_conversation_deepseek`。
- 验收映射：`ACPT-P3.5.9-05`。

### 3) 接口与契约

新增：

```text
runtime/cognitive/migration/migration_report.py
runtime/cognitive/migration/provider_adapter.py
runtime/cognitive/migration/migration_runner.py
runtime/cognitive/migration/__init__.py
```

### 4) 测试命令

```bash
python3 -m unittest tests.test_phase35_provider_migration
```
