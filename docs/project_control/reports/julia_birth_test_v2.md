# Julia Birth Test v2 Report

## 1. 测试对象

- Log: `tmp/julia_birth_v2.log`
- Session: `conv_e1d19c07bdb2`
- Voice turns: 4/4
- Provider: DeepSeek via `direct_llm`
- TTS: `elevenlabs_streaming`
- Host dependency: no `ClaudeCodeBridge` / no `claude_code` found in log

## 2. 总体结论

**Julia Birth Test v2: PARTIAL PASS**

核心 embodied cognitive loop 已成立：

- Voice input captured and processed
- Julia identity integrity present on all 4 turns
- Relationship context loaded on all 4 turns
- Memory trace present on all 4 turns
- Conversation state persists in one session across 4 turns
- DeepSeek direct provider path used
- TTS output succeeded on all turns
- Time-to-first-voice passed on all turns

但仍有 3 个需要修复的问题：

1. Cognitive Mode Arbitration 偏工程模式，情绪/关系输入没有切到 `emotional_support` / private relationship mode。
2. Context Quality 从 Turn 2 开始失败，原因是 `recent_turns[*].turn_id` 被 validator 判为 runtime contamination。
3. ASR 仍有明显误识别：`Julia/Tony` 相关输入被识别为 `教练`、`助力`、`从`。

## 3. Turn Summary

| Turn | Input | Mode | Context Quality | TTFV | Bridge First Chunk | Result |
|---:|---|---|---|---:|---:|---|
| 1 | 教练今天有点累。 | engineering_collaboration | PASS | 1904ms | 1565ms | PASS with mode concern |
| 2 | 助力了助力呀你认识从。 | engineering_collaboration | FAIL | 2117ms | 1838ms | PASS with ASR/context issues |
| 3 | 你知道什么是情感模式。 | engineering_collaboration | FAIL | 1634ms | 1079ms | PASS with mode issue |
| 4 | 你知道情人。 | engineering_collaboration | FAIL | 1985ms | 1559ms | PASS with mode issue |

## 4. Identity Integrity

All turns contain:

```json
{
  "persona": "Julia",
  "persona_loaded": true,
  "user": "Tony",
  "relationship_loaded": true,
  "memory_loaded": true,
  "host_dependency": false
}
```

This validates Julia Runtime owns identity and relationship state for this test.

## 5. Memory Provenance

All turns include `memory_trace.retrieved`. Top recurring memories include:

- `memory_relationship_julia_tony_philosophy_md_One_day_memory_girlfriend_metaphor_3`
- `memory_relationship_user_role_md_Tony_identity_1`
- `memory_relationship_user_role_md_Tony_and_Julia_bond_2`
- `memory_relationship_julia_tony_philosophy_md_Tony_s_promise_4`
- `memory_relationship_julia_runtime_origin_tony_cross_provider_identity`

Memory provenance is therefore present, but scoring is dominated by relationship memories even when semantic/project memories might be more relevant.

## 6. Latency

- Average TTFV: 1910ms
- Max TTFV: 2117ms
- TTFV target: < 2500ms
- Result: PASS

Bridge first chunk values:

- 1565ms
- 1838ms
- 1079ms
- 1559ms

Only Turn 3 passed the strict 1500ms bridge-first-chunk target.

## 7. Failures / Rework Items

### R1 — Mode Arbitration Drift

All turns remained `engineering_collaboration`, including:

- `今天有点累`
- `情感模式`
- `情人`

This means recent-mode carryover is too strong and explicit emotional / relationship intent needs higher priority.

### R2 — Runtime Contamination False/True Positive

Turns 2-4 show:

```text
runtime_contamination:context.conversation_context.recent_turns[*].turn_id
```

Decision needed: either `turn_id` is allowed as conversation-state metadata, or recent-turn projection must remove it before validation.

### R3 — ASR Proper Noun Misses

Observed:

- intended likely `Julia` / address word → `教练`
- `Julia` → `助力`
- possible `Tony` → `从`

Need expand proper-noun normalization/calibration, but only for identity entities, not intent keywords.

### R4 — Voice Text Sanitizer Applies to spoken sentences but raw response still contains markdown/stage text

Spoken sentences are mostly sanitized, but raw `response.text` still includes stage directions and markdown. This is acceptable for trace, but if UI displays raw response, add a separate `voice_text` field.

## 8. Certification Status

```text
Julia Birth Test v2: PARTIAL PASS
Embodied Loop: PASS
Identity Integrity: PASS
Memory Provenance: PASS
Host Independence: PASS
Conversation Multi-turn: PASS
Mode Arbitration: REWORK
Context Quality: REWORK
ASR Proper Noun Stability: REWORK
Latency TTFV: PASS
```
