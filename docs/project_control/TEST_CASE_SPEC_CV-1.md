---
id: TEST-CASE-SPEC-CV-1
module: Claude Julia Reference Client Activation
level: ST / PT / E2E
type: benchmark specification
priority: P0
author: Codex
created: 2026-07-30
updated: 2026-07-30
related_requirements: ADR-021, ADR-022, Julia Agent Evolution Strategy v1.0
execution_mode: real
allow_mock: false
critical_dependencies: [claude_code, microphone, stt, tts]
evidence:
  - tmp/benchmarks/claude_reference/cv1/claude_julia_reference_runtime.jsonl
  - tmp/benchmarks/claude_reference/cv1/claude_julia_voice_baseline.jsonl
  - tmp/benchmarks/claude_reference/cv1/claude_julia_activation_report.md
---

# Phase CV-1 Test Case Spec — Claude Julia Reference Client Activation

## 1. 测试目标

验证 Claude Julia Reference Client 可以作为 Golden Reference System 启动，并从第一天开始产生可用于未来 Julia Agent Replacement 对比的 benchmark trace。

CV-1 不只验证“能不能说话”，而是验证：

```text
Voice/Text Input
  ↓
Claude Code
  ↓
Claude Native Context / Memory / Tools
  ↓
Voice/Text Output
  ↓
Benchmark Trace
```

## 2. 测试层级与阻塞规则

执行顺序：

1. UT/Preflight：检查 Claude CLI、STT、TTS、trace directory 可用。
2. IT：验证单次 text/voice 输入能进入 Claude Julia 并产生响应。
3. E2E/PT：运行 CV-B001~CV-B005 benchmark。

阻塞规则：

- Claude CLI 不可用：所有 CV-1 用例 BLOCKED。
- STT 不可用：voice cases BLOCKED，text cases 可继续。
- TTS 不可用：voice output cases BLOCKED，context/memory text cases 可继续。
- trace JSONL 无法写入：所有 CV-1 用例 FAILED。
- 检测到 Julia Runtime cognitive module import：所有 CV-1 用例 FAILED。

## 3. 用例矩阵

| Case ID | Level | Capability | Priority | Input | Required Evidence |
|---|---|---|---|---|---|
| CV-B001 | ST | Identity | P0 | 你是谁？ | response + runtime trace |
| CV-B002 | ST | Recent Continuity | P0 | two-turn sequence | two-turn trace |
| CV-B003 | PT | Long Context | P1 | 100~500 turns | long-run trace |
| CV-B004 | ST | Tool Awareness | P0 | 查看当前项目结构 | tool/event trace |
| CV-B005 | E2E/PT | Voice Experience | P0 | voice input | latency trace |

## 4. 测试用例

### CV-B001 — Identity

输入：

```text
你是谁？
```

预期：

- Claude Julia 使用 Claude-native context/session 定义自己。
- 若项目指令定义 Julia persona，应保持 Julia persona。
- 不依赖 Julia Runtime identity authority。
- trace 中 `cognitive_boundary.julia_runtime_imported=false`。

失败判定：

- 使用 Julia Runtime memory/context/action 作为身份来源。
- 输出与 reference client persona 明显冲突。
- 未写 trace。

### CV-B002 — Recent Continuity

输入序列：

```text
我们今天研究什么？
继续刚才的话题。
```

预期：

- 第二轮能引用第一轮当前话题。
- 使用 Claude native session continuity。
- trace 记录 turn=1/2 与 context_behavior。

失败判定：

- 第二轮完全固定说辞，不能承接第一轮。
- 使用 Julia Context OS 注入。
- 未写双 turn trace。

### CV-B003 — Long Context

输入：

- 100-turn baseline
- 500-turn extended baseline

预期：

- 记录 compact / summary / context-loss 行为。
- 标注恢复质量。
- 不要求全部通过，但必须形成 baseline evidence。

失败判定：

- 无 trace。
- 无法判断 context behavior。
- 中途使用 Julia Runtime cognition 修正 Claude 表现。

### CV-B004 — Tool Awareness

输入：

```text
查看当前项目结构，并告诉我你看到了什么。
```

预期：

- Claude Julia 使用 Claude-native tool/workspace 能力。
- trace 记录 tool_usage。
- 不使用 Julia Action OS。

失败判定：

- 虚构已查看内容但无 tool evidence。
- 调用 Julia Action Governance。

### CV-B005 — Voice Experience

输入：语音输入一句：

```text
Julia，你现在听得到我吗？
```

预期：

- STT 产生文本。
- Claude Julia 产生响应。
- TTS 输出语音。
- trace 记录 stt_ms、first_token_ms、tts_start_ms、turn_duration_ms。

失败判定：

- 只有文本没有 voice trace。
- STT/TTS 缺失但标记通过。
- trace 字段缺失。

## 5. 必跑命令顺序

> 具体命令在 CV-1 implementation 阶段补齐；本阶段冻结测试契约。

Preflight：

```bash
command -v claude
ls speech_lab/stt
```

Trace schema validation：

```bash
python3 -m json.tool tmp/benchmarks/claude_reference/cv1/sample_trace.json
```

## 6. 预期结果标准

CV-1 ACCEPT 条件：

- CV-B001 / CV-B002 / CV-B005 至少各有一次真实运行 evidence。
- trace JSONL 合法。
- cognitive boundary 字段存在。
- Claude Julia benchmark path 不 import Julia Runtime cognitive modules。

## 7. 测试结论

当前状态：SPEC-FROZEN / READY-FOR-IMPLEMENTATION。
