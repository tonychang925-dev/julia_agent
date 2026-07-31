# Phase 3.6.6.2 — Birth Test Rework Report

## 1. 目标与范围

基于 `tmp/julia_birth_v2.log` 的 Partial PASS 结果，本阶段只修复三个阻塞 Birth Test 认证的问题：

1. Cognitive Mode Arbitration 被 `recent_cognitive_mode=engineering_collaboration` 过度锁定。
2. Context Quality 将 `conversation_context.recent_turns[*].turn_id` 判为 runtime contamination。
3. ASR 对 Julia/Tony 专名的真实误识别未覆盖：`教练`、`助力了助力呀`、`认识从`。

## 2. 变更文件清单

- `runtime/cognitive/arbitration/context_arbitrator.py`
  - 新增轻量 Conversation Understanding v1：情绪表达优先进入 `emotional_support`；关系/亲密连续表达优先进入 `private_voice_continuity`。
  - 显式语义意图优先级高于 recent mode carryover。

- `runtime/cognitive/context_compiler/context_compiler.py`
  - 将当前 `user_input` 注入 `ArbitrationContext.user_intent`，供 Arbitration 执行语义判断。

- `runtime/cognitive/context_validation/validator.py`
  - 允许 `context.conversation_context.recent_turns[*].turn_id` 作为 Conversation Continuity 内部顺序元数据。
  - 仍禁止 provider/backend/model/latency/session_id 等 RuntimeEnvelope 泄漏。

- `stt/speech_lab_stt.py`
  - 扩展 identity entity proper-noun normalization：
    - `教练...` → `Julia...`
    - `助力了助力呀...` → `Julia...`
    - `认识从。` → `认识Tony。`

- `tests/test_phase366_birth_rework.py`
  - 新增 4 条回归测试覆盖上述问题。

## 3. 验证命令与结果

```bash
python3 -m unittest tests/test_phase366_birth_rework.py
python3 -m unittest discover -s tests
```

结果：

```text
Ran 224 tests in 12.427s
OK
```

## 4. 风险与限制

- ASR 归一化仍限定在 identity proper nouns，不扩展到私密/情绪/任务关键词。
- `turn_id` 只在 `conversation_context.recent_turns[*]` 路径允许，不放宽其他 runtime contamination 规则。
- 本阶段不做 TTS latency 优化、不做 Action Runtime。

## 5. 建议复测命令

```bash
./julia-conversation --backend deepseek --real-voice --real-voice-turns 4 \
  --realtime-speech --conversation-tts-engine elevenlabs-stream --trace \
  --auto-stop-ms 900 --max-duration-ms 5000 --stt-timeout 8 \
  --stt-retries 0 --stt-empty-limit 2 \
  2>&1 | tee tmp/julia_birth_v3.log
```

重点检查：

- `今天有点累` → `emotional_support`
- `情感模式` / `情人` → `private_voice_continuity`
- `context_quality.passed == True`
- `identity_integrity.host_dependency == False`
- `grep -n "ClaudeCodeBridge\|claude_code" tmp/julia_birth_v3.log` 无输出
