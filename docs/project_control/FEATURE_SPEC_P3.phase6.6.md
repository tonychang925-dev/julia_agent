# FEATURE_SPEC_P3.phase6.6 — Full Voice Cognitive Loop Validation

## Task `P3.phase6.6-T01` — Julia Birth Test v1 Validator

### 1) 目标与边界

目标：新增 voice validation 层，用于验证无 Host Agent 参与时，真实/模拟语音 trace 是否完成 Tony Voice → Julia Runtime → Julia Voice 的完整 cognitive loop。

非目标：

- 不新增 STT/TTS 功能。
- 不调用真实麦克风/扬声器/DeepSeek。
- 不修改 ConversationLoop、TTS、STT 管道。
- 不以自然聊天质量作为本阶段验收；本阶段验证 Embodied Presence trace。

### 2) 子功能分解

#### F-P3.phase6.6-T01-01 VoiceE2EScenario

- 输入：scenario_id、input_text、expected persona/mode/memory topics/latency target。
- 处理逻辑：定义 Julia Birth Test v1 场景契约。
- 输出：VoiceE2EScenario。
- 失败处理：缺省 persona=Julia、user=Tony、latency=2500ms。
- 可观测证据：`tests/test_phase36_voice_cognitive_loop_validation.py::test_tc_phase366_001_identity_voice_trace`。
- 验收映射：`ACPT-P3.6.6-01`。

#### F-P3.phase6.6-T01-02 VoiceTraceValidator

- 输入：VoiceE2EScenario + trace dict。
- 处理逻辑：验证 identity、relationship、host independence、provider、mode、memory、conversation continuity、tts、latency。
- 输出：VoiceTraceValidationResult。
- 失败处理：逐项 errors 标注。
- 可观测证据：`tests/test_phase36_voice_cognitive_loop_validation.py::{test_tc_phase366_001_identity_voice_trace,test_tc_phase366_002_memory_recall_trace,test_tc_phase366_003_conversation_continuity_trace,test_tc_phase366_004_cognitive_mode_trace,test_tc_phase366_005_voice_latency_trace}`。
- 验收映射：`ACPT-P3.6.6-02`。

#### F-P3.phase6.6-T01-03 Host Independence Check

- 输入：voice trace。
- 处理逻辑：拒绝 ClaudeCodeBridge / claude_code bridge；要求 direct_llm/deepseek trace。
- 输出：host_independence check。
- 失败处理：host_independence_check_failed。
- 可观测证据：`tests/test_phase36_voice_cognitive_loop_validation.py::test_tc_phase366_001_identity_voice_trace`。
- 验收映射：`ACPT-P3.6.6-03`。

#### F-P3.phase6.6-T01-04 Latency Validation

- 输入：latency trace，包括 speech_to_text/context_compile/first_chunk/tts_start/time_to_first_voice。
- 处理逻辑：验证 time_to_first_voice_ms <= scenario latency target。
- 输出：latency check。
- 失败处理：latency_check_failed。
- 可观测证据：`tests/test_phase36_voice_cognitive_loop_validation.py::test_tc_phase366_005_voice_latency_trace`。
- 验收映射：`ACPT-P3.6.6-04`。

#### F-P3.phase6.6-T01-05 JuliaBirthTestReport

- 输入：VoiceTraceValidationResult list。
- 处理逻辑：生成 PASS/FAIL markdown 报告。
- 输出：Julia Birth Test v1 report。
- 失败处理：任一 scenario fail 则 overall fail。
- 可观测证据：`tests/test_phase36_voice_cognitive_loop_validation.py::test_tc_phase366_006_birth_test_report_markdown`。
- 验收映射：`ACPT-P3.6.6-05`。

### 3) 接口与契约

新增：

```text
runtime/voice_validation/e2e_scenario.py
runtime/voice_validation/voice_trace_validator.py
runtime/voice_validation/birth_test_report.py
runtime/voice_validation/__init__.py
```

### 4) 测试命令

```bash
python3 -m unittest tests.test_phase36_voice_cognitive_loop_validation
python3 -m unittest discover -s tests
```

### 5) 风险与回滚

风险：本阶段是 trace validator，不代表真实设备链路一定通过；真实麦克风/扬声器需手动 E2E。

回滚：删除 `runtime/voice_validation/` 与 `tests/test_phase36_voice_cognitive_loop_validation.py`。

### 6) 验收映射

- `ACPT-P3.6.6-01` VoiceE2EScenario 契约成立。
- `ACPT-P3.6.6-02` Identity/Memory/Continuity/Mode trace checks 成立。
- `ACPT-P3.6.6-03` Host independence check 成立。
- `ACPT-P3.6.6-04` Voice latency check 成立。
- `ACPT-P3.6.6-05` Birth report 输出成立。
