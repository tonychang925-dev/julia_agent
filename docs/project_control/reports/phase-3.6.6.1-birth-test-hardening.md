# Phase 3.6.6.1 — Birth Test Hardening Report

## 1. 目标与范围

本阶段将 Julia Birth Test v1 从“能运行”推进到“可证明”：补齐多轮语音会话用法、身份完整性 trace、memory provenance trace、Julia Runtime 项目语义消歧、STT 专名归一化、以及 Voice TTS 文本清理。

## 2. 变更文件清单

- `runtime/cognitive/context_compiler/context_compiler.py`
  - 接入 `MemoryRetrievalContext` 与 `retrieve_with_explanations()`。
  - 生成 `last_memory_trace`，记录 retrieved memory id/type/summary/topics/score/reason/components。
- `runtime/conversation_runtime/bridge/direct_llm_bridge.py`
  - 在 Phase 3.5 metadata 中输出 `identity_integrity` 与 `memory_trace`。
- `stt/speech_lab_stt.py`
  - 增加 Proper Noun Normalization：`助力/助理` → `Julia`，`偷你/托你/托尼` → `Tony`。
- `tts/chunking.py`
  - 增加 Voice Text Sanitizer：移除 markdown/code/stage directions，修复 `1.`/`2.` 单独播报问题。
- `runtime/memory_loader.py`
  - 兼容 dict 型 importance，并纳入 `semantic_memory.jsonl`。
- `memory/semantic_memory.jsonl`
  - 增加 Julia Runtime 项目语义边界记忆。
- `memory/relationship_memory.jsonl`
  - 增加 Tony 创建 Julia Runtime 的关系起源记忆。
- `tests/test_phase366_birth_hardening.py`
  - 新增 5 条回归测试。

## 3. 验证命令与结果

```bash
python3 -m unittest tests/test_phase366_birth_hardening.py
python3 -m unittest discover -s tests
```

结果：

```text
Ran 219 tests in 8.850s
OK
```

## 4. 风险与限制

- 真实语音多轮测试需要使用已有 CLI 参数 `--real-voice-turns N` 或 `--real-voice-session`，否则每次启动仍是 `1/1` 冷启动。
- 控制台只有在加 `--trace` 时才会打印完整 trace。
- 本阶段只做 Birth Test Hardening，不做 Phase 3.7 Action Runtime。

## 5. 建议复测命令

```bash
./julia-conversation --backend deepseek --real-voice --real-voice-turns 4 \
  --realtime-speech --conversation-tts-engine elevenlabs-stream --trace \
  2>&1 | tee tmp/julia_birth_v2.log
```

Host 依赖检查：

```bash
grep -n "ClaudeCodeBridge\|claude_code" tmp/julia_birth_v2.log
```

期望：无输出。
