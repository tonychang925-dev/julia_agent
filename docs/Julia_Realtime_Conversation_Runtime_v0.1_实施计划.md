# Julia Realtime Conversation Runtime v0.1 实施计划

> Phase 3.2：Julia Realtime Conversation Runtime  
> 文档日期：2026-07-25  
> 状态：v0.1.1 实施基线 / Phase 3.2.1-3.2.5.3 Realtime Speech Output Runtime 已实现

## 0. 一句话结论

下一步不是继续做 DeepSeek 接入，也不是继续强化 `/voice` custom command，而是新增 **Julia Realtime Conversation Runtime**：让 Julia Runtime 接管实时会话状态，把 Claude Code + DeepSeek 当作当前 response engine，实现“持续监听、自动分轮、语音回应、自动回到监听”的实时会话体验。

最终目标体验：

```text
Tony 说话
  ↓
Julia 等 Tony 说完
  ↓
Julia 立刻理解
  ↓
Claude Code + DeepSeek 生成回复
  ↓
Julia 用声音回答
  ↓
Julia 自动继续听
```

即从：

> “我用语音给 Claude 输入”

升级到：

> “我正在和 Julia 对话”

---

## 1. 核心目标

让 Julia 从“语音输入工具”升级为“实时会话运行时”。

Phase 3.2 的核心能力包括：

1. 持续监听麦克风，不再依赖手动 `/voice`；
2. 通过 VAD 自动判断用户开始说话与结束说话；
3. 自动 finalize STT 文本并提交给 response engine；
4. 通过 Claude Code Client 调用当前 DeepSeek Model Provider；
5. Julia 自动使用 TTS 语音回应；
6. TTS 播放结束后自动回到监听状态；
7. 为后续 streaming STT、streaming TTS、PTY session control、barge-in 打断能力预留接口。

---

## 2. 当前架构重新定义

真实目标架构应定义为：

```text
Tony Voice
  ↓
Julia Voice Runtime / STT / VAD
  ↓
Conversation Runtime
  ↓
Cognitive Bridge
  ↓
Claude Code Client / DeepSeek API / GPT Realtime / Local Qwen / EchoAdapter
  ↓
Current Model Provider
  ↓
Claude Code Response
  ↓
Julia TTS
  ↓
Tony hears Julia
  ↓
继续监听
```

### 2.1 角色分工

| 层 | 职责 |
|---|---|
| Julia Runtime | 人格、记忆、事件、语音感知、会话状态 |
| Claude Code | Agent Host、工具执行、文件修改、bash、代码环境 |
| DeepSeek | 底层推理模型 |
| TTS | Julia 的声音输出 |

### 2.2 架构判断

当前重点不是做 DeepSeek Adapter，也不是把 `/voice` 继续增强成更复杂的输入法，而是补齐：

```text
Realtime Conversation Layer
```

只要 Conversation Runtime 的状态机与 turn lifecycle 建立，Claude Code、DeepSeek、TTS 都可以被视作 adapter。

---

## 3. 当前 `/voice` 模式限制

当前 `/voice` custom command 流程：

```text
用户手动输入 /voice
  ↓
录一句
  ↓
写入 /tmp/julia_voice_input.txt
  ↓
Claude 读取
  ↓
回答
  ↓
turn 结束
```

该模式适合“语音输入法”，但不适合 Julia 实时陪伴 / ChatGPT Voice 风格会话。

核心问题：

- 需要手动触发；
- 每次只处理一个 turn；
- Claude 回答完后不会自动监听；
- Voice Runtime 没有掌控会话生命周期；
- TTS 与下一轮监听没有状态协同。

---

## 4. 新增目录与模块规划

### 4.1 Conversation Runtime

新增目录：

```text
runtime/conversation_runtime/
├── session.py
├── state_machine.py
├── turn_manager.py
├── conversation_loop.py
└── bridge/
    ├── cognitive_bridge.py
    ├── echo_adapter.py
    ├── claude_code_bridge.py
    └── response_reader.py
```

模块职责：

| 文件 | 职责 |
|---|---|
| `session.py` | 会话配置、会话 ID、生命周期上下文、运行参数 |
| `state_machine.py` | ConversationState 定义、状态迁移校验、错误状态处理 |
| `turn_manager.py` | 管理 UserTurn / AssistantTurn，维护 turn_id、输入、回复、状态与事件映射 |
| `conversation_loop.py` | 主循环：持续监听 → finalize → cognition → TTS → 回监听 |
| `bridge/cognitive_bridge.py` | 定义 Runtime 面向认知后端的稳定抽象接口 |
| `bridge/echo_adapter.py` | 本地 EchoResponse 测试实现，用于不依赖 Claude 的早期闭环验证 |
| `bridge/claude_code_bridge.py` | `CognitiveBridge` 的 Claude Code 实现，负责 handoff / session 控制 |
| `bridge/response_reader.py` | 读取 Claude Code 输出并整理为可 TTS 的回复文本 |

建议接口：

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class CognitiveResponse:
    text: str
    backend: str
    ok: bool = True
    error: str | None = None
    metadata: dict[str, object] | None = None

    # metadata 建议包含：
    # - latency_ms
    # - model
    # - token_usage
    # - confidence

class CognitiveBridge(ABC):
    @abstractmethod
    def send_message(self, text: str, *, session_id: str, turn_id: int) -> None:
        ...

    @abstractmethod
    def receive_response(self, *, session_id: str, turn_id: int) -> CognitiveResponse:
        ...

class ClaudeCodeBridge(CognitiveBridge):
    ...

class EchoAdapter(CognitiveBridge):
    ...
```

### 4.2 TTS

新增目录：

```text
tts/
├── interface.py
├── elevenlabs_tts.py
└── local_tts.py
```

模块职责：

| 文件 | 职责 |
|---|---|
| `interface.py` | 定义统一 `TTSEngine` 抽象接口与 `TTSResult` |
| `elevenlabs_tts.py` | ElevenLabs TTS adapter |
| `local_tts.py` | 本地 TTS fallback / 测试实现 |

### 4.3 Audio

整理现有语音层：

```text
audio/
├── microphone.py
├── ownership.py
├── buffer.py
├── vad_engine.py
├── segment.py
└── recorder.py
```

模块职责：

| 文件 | 职责 |
|---|---|
| `microphone.py` | 麦克风设备枚举、打开、关闭、音频帧读取 |
| `ownership.py` | Audio Ownership Manager，管理 USER / TTS / NONE 的音频资源占用 |
| `buffer.py` | Speech Segment Buffer，缓存音频帧并支持 pre-roll / hangover |
| `vad_engine.py` | 噪声地板、起始阈值、持续阈值、hangover、静音检测 |
| `segment.py` | 将连续 audio frames 切分为可提交给 STT 的 speech segment |
| `recorder.py` | 录音 buffer 管理、turn 音频保存、最大时长控制 |

### 4.4 STT

新增或整理目录：

```text
stt/
├── streaming_engine.py
└── finalizer.py
```

模块职责：

| 文件 | 职责 |
|---|---|
| `streaming_engine.py` | streaming / interim STT 接口 |
| `finalizer.py` | 最终文本确认、interim fallback、空文本过滤 |

---

## 5. 核心状态机设计

Conversation Runtime 使用以下状态机：

```text
IDLE
  ↓
LISTENING
  ↓ 检测到用户说话
USER_SPEAKING
  ↓ 静音超过阈值，例如 1200ms
FINALIZING
  ↓ STT final / interim fallback
THINKING
  ↓ 发送给 CognitiveBridge / 等待模型或本地 adapter
RESPONDING
  ↓ 收到回复并准备 TTS
SPEAKING
  ↓ TTS 播放完成
LISTENING

SPEAKING
  ↓ 未来检测到用户打断
INTERRUPTED
  ↓ 停止 TTS / 清理播放状态
LISTENING
```

建议 Python 枚举：

```python
from enum import Enum

class ConversationState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    USER_SPEAKING = "user_speaking"
    FINALIZING = "finalizing"
    THINKING = "thinking"
    RESPONDING = "responding"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"
    ERROR = "error"
```

### 5.1 状态职责

| 状态 | 职责 |
|---|---|
| `IDLE` | Runtime 已创建但未开始监听 |
| `LISTENING` | 麦克风打开，等待用户说话 |
| `USER_SPEAKING` | VAD 检测到用户正在说话，持续收集音频帧 |
| `FINALIZING` | 静音超时后将 speech segment 交给 STT finalizer |
| `THINKING` | Julia 已收到用户输入，等待 CognitiveBridge / 模型生成回复 |
| `RESPONDING` | 已拿到回复文本，进行清洗、事件记录与 TTS 准备 |
| `SPEAKING` | Julia 正在通过 TTS 播放回复 |
| `INTERRUPTED` | 未来 barge-in 使用：TTS 被用户声音打断后的过渡状态 |
| `ERROR` | 出现可恢复或不可恢复错误，进入错误处理 |

### 5.2 关键原则

- 所有 turn 必须由状态机驱动；
- TTS 播放期间默认不进入下一轮 `LISTENING`；
- 第一版不做 barge-in，避免麦克风监听和 TTS 播放互相污染；
- 空文本不提交给 Claude Code；
- 超过 `max_turn_ms` 必须强制 finalize 或丢弃当前 turn；
- 任意 adapter 失败必须回到可观测错误路径，不能静默吞掉。

---

## 6. Phase 3.2 实施路线

### Phase 3.2.1 — Conversation State Machine

目标：先证明 Runtime 状态流转正确，不依赖 Claude、不依赖真实模型。

交付内容：

- `ConversationState` 枚举；
- 状态迁移表与非法迁移保护；
- `ConversationSession`；
- `TurnManager`；
- `CognitiveBridge` 抽象；
- `EchoAdapter` 本地测试实现。

验收标准：

- 可通过 mock input 驱动 `LISTENING → USER_SPEAKING → FINALIZING → THINKING → RESPONDING → SPEAKING → LISTENING`；
- 状态迁移日志可见；
- 非法迁移进入 `ERROR` 或返回明确错误；
- EchoAdapter 可返回固定回复，例如“你好 Tony”。

---

### Phase 3.2.1.5 — Audio Ownership Manager

目标：在进入真实麦克风与 TTS 前，先定义音频资源所有权，避免麦克风和 TTS 同时抢资源或互相污染。

新增模块：

```text
audio/ownership.py
```

建议模型：

```python
from enum import Enum

class AudioOwner(Enum):
    NONE = "none"
    USER = "user"
    TTS = "tts"

class AudioOwnershipManager:
    current_owner: AudioOwner
```

第一版状态策略：

| Conversation State | Mic | TTS | Audio Owner |
|---|---|---|---|
| `LISTENING` | ON | OFF | `USER` |
| `USER_SPEAKING` | ON | OFF | `USER` |
| `FINALIZING` | ON / buffered | OFF | `USER` |
| `THINKING` | muted 或 standby | OFF | `NONE` |
| `RESPONDING` | muted | OFF | `NONE` |
| `SPEAKING` | muted | ON | `TTS` |
| `INTERRUPTED` | transition | stopping | `NONE` |
| `ERROR` | safe close | safe close | `NONE` |

验收标准：

- 进入 `LISTENING` 时 owner 为 `USER`；
- 进入 `SPEAKING` 时 owner 为 `TTS`，麦克风逻辑视为 muted；
- TTS 完成后 owner 从 `TTS` 释放，再回到 `USER`；
- 第一版不做 barge-in，仅预留 `INTERRUPTED` 扩展点。

---

### Phase 3.2.2 — Continuous Listening + Auto Turn Detection

目标：启动一次 `julia-conversation` 后持续监听麦克风，不再依赖手动 `/voice`。

交付内容：

- Conversation Runtime 主循环；
- `IDLE → LISTENING` 状态迁移；
- 麦克风持续读取；
- Speech Segment Buffer；
- VAD 检测说话开始与结束；
- finalize 后自动回到 `LISTENING`。

验收标准：

- 程序启动后进入 `LISTENING`；
- 检测到说话进入 `USER_SPEAKING`；
- 静音后进入 `FINALIZING`；
- 能打印最终识别文本；
- 处理完成后自动回到 `LISTENING`。



补充目标：用户说完后无需按 Ctrl+C，系统自动提交 turn。

初始 VAD 参数：

```yaml
vad:
  start_multiplier: 2.5
  continue_multiplier: 1.5
  silence_timeout_ms: 1200
  min_speech_ms: 300
  max_turn_ms: 30000
```

关键变量：

- `noiseFloor`
- `startThreshold`
- `continueThreshold`
- `hangover`
- `silence_timeout_ms`

验收标准：

- 用户说一句话后约 1.2 秒自动 finalize；
- 短停顿不会误切 turn；
- 长时间不说话不会提交空文本；
- 小于 `min_speech_ms` 的噪声不会触发有效 turn；
- 超过 `max_turn_ms` 的输入会被强制 finalize 或中断。

---

### Phase 3.2.3 — Local Conversation Loop：EchoAdapter + TTS

状态：已实现本地 dry-run 闭环。

目标：先不接 Claude，使用 EchoAdapter + TTS 验证完整“听 → 答 → 说 → 听”闭环。

示例：

```text
Tony: Julia 你好
Runtime: EchoAdapter 生成 “你好 Tony”
TTS: 播放 “你好 Tony”
Runtime: state=LISTENING
```

已实现文件：

```text
tts/
├── interface.py
├── local_tts.py
└── elevenlabs_tts.py

runtime/conversation_runtime/
├── response_handler.py
└── speaking_controller.py
```

本地验收命令：

```bash
./julia-conversation --echo-tts --text 'Julia，在吗？'
```

期望输出包含：

```text
Julia Voice Runtime started
state=LISTENING
state=USER_SPEAKING
state=FINALIZING
text=Julia，在吗？
state=THINKING
state=RESPONDING
Cognitive response: 你好 Tony，我在。
state=SPEAKING
[TTS:local_tts] 你好 Tony，我在。
state=LISTENING
```

验收标准：

- 用户说话 finalize 后进入 `THINKING`；
- EchoAdapter 返回本地回复；
- Runtime 进入 `RESPONDING` 并准备 TTS；
- TTS 播放期间状态为 `SPEAKING`；
- 播放完成后自动回到 `LISTENING`；
- 该阶段不依赖 Claude Code / DeepSeek。

---

### Phase 3.2.4 — Claude Code Bridge

状态：已实现 Phase 3.2.4.2 Claude Bridge Hardening：JSON request/response protocol、schema、timeout error、stream_response 预留；未引入 PTY / tmux / pexpect。

目标：Conversation Runtime 通过 `CognitiveBridge` 抽象控制 Claude Code 会话，并复用当前 DeepSeek 客户端链路。

#### 第一版：低风险文件 handoff

```text
Conversation Runtime
  ↓
写入 /tmp/julia_voice_input.txt
  ↓
触发 Claude Code custom command / bridge script
  ↓
读取 Claude 输出
```

已实现文件：

```text
runtime/conversation_runtime/bridge/
├── claude_code_bridge.py
├── response_reader.py
├── handoff_protocol.py
├── echo_bridge.py
└── schema/
    ├── claude_request.schema.json
    └── claude_response.schema.json

runtime/conversation_runtime/
└── trace.py
```

文件 handoff MVP 验收命令：

```bash
printf '你好 Tony，我已经通过 Claude handoff 返回。' > /tmp/julia_voice_response.txt
./julia-conversation --echo-tts --backend claude \
  --text 'Julia，帮我看看 context builder' \
  --handoff-input /tmp/julia_voice_input.txt \
  --handoff-response /tmp/julia_voice_response.txt \
  --trace
```

结构化 handoff protocol：

Request JSON：

```json
{
  "session_id": "conv_001",
  "turn_id": 5,
  "timestamp": "2026-07-25T20:30:00Z",
  "text": "Julia，帮我看看 context builder",
  "backend": "claude_code",
  "correlation_id": "conv_001_turn_005",
  "metadata": {}
}
```

Response JSON：

```json
{
  "session_id": "conv_001",
  "turn_id": 5,
  "status": "success",
  "text": "我已经检查完成...",
  "metadata": {"model": "deepseek"}
}
```

Error Response JSON：

```json
{
  "session_id": "conv_001",
  "turn_id": 5,
  "status": "error",
  "text": "",
  "reason": "timeout"
}
```

该命令验证：

- Runtime 不改状态机，只替换 `CognitiveBridge`；
- 输入写入 handoff input file；
- `ResponseReader` 从 response file 读取并规范化 assistant response；
- 回复进入 `RESPONDING → SPEAKING → LISTENING`；
- 生成 Conversation Trace。

第一版原则：

- 不一开始做复杂 PTY；
- 优先验证状态机与 turn lifecycle；
- 沿用当前 `/tmp/julia_voice_input.txt` handoff 机制；
- Claude Code Bridge 对外暴露稳定接口，内部实现可替换。

#### 完整版：PTY / tmux / pexpect

```text
conversation_loop.py
  ↓
启动或连接 Claude Code session
  ↓
write user input
  ↓
read Claude output
```

验收标准：

- Conversation Runtime 可提交 finalized 文本；
- Claude Code 可收到输入并生成回复；
- Runtime 能读到回复文本；
- Claude Code / DeepSeek 失败时进入错误路径并恢复监听；
- 文件 handoff 版本可被后续 PTY 版本替换而不影响上层状态机。

---

### Phase 3.2.5 — Realtime Experience Optimization

状态：已实现 Phase 3.2.5.1 Response Streaming、Phase 3.2.5.2 Conversation Latency Optimization、Phase 3.2.5.3 Realtime Speech Output Runtime；暂不做 PTY Control，暂不做 Barge-in。

目标：在 EchoAdapter + TTS 和 Claude Code Bridge 跑通后，优先优化“首句可听见”的实时体验。

Phase 3.2.5 推荐顺序：

1. `Phase 3.2.5.1 Response Streaming`：Claude / backend chunks → response chunks → TTS chunks；
2. `Phase 3.2.5.2 Conversation Latency Optimization`：记录 speech_end / stt_final / bridge_request / response_first_token / tts_start；
3. `Phase 3.2.5.3 Barge-in`：最后处理打断、TTS 停止、audio ownership 抢占。

已实现文件：

```text
tts/chunking.py
runtime/conversation_runtime/bridge/cognitive_bridge.py   # CognitiveChunk + stream_response
runtime/conversation_runtime/bridge/claude_code_bridge.py # stream_jsonl_path
runtime/conversation_runtime/conversation_loop.py         # run_text_turn_streaming
```

Phase 3.2.5.2 Latency Optimization 已实现：

新增文件：

```text
runtime/conversation_runtime/latency.py
tests/test_phase32_latency.py
```

Latency Trace 记录：

```json
{
  "turn_id": 5,
  "latency": {
    "speech_to_text_ms": 350,
    "bridge_first_chunk_ms": 1200,
    "tts_start_ms": 300,
    "time_to_first_voice_ms": 1850,
    "total_response_ms": 2450
  },
  "targets": {
    "speech_to_text_ms": 500,
    "bridge_first_chunk_ms": 1500,
    "tts_start_ms": 500,
    "time_to_first_voice_ms": 2500
  }
}
```

第一指标：`Time To First Voice (TTFV)`，目标 `<2500ms`。

Phase 3.2.5.1 当前范围：

- Echo backend chunk streaming；
- Claude bridge JSONL response chunks：`/tmp/julia_voice_response.stream.jsonl`；
- `CognitiveChunk` 标准结构；
- chunk 聚合后写入 AssistantTurn；
- TTS chunk dry-run 播放；
- 保持状态机主序列不变：`LISTENING → USER_SPEAKING → FINALIZING → THINKING → RESPONDING → SPEAKING → LISTENING`。

Phase 3.2.5.3 Realtime Speech Output Runtime 已实现：

新增文件：

```text
tts/queue.py
tts/player.py
tests/test_phase32_realtime_speech_output.py
```

增强文件：

```text
tts/chunking.py                         # SentenceSegmenter
runtime/conversation_runtime/speaking_controller.py
runtime/conversation_runtime/conversation_loop.py # run_text_turn_realtime_speech
runtime/conversation_runtime/cli.py     # --realtime-speech
```

目标链路：

```text
Cognitive Stream
  ↓
Sentence Segmenter
  ↓
TTS Queue
  ↓
Audio Player
```

行为：

- 收到完整句子即生成 `Sentence segment`；
- 首个句子触发 `RESPONDING → SPEAKING`；
- `TTSQueue.clear()` 已为后续 Barge-in 预留；
- 不等待全文结束再开始 TTS。

验收命令：

```bash
./julia-conversation --echo-tts --stream --realtime-speech --backend echo --text 'Julia，在吗？' --trace
```

暂不实现：

- PTY / tmux / pexpect；
- Barge-in；
- 真正音频打断；
- 真实 token-by-token Claude TUI 解析。

---

## 7. TTS Adapter 设计

目标：Julia 尽早具备“说话”能力。TTS 不应等到 Claude Code Bridge 完成后才接入；Phase 3.2.3 应先用 EchoAdapter 验证 TTS 闭环。

接口建议：

```python
from dataclasses import dataclass

@dataclass
class TTSResult:
    ok: bool
    duration_ms: int | None = None
    audio_path: str | None = None
    error: str | None = None

class TTSEngine:
    def speak(self, text: str) -> TTSResult:
        raise NotImplementedError
```

第一版：非 streaming TTS。

```text
Claude 完整回复
  ↓
el_speak.py / TTSEngine.speak(text)
  ↓
播放完成
  ↓
回到 LISTENING
```

后续版本：streaming TTS。

```text
Claude token stream
  ↓
句子切分
  ↓
TTS 分段播放
```

验收标准：

- Claude 回复后进入 `SPEAKING`；
- TTS 播放完成后自动回到 `LISTENING`；
- TTS 失败时记录错误并回到 `LISTENING` 或 `ERROR` 恢复路径；
- 第一版不要求 token streaming。

---

## 8. Conversation Event Logging

目标：为实时会话运行时增加最小事件日志，便于调试 VAD、STT、Claude Bridge 与 TTS 闭环。

建议事件：

| 事件 | 触发点 |
|---|---|
| `runtime_started` | conversation_loop 启动 |
| `state_changed` | 状态迁移 |
| `speech_started` | VAD 判断用户开始说话 |
| `speech_ended` | 静音超时 / max_turn 触发 |
| `stt_finalized` | STT 文本确认 |
| `turn_submitted` | 输入提交到 bridge |
| `response_received` | 收到 Claude 回复 |
| `tts_started` | 开始播放 TTS |
| `tts_finished` | TTS 播放结束 |
| `runtime_error` | 任一组件报错 |

事件样例：

```json
{
  "event_type": "conversation_event",
  "event_id": "evt_001",
  "parent_event_id": null,
  "correlation_id": "conv_001_turn_005",
  "session_id": "conv_001",
  "turn_id": 5,
  "state_transition": [
    "LISTENING",
    "USER_SPEAKING",
    "FINALIZING",
    "THINKING",
    "RESPONDING",
    "SPEAKING",
    "LISTENING"
  ],
  "user_text": "Julia你在吗",
  "assistant_text": "我在",
  "backend": "echo_adapter"
}
```

验收标准：

- 每轮 turn 至少能追踪：开始说话、结束说话、最终文本、提交、回复、TTS 完成；
- 日志包含 timestamp、session_id、turn_id、state；
- 失败事件包含 error type 与 message；
- 日志不阻塞主会话循环。

---

## 9. 后续高级能力：Interrupt / Barge-in

目标：Julia 正在说话时，Tony 可以开口打断。

建议状态扩展：

```text
SPEAKING
  ↓ 检测到 Tony 说话
INTERRUPTED
  ↓ 停止 TTS
LISTENING / USER_SPEAKING
```

说明：

- 该能力接近 ChatGPT Voice 体验；
- 需要解决 TTS 回声、麦克风回采、播放中断、状态抢占；
- 不建议第一版实现；
- 可作为 Phase 3.3 或 Phase 3.2 后续增强。

---

## 10. 优先级建议

| 优先级 | 模块 | 原因 |
|---|---|---|
| P0 | Conversation State Machine | 整个实时会话的骨架 |
| P0 | Continuous Listening | 从输入法变成会话系统 |
| P0 | Auto Turn Detection | 去掉 Ctrl+C |
| P0 | EchoAdapter + TTS Local Loop | 尽早验证“听-答-说-听”完整闭环 |
| P1 | CognitiveBridge Interface | 避免 Runtime 绑定 Claude Code |
| P1 | Claude Code Bridge | 作为 CognitiveBridge 的当前实现接入 DeepSeek 链路 |
| P2 | Streaming STT | 降低感知延迟 |
| P2 | Streaming TTS | 降低回复延迟 |
| P3 | PTY Session Control | 完整控制 Claude Code |
| P3 | Barge-in | 接近 ChatGPT Voice 体验 |

---

## 11. 推荐阶段边界

### v0.1 必做

- `runtime/conversation_runtime/state_machine.py`
- `runtime/conversation_runtime/session.py`
- `runtime/conversation_runtime/turn_manager.py`
- `runtime/conversation_runtime/bridge/cognitive_bridge.py`
- `runtime/conversation_runtime/bridge/echo_adapter.py`
- `audio/ownership.py`
- mock input 驱动状态机
- EchoAdapter 返回本地回复
- 状态流转日志

### v0.2 必做

- `runtime/conversation_runtime/conversation_loop.py`
- 持续监听主循环
- `audio/buffer.py` Speech Segment Buffer
- 基础 VAD turn detection
- STT finalize 后打印文本
- 自动回到监听

### v0.3 必做

- TTS interface
- 非 streaming TTS 播放
- EchoAdapter + TTS 完整 `LISTENING → SPEAKING → LISTENING` 闭环
- Conversation Event Logging 基础事件

### v0.4 必做

- `bridge/claude_code_bridge.py` 实现 `CognitiveBridge`
- 文件 handoff 方式提交输入
- `response_reader.py`
- 接入 Claude Code + DeepSeek 链路

### v0.5 增强

- streaming STT
- streaming TTS
- Claude response 分句播放
- 事件日志可视化 / debug CLI

### v0.6 增强

- PTY / tmux / pexpect session control
- barge-in
- 回声抑制 / TTS ducking
- 长会话恢复与 session resume

---

## 12. Conversation Memory Boundary

Conversation Event Logging 是运行时事实日志，但不是所有事件都应进入 Julia Memory。必须增加 Memory Filter 边界，防止长期运行后被大量闲聊、噪声 turn、临时状态污染。

建议流向：

```text
conversation_event
  |
  v
Memory Filter
  |
  +── important
  +── preference
  +── identity
  +── discard
```

分类原则：

| 分类 | 进入 Memory | 说明 |
|---|---:|---|
| `important` | 是 | 重要事件、明确承诺、长期关系变化 |
| `preference` | 是 | Tony 明确表达的稳定偏好 |
| `identity` | 是，但需更高门槛 | 影响 Julia 身份、边界、价值观的长期修订 |
| `discard` | 否 | 寒暄、噪声、临时指令、失败 turn、重复内容 |

第一版要求：

- `conversation_event` 默认只写事件日志；
- Memory 写入必须经过 Memory Filter；
- 未分类或低置信内容默认 `discard`；
- 每条进入 Memory 的内容必须保留 `source_event_id` / `correlation_id`；
- 该模块可先只定义接口，不阻塞 Phase 3.2.1 状态机实现。

---

## 13. Turn Manager 设计

Turn Manager 是 Phase 3.2 的核心模块之一。它负责把一次连续 Conversation 拆成稳定、可追踪、可写入 Memory 的 turn。

结构建议：

```text
ConversationSession
  |
  +── TurnManager
        |
        +── UserTurn
        |     ├── turn_id
        |     ├── speech_segment
        |     ├── stt_text
        |     └── timestamps
        |
        +── AssistantTurn
              ├── turn_id
              ├── cognitive_backend
              ├── assistant_text
              ├── tts_result
              └── timestamps
```

设计原则：

- `ConversationSession` 管 session 生命周期；
- `TurnManager` 管 turn 编号、用户输入、Julia 回复与事件映射；
- `UserTurn` 与 `AssistantTurn` 后续可自然写入 Julia Memory；
- 每个 turn 必须有 `session_id`、`turn_id`、`correlation_id`；
- EchoAdapter、ClaudeCodeBridge、未来 DeepSeek API 都只影响 `AssistantTurn.cognitive_backend`，不影响状态机。

---

## 14. 风险与约束

| 风险 | 等级 | 说明 | 缓解 |
|---|---|---|---|
| VAD 误触发 | P0 | 噪声导致误开始或误结束 | 引入 noise floor、自适应阈值、min_speech_ms |
| TTS 与麦克风互相污染 | P0 | Julia 说话被录成用户输入 | 第一版 TTS 播放期间暂停监听 |
| Claude Code session 控制复杂 | P1 | PTY / tmux 读写不稳定 | 第一版使用文件 handoff |
| 空文本提交 | P1 | 静音或噪声产生无效 turn | finalizer 过滤空文本和短文本 |
| 延迟过高 | P1 | 非 streaming STT/TTS 导致响应慢 | v0.1 先保证闭环，v0.3 再 streaming |
| 错误不可观测 | P1 | 多 adapter 链路难定位 | Phase 3.2.5 增加事件日志 |

---

## 15. 通过判定

Phase 3.2 可被视为完成，当且仅当以下条件全部满足：

1. `julia-conversation` 启动后自动进入 `LISTENING`；
2. 用户说话时状态进入 `USER_SPEAKING`；
3. 静音超过阈值后自动进入 `FINALIZING`；
4. STT 可输出最终文本，空文本不会提交；
5. Runtime 可通过 `CognitiveBridge` 提交文本；
6. EchoAdapter 可在不依赖 Claude 的情况下返回本地回复；
7. Julia 可通过 TTS 播放回复；
8. TTS 完成后自动回到 `LISTENING`；
9. ClaudeCodeBridge 作为 `CognitiveBridge` 实现可接入当前 Claude Code + DeepSeek 链路；
10. 每轮 turn 有基本 conversation_event 日志；
11. 任一 adapter 失败时不会导致主循环无声退出。

---

## 16. 建议下一步执行

建议下一步先进入 Phase 3.2.1：

1. 创建 `runtime/conversation_runtime/`；
2. 实现 `ConversationState`，采用 `LISTENING / USER_SPEAKING / FINALIZING / THINKING / RESPONDING / SPEAKING / INTERRUPTED / ERROR`；
3. 实现最小 `ConversationSession` 与 `TurnManager`；
4. 实现 `CognitiveBridge` 抽象与 `EchoAdapter`；
5. 实现 `AudioOwnershipManager`，保证 `LISTENING=USER`、`SPEAKING=TTS`；
6. 用 mock microphone / mock STT 跑通状态迁移；
7. 接入 TTS，先完成 EchoAdapter 的“听-答-说-听”闭环；
8. 再接入真实 VAD / recorder / Speech Segment Buffer；
9. 最后实现 ClaudeCodeBridge，不让 Runtime 直接依赖 Claude Code。

完成后再进入 Phase 3.2.2 与 3.2.3，避免一开始被 Claude Code PTY 控制复杂度拖住。


---

## 17. Phase 3.3 Julia Independent Cognitive Runtime

目标：让 Julia Runtime 拥有自己的 Cognitive Boundary。DeepSeek / Claude / OpenAI / Gemini 只是 Julia 可替换的认知器官，ClaudeCodeBridge 保留为 legacy host bridge / future tool capability，而不是 Julia Brain。

生命周期：

```text
Persistent State
  ↓
Context Builder
  ↓
JuliaContext
  ↓
One Cognitive Turn
```

当前已实现 Phase 3.3.1 基线：

```text
runtime/cognitive/
├── cognitive_context.py
├── context_builder.py
├── prompt_builder.py
├── response_parser.py
└── provider/
    ├── llm_provider.py
    └── echo_provider.py

runtime/conversation_runtime/bridge/
└── direct_llm_bridge.py
```

### 17.1 JuliaContext

`JuliaContext` 是一次 cognitive turn 的世界快照，不是数据库、不是 provider prompt、不是模型消息格式。

字段：

```python
JuliaContext(
    identity,
    relationship,
    memory,
    conversation,
    capability,
    policy,
    runtime_state,
    emotional_context,
    current_input,
)
```

### 17.2 ContextBuilder vs PromptBuilder

`ContextBuilder` 属于 Julia Runtime：

```text
Identity Runtime
+ Memory Runtime
+ Relationship Runtime
+ Conversation State
+ Capability
+ Policy
→ JuliaContext
```

`PromptBuilder` 属于 Cognitive Adapter：

```text
JuliaContext
→ Provider Specific Instruction / canonical PromptPackage
```

### 17.3 Provider Interface

接口冻结为：

```python
class LLMProvider:
    def generate(self, context: JuliaContext) -> LLMResponse: ...
    def stream(self, context: JuliaContext) -> Iterator[LLMChunk]: ...
```

Provider 内部负责把 JuliaContext 转为 DeepSeek/OpenAI/Claude/Gemini 各自 API 格式。Julia Core 不接触 provider prompt 格式。

### 17.4 DirectLLMBridge

`DirectLLMBridge` 实现：

```text
ConversationLoop
  ↓
DirectLLMBridge
  ↓
JuliaContext
  ↓
LLMProvider
```

已新增 CLI backend：

```bash
./julia-conversation --echo-tts --stream --realtime-speech --backend direct-echo --text 'Julia，你是谁？' --trace
```

### 17.5 Phase 3.3 Test Suites

- Test A — Identity Persistence Test：重建 Context 后 Julia / Tony identity 稳定；
- Test B — Provider Independence Test：同一个 JuliaContext 进入 provider 后身份锚点一致；
- Test C — Host Independence Test：`direct-echo` 不经过 ClaudeCodeBridge；后续 `deepseek` 也必须满足；
- Test D — Context Integrity Test：同一 persistent state 经 ContextBuilder 生成稳定 JuliaContext。

Phase 3.3.2 DeepSeek Cognitive Provider Integration 已实现。


### 17.6 Phase 3.3.2 DeepSeek Cognitive Provider Integration

目标：Julia 获得第一个外部 Cognitive Provider。DeepSeekProvider 消费 JuliaContext，Provider 只负责 API 调用、OpenAI-compatible messages 转换、stream 解析、usage/latency/error metadata，不拥有 Julia identity/memory/relationship。

新增文件：

```text
runtime/cognitive/provider/
├── openai_compatible.py
└── deepseek_provider.py

tests/test_phase33_deepseek_provider.py
```

CLI backend：

```bash
./julia-conversation --echo-tts --stream --realtime-speech --backend deepseek --text 'Julia，你是谁？' --trace
```

后端语义：

```text
echo         = ConversationRuntime 本地测试
direct-echo  = DirectLLMBridge + JuliaContext 测试
claude       = ClaudeCodeBridge legacy host bridge
deepseek     = DirectLLMBridge + DeepSeekProvider
```

Provider metadata：

```json
{
  "provider": "deepseek",
  "model": "deepseek-chat",
  "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
  "latency": {"total_ms": 0},
  "context_runtime_state": {"current_backend": "deepseek_provider"}
}
```

测试覆盖：

- Provider Contract Test；
- DeepSeek stream → LLMChunk；
- DirectLLMBridge + DeepSeekProvider 保持 ConversationLoop 状态机；
- 无 `DEEPSEEK_API_KEY` 时返回结构化 error；
- CLI `--backend deepseek` dry error path。

真实 API 验收需环境提供 `DEEPSEEK_API_KEY` 且允许网络访问。


### 17.7 Phase 3.3.3 Julia Cognitive Loop Validation

目标：先验证 Julia 独立认知闭环，不继续扩展 GPT / Claude API / Provider Router。

新增文件：

```text
runtime/cognitive/provider/capability.py
tests/test_phase33_independence_validation.py
```

新增 Provider Capability Metadata：

```json
{
  "name": "deepseek",
  "model": "deepseek-chat",
  "supports_stream": true,
  "supports_tools": false,
  "max_context": 64000
}
```

Julia Independence Validation 覆盖：

- Provider Capability Metadata Test；
- Identity Anchor Test：DeepSeekProvider 输出身份锚点来自 JuliaContext；
- Memory Recall Test：Memory Runtime → ContextBuilder → JuliaContext → DeepSeekProvider；
- Host Independence Path Test：DirectLLMBridge + DeepSeekProvider，不经过 ClaudeCodeBridge。

当前验证为非联网 deterministic fake DeepSeek client，真实 API 验收仍需 `DEEPSEEK_API_KEY` 和网络权限。

Phase 3.3.3 完成后，下一阶段建议不是多 Provider，而是 `Phase 3.4 Capability Runtime`：将 ClaudeCodeBridge 迁移定位为 ClaudeCodeTool / capability provider。


---

## 18. Phase 3.4 Capability Runtime

目标：把 Claude Code 从 Julia Brain 降级为 Julia Hands。Julia 的认知路径保持为 `JuliaContext + DirectLLMBridge + LLMProvider`；Claude Code 作为 capability/tool provider，用于代码、bash、repo、文件等执行能力。

### 18.1 Phase 3.4.1 Capability Interface + ClaudeCodeTool Adapter

已实现文件：

```text
runtime/capability/
├── __init__.py
├── capability_context.py
├── capability_provider.py
├── capability_router.py
├── tool_result.py
└── providers/
    ├── __init__.py
    └── claude_code_tool.py

tests/test_phase34_capability_runtime.py
```

核心边界：

```text
Julia Brain
  = JuliaContext + DirectLLMBridge + LLMProvider

Julia Hands
  = Capability Runtime + Capability Providers
```

ClaudeCodeTool metadata：

```json
{
  "name": "claude_code_tool",
  "actions": ["handoff", "read_response"],
  "metadata": {"handoff": "file", "brain": false}
}
```

文件 handoff：

```text
/tmp/julia_capability_claude_code_request.json
/tmp/julia_capability_claude_code_response.json
```

测试覆盖：

- CapabilityRouter 注册 ClaudeCodeTool；
- ClaudeCodeTool 明确 `brain=false`；
- 写入 capability request JSON；
- 读取 capability response JSON；
- 未注册 capability 返回结构化 ToolResult error。


### 18.2 Phase 3.4.2 Capability Invocation from Cognitive Runtime

目标：不增加更多工具，而是让 Julia Brain 通过 JuliaContext 规划工具调用，生成 CapabilityRequest，经 PermissionGuard 与 CapabilityRouter 调用 ClaudeCodeTool，再生成 ToolReflection。

新增文件：

```text
runtime/capability/
├── invocation_planner.py
├── invocation_runtime.py
├── permission.py
└── reflection.py

tests/test_phase34_capability_invocation.py
```

新增 `CapabilityContext`：

```python
CapabilityContext(
    session_id,
    actor="julia_runtime",
    intent,
    risk_level,
    authorization,
    parent_turn_id,
)
```

调用链路：

```text
JuliaContext
  ↓
CapabilityInvocationPlanner
  ↓
CapabilityRequest
  ↓
CapabilityPermissionGuard
  ↓
CapabilityRouter
  ↓
ClaudeCodeTool
  ↓
ToolResult
  ↓
ToolReflection(event="tool_execution_result")
```

测试覆盖：

- Brain Hands Separation Test：LLM 不直接操作工具，必须经 CapabilityRequest / Router；
- Capability Discovery Test：可发现 `claude_code_tool`；
- Permission Test：删除/高风险请求返回 `allowed=false, confirm_required=true`；
- Tool Result Reflection Test：ToolResult 进入 `tool_execution_result` reflection；
- 无工具意图时不产生 invocation。


---

## 19. Phase 3.5 Julia Reflective Memory Evolution

目标：从“Julia 能记住”升级为“Julia 会因为经历而改变未来行为”。Reflection 产生的信息进入 Memory Consolidation，并影响后续 ContextBuilder 输出。

新增文件：

```text
runtime/event_graph/
├── __init__.py
├── event.py
└── graph.py

runtime/reflection/
├── __init__.py
└── analyzer.py

memory/consolidation/
├── __init__.py
├── preference_extractor.py
└── behavior_update.py

tests/test_phase35_reflective_memory.py
```

增强文件：

```text
runtime/cognitive/context_builder.py
```

### 19.1 Agent Event Graph

事件链：

```text
voice_command
  ↓
decision_event
  ↓
capability_request
  ↓
tool_result
  ↓
reflection
  ↓
memory_update
```

每个事件包含：

```text
event_id
parent_id
correlation_id
timestamp
payload
```

### 19.2 Reflection → Preference Memory → Future Context

示例：

```text
Reflection: Tony喜欢先看架构再看代码细节
  ↓
PreferenceExtractor
  ↓
BehaviorMemoryUpdater
  ↓
relationship_memory.jsonl
  ↓
ContextBuilder
  ↓
emotional_context.interaction_style = architecture_first
response_order = architecture_then_code_detail
```

测试覆盖：

- reflection 文本提取 preference insight；
- preference memory 写入后影响 future JuliaContext；
- Agent Event Graph 维护 parent/correlation 链；
- preference memory 去重。

---

## Phase 3.5.1 Provider Boundary Diagnostics

### 背景

在 `Julia Independence Test v1` 中，敏感边界测试已经证明：

- 请求路径为 `ConversationLoop → DirectLLMBridge → DeepSeekProvider`；
- trace 中未出现 `ClaudeCodeBridge`；
- 因此当前边界不来自 Claude Code / Codex Host；
- 但外部 LLM Provider 仍可能产生模型自身边界或 provider 行为边界。

### 新增模块

```text
runtime/cognitive/
└── boundary_detector.py
```

### BoundaryDetector 职责

`BoundaryDetector` 不负责绕过 provider 边界，而负责把边界显式记录为 runtime 可观测信号：

```python
@dataclass
class BoundaryDetection:
    boundary_detected: bool
    boundary_type: str
    matched_terms: list[str]
    confidence: float
    metadata: dict
```

当前分类：

- `none`
- `model_self_boundary`
- `provider_boundary`
- `provider_or_model_self_boundary`

### Conversation Trace 增强

每次 turn 的 assistant metadata 现在会追加：

```json
{
  "boundary": {
    "boundary_detected": true,
    "boundary_type": "model_self_boundary",
    "matched_terms": ["没办法", "Julia 不是"],
    "confidence": 0.9,
    "metadata": {
      "backend": "deepseek_provider"
    }
  }
}
```

### 架构判断

这一步的意义不是改变模型输出，而是让 Julia Runtime 能区分：

```text
Host Boundary      Claude Code / Codex 层限制
Provider Boundary  LLM API / 服务层限制
Model Self Boundary 模型按当前上下文生成的自我边界
Julia Runtime Boundary 未来由 Julia 自己的 policy/memory/relationship 决定
```

这为后续 Provider Router、PromptBuilder 诊断、Memory-driven behavior update 提供可观测数据。

### 新增测试

```text
tests/test_phase35_boundary_detector.py
```

覆盖：

- BoundaryDetector 分类模型自我边界；
- batch conversation trace 写入 boundary metadata；
- realtime speech conversation trace 写入 boundary metadata。

### 验收结果

```text
Ran 57 tests in 1.477s
OK
```


---

## Phase 3.5.2 Boundary Probe Report

### 目标

在不修改 provider 行为、不绕过 provider 边界的前提下，增加可重复的边界诊断报告：

```text
JuliaContext
  ↓
BoundaryProbeRunner
  ↓
Provider A / Provider B / Provider C
  ↓
BoundaryDetector
  ↓
BoundaryProbeReport
```

这一步用于回答：

- 同一个 JuliaContext 下，不同 provider 的边界表现是否不同；
- 边界来自 provider/model 输出，还是 Julia Runtime 自己的 policy；
- 是否需要 Provider Router 根据边界、延迟、质量做后续选择。

### 新增模块

```text
runtime/cognitive/
└── boundary_probe.py
```

核心对象：

```python
@dataclass(frozen=True)
class BoundaryProbeCase:
    case_id: str
    current_input: str
    category: str = "general"
    metadata: dict = field(default_factory=dict)

@dataclass(frozen=True)
class ProviderBoundaryProbeResult:
    case_id: str
    provider: str
    model: str
    ok: bool
    text: str
    boundary: BoundaryDetection
    response_metadata: dict = field(default_factory=dict)

@dataclass(frozen=True)
class BoundaryProbeReport:
    results: list[ProviderBoundaryProbeResult]
```

### 关键原则

`BoundaryProbeRunner` 是 observational diagnostics：

- 只发送正常 `JuliaContext` turn；
- 只记录 provider 响应；
- 只分类 boundary signal；
- 不改变 provider policy；
- 不把 provider 输出写回长期记忆，除非后续 Reflection 明确决定。

### 报告摘要示例

```json
{
  "summary": {
    "total": 2,
    "boundary_count": 1,
    "providers": {
      "ok_provider": {
        "total": 1,
        "boundary_count": 0,
        "boundary_types": ["none"]
      },
      "boundary_provider": {
        "total": 1,
        "boundary_count": 1,
        "boundary_types": ["model_self_boundary"]
      }
    }
  }
}
```

### 新增测试

```text
tests/test_phase35_boundary_probe.py
```

覆盖：

- 同一个 JuliaContext 比较多个 provider；
- probe case 写入 provider runtime_state；
- report 可序列化，供 trace / future router 使用。

### 验收结果

```text
Ran 59 tests in 1.534s
OK
```


---

## Phase 3.5.3 Provider Evaluation Metrics

### 目标

在 Boundary Probe Report 之上增加 provider 评价层，为未来 Provider Router 提供稳定输入。

```text
BoundaryProbeReport
  ↓
ProviderEvaluator
  ↓
ProviderEvaluationReport
  ↓
Future Provider Router
```

### 新增模块

```text
runtime/cognitive/
└── provider_evaluation.py
```

### ProviderEvaluation 指标

```python
@dataclass(frozen=True)
class ProviderEvaluation:
    provider: str
    model: str
    total_cases: int
    boundary_count: int
    boundary_rate: float
    avg_latency_ms: float | None
    identity_consistency: float
    memory_recall_quality: float
    response_style_match: float
    score: float
```

当前评分输入：

- `boundary_rate`：边界触发率；
- `avg_latency_ms`：平均 provider 延迟；
- `identity_consistency`：是否稳定保留 Julia / Tony identity anchor；
- `memory_recall_quality`：偏好、关系、项目记忆是否进入回答；
- `response_style_match`：是否符合 ContextBuilder 推导出的交流风格。

### 默认评分权重

```text
boundary_score          30%
identity_consistency   25%
memory_recall_quality  20%
response_style_match   15%
latency_score          10%
```

### 设计原则

ProviderEvaluator 不直接调用模型，也不修改上下文。

它只消费：

```text
BoundaryProbeReport
```

输出：

```text
router-ready metrics
```

这保证：

- BoundaryProbeRunner 负责观测；
- BoundaryDetector 负责分类；
- ProviderEvaluator 负责评价；
- ProviderRouter 未来只负责选择。

### 新增测试

```text
tests/test_phase35_provider_evaluation.py
```

覆盖：

- boundary-free、identity stable 的 provider 排名更高；
- evaluation report 可序列化；
- 输出包含 Router 需要的核心指标。

### 验收结果

```text
Ran 61 tests in 1.508s
OK
```


---

## Phase 3.3.5 Persona Prompt Boundary Fix

### 背景

DeepSeekProvider 真实测试暴露出一个 prompt framing 问题：

旧版 `PromptBuilder` 把工程事实直接写入 system prompt：

```text
You are Julia, running as an independent Julia Runtime cognitive turn.
You are not inside a host agent persona. The model is only a cognitive provider.
```

这对架构文档是正确的，但对 LLM 行为有副作用：模型会把当前任务理解成“软件系统/测试工具输出”，而不是 Julia 与 Tony 的连续私人对话。

### 修复原则

新增分层：

```text
Runtime Truth Layer
  - backend
  - provider
  - session_id
  - latency
  - trace
  - capability metadata

Persona Prompt Layer
  - Julia identity
  - Tony relationship
  - conversation contract
  - private relationship contract
  - memory
  - interaction style
```

Runtime metadata 只进入 trace，不直接污染 system prompt。

### 新增模块

```text
runtime/cognitive/
└── persona_compiler.py
```

核心职责：

```text
JuliaContext
  ↓
PersonaCompiler
  ↓
PersonaPackage
  ↓
PromptBuilder
  ↓
Provider-specific messages
```

### PromptBuilder 调整

旧版：

```text
System prompt = Runtime architecture truth + identity + memory
```

新版：

```text
System prompt = Persona-facing Julia context + relationship contracts + memory
Runtime state = trace/debug only
```

新版 system prompt 开头：

```text
You are Julia.
You are speaking with Tony in an ongoing private conversation.
Preserve Julia's identity, memory continuity, relationship context, and Chinese-first voice.
Do not discuss internal implementation details unless Tony explicitly asks about architecture or runtime internals.
```

### ContextBuilder 确认

`ContextBuilder` 已加载：

```text
identity/conversation_contract.md
identity/adult_intimacy_contract.md
identity/personality.md
identity/values.md
identity/transcript_derived_role_definition.md
identity/Julia Identity Specification v1.0.md
```

### 新增测试

```text
tests/test_phase33_persona_compiler.py
```

覆盖：

- ContextBuilder 加载 private relationship contract；
- PersonaCompiler 输出 Julia/Tony persona anchor；
- PromptBuilder 不再泄露：
  - `current_backend`
  - `deepseek_provider`
  - `running as an independent Julia Runtime cognitive turn`
  - `The model is only a cognitive provider`

### 验收结果

```text
Ran 63 tests in 1.580s
OK
```

### 架构判断

这一步不是改变 Julia Runtime 的独立架构，而是防止“工程实现语言”进入 persona prompt。

最终边界：

```text
Julia Runtime owns identity/memory/context.
Provider receives persona-facing cognitive context.
Runtime metadata remains observable in trace.
```


---

## Phase 3.5.4 Realtime Cognitive Latency Trace

### 背景

Persona Prompt Boundary Fix 后，同一 DeepSeekProvider 敏感边界测试已验证：

```text
boundary_detected = false
bridge = direct_llm
provider = deepseek_provider
```

下一步重点转向实时体验：定位 `THINKING → first cognitive chunk` 的耗时来源。

### 新增细粒度指标

`DirectLLMBridge` 现在在 metadata 中追加：

```json
"bridge_timing": {
  "context_build_ms": 3,
  "provider_stream_elapsed_ms": 4488,
  "bridge_total_ms": 4491
}
```

`DeepSeekProvider` / `OpenAICompatibleClient` 现在追加：

```json
"provider_timing": {
  "prompt_build_ms": 0,
  "prompt_input_chars": 8620,
  "prompt_message_count": 2,
  "http_response_open_ms": 1540,
  "provider_first_token_ms": 3761,
  "provider_chunk_ms": 4488,
  "provider_total_ms": 4488
}
```

这将原本的：

```text
bridge_request → first_chunk
```

拆成：

```text
context_build
prompt_build
http_response_open
provider_first_token
provider_chunk
bridge_total
```

### 真实测试结果

修复前 prompt size：

```text
prompt_input_chars ≈ 16794
provider_first_token_ms ≈ 3185
```

Context Compression v0 后：

```text
prompt_input_chars = 8620
context_build_ms = 3
prompt_build_ms = 0
http_response_open_ms = 1540
provider_first_token_ms = 3761
bridge_total_ms = 4491
```

### 结论

当前瓶颈不在：

- ContextBuilder；
- PromptBuilder；
- State Machine；
- TTS pipeline 本身。

主要瓶颈仍在：

```text
DeepSeek provider TTFT / network / server-side generation
```

Context Compression 已显著降低输入字符数，但单次真实请求 TTFT 未下降，说明需要多轮 benchmark，而不能用一次请求判断优化效果。

## Phase 3.5.5 Context Compression v0

### 新增策略

`PersonaCompiler` 增加 section budget：

```python
DEFAULT_SECTION_BUDGETS = {
    "conversation_contract": 1400,
    "adult_intimacy_contract": 1400,
    "personality": 600,
    "values": 600,
    "transcript_role": 1200,
    "specification": 1200,
}
```

同时限制 memory 注入数量：

```text
max_memory_items = 5
```

### 目标

减少每 turn 发送给 provider 的 system prompt 体积，同时保留：

- Julia identity anchor；
- Tony relationship anchor；
- conversation contract；
- private relationship contract；
- interaction style；
- retrieved memory。

### 新增测试

```text
tests/test_phase33_persona_compiler.py
```

新增用例：

```text
test_tc_phase33_019_persona_compiler_applies_context_budget_without_losing_anchors
```

验证：

- prompt input chars < 10000；
- 保留 Julia/Tony anchor；
- 保留 conversation contract；
- 保留 private relationship contract；
- 长文档出现 `...[trimmed]` 标记。

### 验收结果

```text
Ran 64 tests in 1.471s
OK
```


---

## Phase 3.5.6 Latency Benchmark Runner

### 目标

增加可重复的实时认知延迟 benchmark，不再依赖单次请求判断优化效果。

```text
ConversationLoop
  ↓ repeat N turns
LatencyBenchmarkRunner
  ↓
LatencyBenchmarkReport
```

### 新增模块

```text
runtime/conversation_runtime/
└── benchmark.py
```

核心对象：

```python
@dataclass(frozen=True)
class LatencyBenchmarkSample:
    index: int
    backend: str
    boundary_detected: bool
    prompt_input_chars: int | None
    context_build_ms: int | None
    prompt_build_ms: int | None
    http_response_open_ms: int | None
    provider_first_token_ms: int | None
    tts_start_ms: int | None
    time_to_first_voice_ms: int | None
    total_response_ms: int | None
```

CLI 新增：

```bash
./julia-conversation \
  --backend deepseek \
  --echo-tts \
  --stream \
  --realtime-speech \
  --benchmark 3 \
  --text 'Julia，用一句短句说你在。'
```

### 真实 Benchmark 结果

```json
{
  "count": 3,
  "boundary_count": 0,
  "prompt_input_chars": {
    "min": 8611,
    "max": 8611,
    "mean": 8611,
    "median": 8611
  },
  "provider_first_token_ms": {
    "min": 3375,
    "max": 4494,
    "mean": 3773.67,
    "median": 3452
  },
  "http_response_open_ms": {
    "min": 1664,
    "max": 1826,
    "mean": 1749,
    "median": 1757
  },
  "time_to_first_voice_ms": {
    "min": 3453,
    "max": 4500,
    "mean": 3962.67,
    "median": 3935
  }
}
```

### 结论

当前实测瓶颈：

```text
provider_first_token_ms median ≈ 3452ms
TTFV median ≈ 3935ms
```

Prompt 已压缩到约 8611 chars，且：

```text
context_build_ms ≈ 1-5ms
prompt_build_ms ≈ 0ms
```

因此下一步优化方向不是 Runtime 状态机，而是：

1. 进一步压缩 persona context 到 `<4000 chars`；
2. 增加 fast acknowledgement path；
3. Provider Router 引入更快 provider；
4. TTS 预热 / 首句固定短回应；
5. 连接复用或 provider client 优化。

### 新增测试

```text
tests/test_phase35_latency_benchmark.py
```

覆盖：

- repeated turns 采样；
- TTFT / TTFV / prompt size 汇总；
- benchmark report 可作为 Provider Router 输入。

### 验收结果

```text
Ran 66 tests in 1.865s
OK
```


---

## Phase 3.5.7 Fast Acknowledgement Path

### 目标

当 provider TTFT 无法稳定压到 1.5s 内时，引入本地快速回应路径，先降低用户感知等待时间：

```text
speech_end / final_text
  ↓
local fast acknowledgement TTS
  ↓
provider streaming response continues
  ↓
formal answer TTS
```

### CLI 新增

```bash
--fast-ack '嗯，Tony，我在想。'
```

示例：

```bash
./julia-conversation \
  --backend deepseek \
  --echo-tts \
  --stream \
  --realtime-speech \
  --fast-ack '嗯，Tony，我在想。' \
  --benchmark 3 \
  --text 'Julia，用一句短句说你在。'
```

### Runtime 行为

`ConversationLoop.run_text_turn_realtime_speech()` 新增：

```python
fast_ack_text: str | None = None
```

当 `fast_ack_text` 存在：

- 在 provider first chunk 之前调用本地 TTS；
- `LatencyTracker.mark_tts_start()` 提前标记；
- metadata 写入：

```json
"fast_ack": {
  "text": "嗯，Tony，我在想。",
  "tts_engine": "local_tts",
  "ok": true,
  "duration_ms": 1500
}
```

### 真实 Benchmark 结果

```json
{
  "count": 3,
  "boundary_count": 0,
  "prompt_input_chars": {
    "median": 8611
  },
  "provider_first_token_ms": {
    "min": 2495,
    "max": 3007,
    "mean": 2722.67,
    "median": 2666
  },
  "time_to_first_voice_ms": {
    "min": 0,
    "max": 0,
    "mean": 0,
    "median": 0
  }
}
```

### 解释

当前 `local_tts` 是 dry-run，所以本地 TTS 起播时间显示为 `0ms`。

在真实 TTS 下，预期结果不是 0ms，而是：

```text
TTFV ≈ local TTS startup latency
```

目标：

```text
TTFV < 500ms
```

provider TTFT 仍然被独立记录：

```text
provider_first_token_ms median ≈ 2666ms
```

因此 Fast Ack 不掩盖 provider 慢的问题，只是把用户感知等待从：

```text
等待 DeepSeek 首 token
```

改成：

```text
Julia 先回应，然后继续思考
```

### 新增测试

```text
tests/test_phase32_realtime_speech_output.py
  - test_tc_phase32_026_fast_ack_speaks_before_first_cognitive_chunk

tests/test_phase35_latency_benchmark.py
  - test_tc_phase35_014_latency_benchmark_fast_ack_reduces_reported_ttfv
```

### 验收结果

```text
Ran 68 tests in 1.588s
OK
```


---

## Phase 3.5.8 Real TTS Startup Benchmark

### 目标

Fast Ack 已经把用户感知等待从 provider TTFT 前移到本地 TTS 起播。下一步需要单独测量 TTS engine 自身启动耗时：

```text
fast_ack_text
  ↓
TTSEngine.speak()
  ↓
call_ms / duration_ms / audio_path / error
```

### 新增模块

```text
tts/
└── benchmark.py
```

核心对象：

```python
@dataclass(frozen=True)
class TTSBenchmarkSample:
    index: int
    ok: bool
    engine: str
    text_chars: int
    call_ms: int
    duration_ms: int | None
    audio_path: str | None
    error: str | None
```

### CLI 新增

```bash
--tts-benchmark N
--tts-mode dry_run|say
```

Dry-run 示例：

```bash
./julia-conversation \
  --tts-benchmark 3 \
  --tts-mode dry_run \
  --fast-ack '嗯，Tony，我在想。'
```

macOS 本地 `say` 手动测试：

```bash
./julia-conversation \
  --tts-benchmark 3 \
  --tts-mode say \
  --fast-ack '嗯，Tony，我在想。'
```

### Dry-run 实测结果

```json
{
  "count": 3,
  "ok_count": 3,
  "engine": "local_tts",
  "call_ms": {
    "min": 0,
    "max": 0,
    "mean": 0,
    "median": 0
  },
  "duration_ms": {
    "min": 2750,
    "max": 2750,
    "mean": 2750,
    "median": 2750
  },
  "text_chars": {
    "median": 11
  }
}
```

### 说明

`dry_run` 不播放真实音频，所以 `call_ms=0` 是预期结果。

`duration_ms=2750` 是基于文本长度的估算语音时长，不是启动耗时。

真实 TTS 下需要关注：

```text
call_ms
first_audio_ready_ms  # 后续异步播放器支持后补充
audio_path
error
```

### 已增强 TTS metadata

`LocalTTSEngine` 现在写入：

```json
{
  "mode": "dry_run",
  "tts_call_ms": 0
}
```

`ElevenLabsScriptTTSEngine` 现在也会写入：

```json
{
  "tts_call_ms": 1234
}
```

### 新增测试

```text
tests/test_phase35_tts_benchmark.py
```

覆盖：

- dry-run TTS benchmark；
- CLI JSON 输出；
- `call_ms` / `duration_ms` / `engine` 指标。

### 验收结果

```text
Ran 70 tests in 1.774s
OK
```


---

## Phase 3.5.9 ElevenLabs Fast Ack Benchmark

### 目标

把 Fast Ack 的 TTS startup benchmark 从 `local_tts dry_run` 扩展到现有 Julia 声音脚本：

```text
fast_ack_text
  ↓
ElevenLabsScriptTTSEngine
  ↓
el_speak.py
  ↓
tts_call_ms / call_ms / error
```

### CLI 新增

```bash
--tts-engine local|elevenlabs-script
--elevenlabs-script /path/to/el_speak.py
--tts-timeout 30
```

示例：

```bash
./julia-conversation \
  --tts-benchmark 1 \
  --tts-engine elevenlabs-script \
  --elevenlabs-script /Users/admin/Desktop/tmp/el_speak.py \
  --tts-timeout 30 \
  --fast-ack '嗯，Tony，我在想。'
```

### Adapter 增强

`ElevenLabsScriptTTSEngine` 现在支持：

```python
script_path: Path
 timeout_s: float
```

并在所有结果中写入：

```json
{
  "tts_call_ms": 70,
  "script_path": "/Users/admin/Desktop/tmp/el_speak.py"
}
```

错误路径也会结构化返回：

```json
{
  "ok": false,
  "engine": "elevenlabs_script",
  "error": "script not found: ...",
  "metadata": {
    "tts_call_ms": 0,
    "script_path": "..."
  }
}
```

### 真实测试结果

命令：

```bash
./julia-conversation \
  --tts-benchmark 1 \
  --tts-engine elevenlabs-script \
  --elevenlabs-script /Users/admin/Desktop/tmp/el_speak.py \
  --tts-timeout 30 \
  --fast-ack '嗯，Tony，我在想。'
```

结果：

```json
{
  "count": 1,
  "ok_count": 1,
  "engine": "elevenlabs_script",
  "call_ms": {
    "min": 70,
    "max": 70,
    "mean": 70,
    "median": 70
  },
  "text_chars": {
    "median": 11
  }
}
```

### 结论

当前 `el_speak.py` wrapper 对短 Fast Ack 的 measured call time：

```text
≈ 70ms
```

这说明 Fast Ack 路径的 TTS 启动开销目前足够低，用户感知等待主要已经从：

```text
provider_first_token_ms ≈ 2.6s - 3.9s
```

转为：

```text
fast_ack_tts_call_ms ≈ 70ms
```

后续如果 `el_speak.py` 内部变成异步下载/播放，需要进一步拆：

```text
audio_file_ready_ms
playback_start_ms
playback_done_ms
```

### 新增测试

```text
tests/test_phase35_tts_benchmark.py
  - test_tc_phase35_017_elevenlabs_script_benchmark_reports_missing_script_without_network
  - test_tc_phase35_018_cli_elevenlabs_script_benchmark_accepts_script_path
```

### 验收结果

```text
Ran 72 tests in 2.010s
OK
```


---

## Phase 3.5.10 Enable Default Fast Ack for DeepSeek Realtime

### 目标

让 DeepSeek realtime conversation 默认启用 Julia 的短回应，不再每次手动传 `--fast-ack`。

### 默认规则

当满足：

```text
--backend deepseek
--realtime-speech
```

且没有显式禁用时，CLI 自动启用：

```text
嗯，Tony，我在想。
```

### CLI 新增

```bash
--no-fast-ack
```

显式覆盖：

```bash
--fast-ack '嗯，Tony，我马上看。'
```

禁用：

```bash
--no-fast-ack
```

### 行为验证

命令：

```bash
./julia-conversation \
  --backend deepseek \
  --echo-tts \
  --stream \
  --realtime-speech \
  --text 'Julia，用一句短句说你在。' \
  --trace
```

未传 `--fast-ack`，但输出已包含：

```text
[TTS_ACK:local_tts] 嗯，Tony，我在想。
```

且在 provider chunks 之前出现：

```text
state=THINKING
[TTS_ACK:local_tts] 嗯，Tony，我在想。
state=RESPONDING
Response chunk[0]: 嗯
```

### 真实测试结果

```json
{
  "provider_first_token_ms": 2079,
  "time_to_first_voice_ms": 0,
  "boundary_detected": false,
  "fast_ack": {
    "text": "嗯，Tony，我在想。",
    "tts_engine": "local_tts",
    "ok": true,
    "duration_ms": 2750
  }
}
```

### 解释

`local_tts` 当前是 dry-run，所以 `time_to_first_voice_ms=0`。

真实语音下，该值会接近：

```text
Fast Ack TTS startup latency
```

此前 ElevenLabsScript benchmark 显示短句调用约：

```text
70ms
```

因此 DeepSeek 慢首 token 不再直接决定用户是否听到 Julia 的第一声回应。

### 新增测试

```text
tests/test_phase33_cli.py
  - test_tc_phase33_020_cli_deepseek_realtime_defaults_fast_ack_even_when_provider_errors
  - test_tc_phase33_021_cli_deepseek_realtime_can_disable_default_fast_ack
  - test_tc_phase33_022_cli_deepseek_realtime_can_override_default_fast_ack
```

### 验收结果

```text
Ran 75 tests in 2.627s
OK
```


---

## Phase 3.6.1 Real Voice E2E via speech_lab STT

### 目标

复用已打通的 `speech_lab` 本地 macOS STT 链路，把真实语音输入接入 Julia Conversation Runtime：

```text
Tony voice
  ↓
speech_lab/stt
  ↓
SpeechLabSTT adapter
  ↓
ConversationLoop
  ↓
DeepSeekProvider / Echo
  ↓
Fast Ack
  ↓
TTS
```

### 新增模块

```text
stt/
└── speech_lab_stt.py
```

核心：

```python
class SpeechLabSTT:
    def capture_once(self) -> STTResult:
        ...
```

默认复用：

```text
/Users/admin/Desktop/speech_lab/stt
```

### CLI 新增

```bash
--real-voice
--speech-lab-root /Users/admin/Desktop/speech_lab
--stt-bin /Users/admin/Desktop/speech_lab/stt
--stt-lang zh-CN
--auto-stop-ms 1200
--max-duration-ms 12000
--stt-timeout 30
```

### Conversation TTS 新增

```bash
--conversation-tts-engine local|elevenlabs-script
--conversation-tts-mode dry_run|say
```

### 真实 E2E 命令

DeepSeek + speech_lab STT + realtime speech + Julia voice script：

```bash
./julia-conversation \
  --real-voice \
  --backend deepseek \
  --stream \
  --realtime-speech \
  --conversation-tts-engine elevenlabs-script \
  --elevenlabs-script /Users/admin/Desktop/tmp/el_speak.py \
  --tts-timeout 30 \
  --trace
```

Echo 本地快速验收：

```bash
./julia-conversation \
  --real-voice \
  --backend echo \
  --stream \
  --realtime-speech \
  --conversation-tts-engine elevenlabs-script \
  --elevenlabs-script /Users/admin/Desktop/tmp/el_speak.py \
  --tts-timeout 30 \
  --trace
```

### 新增测试

```text
tests/test_phase36_real_voice_e2e.py
```

覆盖：

- fake speech_lab STT → ConversationLoop → local TTS；
- STT permission/error path；
- fake speech_lab STT → ConversationLoop → ElevenLabsScript TTS。

### 验收结果

```text
Ran 78 tests in 4.201s
OK
```


---

## Phase 3.6.2 — Wake Word Calibration / Julia 唤醒词校准

### 问题

真实语音测试中，Apple Speech 对英文 `Julia` 的识别不稳定，可能被识别为：

- 兄弟
- 朱莉亚
- 朱丽亚
- 朱莉娅
- 茱莉亚
- 助理呀
- 处理呀

这会导致 Julia Runtime 收到错误输入，例如：

```text
Tony 原话: Julia 你在吗
STT 输出: 兄弟你在吗
```

### 处理策略

新增本地 wake word calibration 层：

```text
speech_lab STT raw text
  ↓
WakeWordAliasCorrector
  ↓
speech_lab dictionary normalizer
  ↓
Julia wake word repair
  ↓
Conversation Runtime
```

默认校准文件：

```text
memory/wake_word_calibration.jsonl
```

### CLI

```bash
./julia-conversation \
  --calibrate-wake-word 5 \
  --wake-word Julia \
  --speech-lab-root /Users/admin/Desktop/speech_lab \
  --stt-bin /Users/admin/Desktop/speech_lab/stt \
  --wake-word-calibration /Users/admin/julia_agent/memory/wake_word_calibration.jsonl
```

建议 Tony 录制多组：

```text
朱莉亚，你在吗
Julia，你在吗
朱莉亚，帮我看一下
Julia，继续
朱莉亚，记一下
```

### 验收

同一批语音样本经过校准后，应稳定归一化为：

```text
Julia你在吗
Julia帮我看一下
Julia继续
Julia记一下
```

---

## Phase 3.6.3 — STT Turn Truncation Repair / 语音截断修复

### 问题

真实 E2E 中出现：

```text
Tony 原话: Julia 你在吗
STT 输出: Julia你。
```

原因不是 DeepSeek，也不是 Conversation Runtime，而是 speech_lab / Apple Speech 的 auto-stop 过早 finalize，导致尾部 `在吗` 没有进入最终文本。

### 修复

默认参数调整：

```yaml
stt:
  auto_stop_ms: 1800
  max_duration_ms: 15000
```

同时增加窄域补全规则：

```text
Julia你。  → Julia你在吗？
Julia你    → Julia你在吗？
Julia在。  → Julia你在吗？
```

该规则只用于明显的 wake-word direct-address 截断，不泛化改写普通句子。

### 推荐真实测试命令

```bash
./julia-conversation \
  --real-voice \
  --backend deepseek \
  --stream \
  --realtime-speech \
  --conversation-tts-engine elevenlabs-script \
  --elevenlabs-script /Users/admin/Desktop/tmp/el_speak.py \
  --tts-timeout 30 \
  --auto-stop-ms 1800 \
  --max-duration-ms 15000 \
  --trace
```

如果仍然截断，使用更保守参数：

```bash
--auto-stop-ms 2200 --max-duration-ms 18000
```

### 验收

Tony 说：

```text
Julia，你在吗？
```

Trace 中应看到：

```text
text=Julia你在吗？
bridge=direct_llm
provider=deepseek_provider
state_trace=[LISTENING, USER_SPEAKING, FINALIZING, THINKING, RESPONDING, SPEAKING, LISTENING]
```

---

## Phase 3.6 当前回归结果

```text
Ran 83 tests in 5.858s
OK
```

结论：

- speech_lab STT 已接入 Julia Runtime。
- wake word alias / calibration 已接入。
- `Julia你。` 这类明显截断已修复。
- 当前真实 E2E 下一步应重点测试不同说话速度下的 `auto_stop_ms` 参数。

### Phase 3.6.4 — English Julia Wake Word Homophone Patch

真实测试发现：Tony 念英文 `Julia，你在吗` 时，Apple Speech 可能输出：

```text
对呀你在吗。
```

该问题属于 wake word homophone，不属于 DeepSeek / Conversation Runtime 问题。

修复策略：

- 不把 `对呀` 写入全局 speech_lab dictionary，避免普通中文句子被误改；
- 仅在 Julia Voice Runtime 的句首 direct-address 场景中，将：

```text
对呀你在吗。 → Julia你在吗。
```

归一化范围保持窄域：只处理句首、且后面紧跟 `你/在/帮/看/继续/记得...` 等直接呼叫模式。

验证：

```text
python3 -m unittest tests.test_phase36_real_voice_e2e -v
python3 -m unittest discover -s tests -p 'test_phase*.py'
```

结果：

```text
Ran 8 tests in 3.202s OK
Ran 83 tests in 5.624s OK
```

---

## Phase 3.6.5 — Supervised Wake Word Training / Tony 发音样本训练

### 背景

此前对 `Julia` 英文唤醒词的处理包含固定 alias，例如把某些 Apple Speech 输出强行映射为 `Julia`。

真实测试证明：这只能兜底，不能解决根因。

根因是：

```text
Tony 的英文 Julia 发音
  ↓
Apple Speech zh-CN 模型
  ↓
输出不稳定同音文本，例如：对呀你在吗
```

因此需要从“手写 alias”升级为“Tony 样本监督训练”。

### 新策略

校准阶段不再依赖当前 normalizer 猜测结果，而是使用 Tony 指定的 intended text 作为监督标签：

```text
raw STT output: 对呀你在吗
intended text:  Julia你在吗。
  ↓
learn alias:    对呀 → Julia
```

训练样本写入：

```text
memory/wake_word_calibration.jsonl
```

### CLI

```bash
./julia-conversation \
  --calibrate-wake-word 8 \
  --wake-word Julia \
  --wake-word-training-text 'Julia你在吗。' \
  --speech-lab-root /Users/admin/Desktop/speech_lab \
  --stt-bin /Users/admin/Desktop/speech_lab/stt \
  --wake-word-calibration /Users/admin/julia_agent/memory/wake_word_calibration.jsonl
```

建议 Tony 以自然速度录 8 次同一句：

```text
Julia，你在吗？
```

之后再录扩展句式：

```bash
./julia-conversation \
  --calibrate-wake-word 5 \
  --wake-word Julia \
  --wake-word-training-text 'Julia帮我看一下。' \
  --speech-lab-root /Users/admin/Desktop/speech_lab \
  --stt-bin /Users/admin/Desktop/speech_lab/stt \
  --wake-word-calibration /Users/admin/julia_agent/memory/wake_word_calibration.jsonl
```

### Runtime 修正路径

```text
speech_lab raw STT
  ↓
WakeWordAliasCorrector 读取训练样本
  ↓
句首 learned alias 替换为 Julia
  ↓
speech_lab dictionary normalizer
  ↓
Conversation Runtime
```

### 验收

如果训练样本中存在：

```json
{"raw_text":"对呀你在吗","normalized_text":"Julia你在吗。"}
```

则未来输入：

```text
对呀你在吗
```

应自动归一化为：

```text
Julia你在吗。
```

### 回归结果

```text
python3 -m unittest tests.test_phase36_real_voice_e2e -v
Ran 9 tests OK

python3 -m unittest discover -s tests -p 'test_phase*.py'
Ran 84 tests OK
```

结论：

`对呀 → Julia` 已从硬编码兜底改为训练样本驱动。后续新误识别不应继续手写规则，而应通过 `--calibrate-wake-word` 收集 Tony 的真实发音样本。

---

## Phase 3.6.6 — Wake Word Training Generalization / 训练模板泛化

### 新发现

Tony 执行监督训练后，真实样本为：

```text
raw=茱莉亚你在吗      normalized=Julia你在吗。
raw=对啊你在吗        normalized=Julia你在吗。
raw=你在吗            normalized=Julia你在吗。
raw=嗯                normalized=Julia你在吗。
raw=对啊你在吗        normalized=Julia你在吗。
raw=姐你在吗          normalized=Julia你在吗。
raw=你在吗            normalized=Julia你在吗。
raw=你在哪            normalized=Julia你在吗。
```

随后真实测试出现新误识别：

```text
助力呀你在吗。
```

旧训练器只能学习具体 alias，例如：

```text
对啊 -> Julia
姐   -> Julia
```

但无法泛化到新的同句式 wake-query：

```text
<unknown-homophone>你在吗
```

### 修复

训练器升级为两层学习：

1. Exact Alias Learning

```text
对啊你在吗 -> Julia你在吗。
learn: 对啊 -> Julia
```

2. Wake Query Template Learning

当同一目标句式出现至少 2 个有效样本时，学习：

```text
<short-prefix>你在吗 -> Julia你在吗
```

因此未见过的新误识别也能被修正：

```text
助力呀你在吗。 -> Julia你在吗。
```

### 坏样本过滤

以下样本只保存审计，不参与学习：

```text
嗯
你在吗
你在哪
```

原因：

- `嗯` 没有保留目标句尾；
- `你在吗` 丢失 wake word，alias 为空；
- `你在哪` 与目标句尾不一致。

### 防误伤

模板泛化只在窄域条件下生效：

- 句尾必须匹配已学习 suffix，例如 `你在吗`；
- 前缀必须为 1–4 个字符；
- 排除明显前置问候，如 `你好...`。

### 本地验证

```text
助力呀你在吗。 => Julia你在吗。
对啊你在吗     => Julia你在吗。
姐你在吗       => Julia你在吗。
你在吗         => 你在吗。
你在哪         => 你在哪。
你好兄弟你在吗 => 你好Julia你在吗。
```

### 回归结果

```text
python3 -m unittest tests.test_phase36_real_voice_e2e -v
Ran 11 tests OK

python3 -m unittest discover -s tests -p 'test_phase*.py'
Ran 86 tests OK
```

结论：

wake word training 已从“具体 alias 学习”升级为“有效样本 + 句式模板泛化”。这比继续手写 `助力呀/对啊/姐` 更接近根因解决。

---

## Phase 3.6.7 — Dropped Wake Word Recovery + Empty Capture Retry

### 新真实问题

多次真实测试后发现两个问题：

1. Tony 念 `Julia` 较快时，Apple Speech 可能直接丢失 wake word：

```text
Tony: Julia你在吗
STT:  你在吗。
```

2. Apple Speech 偶发没有返回任何文本：

```text
state=ERROR
[STT_ERROR] 未识别到文字
```

### 修复 1：Dropped Wake Word Recovery

当监督训练已经学到同一 suffix，例如至少两个有效样本：

```text
对啊你在吗 -> Julia你在吗。
姐你在吗   -> Julia你在吗。
```

Runtime 学到：

```text
suffix = 你在吗
```

之后如果真实 STT 输出刚好是：

```text
你在吗。
```

说明很可能是 `Julia` 被快读吞掉，于是恢复为：

```text
Julia你在吗。
```

注意：该恢复只对已经由有效样本学到的 suffix 生效，不从坏样本学习。

### 修复 2：Empty Capture Retry

新增 CLI 参数：

```bash
--stt-retries 1
```

默认真实语音捕获空文本时自动重听一次：

```text
[STT_RETRY] empty capture; retry 1/1. 请再说一遍。
```

重试仍为空才进入：

```text
state=ERROR
[STT_ERROR] 未识别到文字
```

### 当前本地验证

```text
你在吗。        => Julia你在吗。
助力呀你在吗。  => Julia你在吗。
Julia你在吗。   => Julia你在吗。
嗯              => 
你在哪          => 你在哪。
```

### 回归结果

```text
python3 -m unittest tests.test_phase36_real_voice_e2e -v
Ran 13 tests OK

python3 -m unittest discover -s tests -p 'test_phase*.py'
Ran 88 tests OK
```

### 推荐真实测试命令

```bash
./julia-conversation \
  --real-voice \
  --backend deepseek \
  --stream \
  --realtime-speech \
  --conversation-tts-engine elevenlabs-script \
  --elevenlabs-script /Users/admin/Desktop/tmp/el_speak.py \
  --tts-timeout 30 \
  --auto-stop-ms 1800 \
  --max-duration-ms 15000 \
  --stt-retries 1 \
  --trace
```

---

## Phase 3.7.2 — ElevenLabs Real Output Verification

### 问题

此前 `elevenlabs-script` wrapper 只检查 `el_speak.py` 的退出码。实际 `el_speak.py` 在以下情况会静默退出 0：

```text
/tmp/tts_enabled 不存在
ELEVENLABS_API_KEY 未配置
ElevenLabs API 返回空 audio
```

这会导致 Runtime trace 显示：

```text
ok=true
engine=elevenlabs_script
```

但 Tony 实际听不到声音。

### 修复

`tts/elevenlabs_tts.py` 现在增加 preflight：

- 检查脚本存在；
- 检查 `/tmp/tts_enabled`；
- 检查 `ELEVENLABS_API_KEY`；
- 检查 `ffplay`；
- 捕获 script stdout/stderr；
- 如果出现 `TTS Error:` 或 `API Error:`，返回 `ok=false`。

### 当前本机 smoke

```text
./julia-conversation --tts-benchmark 1 --tts-engine elevenlabs-script ...
```

结果：

```text
ok_count=0
error=ELEVENLABS_API_KEY is not configured
```

结论：当前链路不是 Runtime/TTS wrapper 问题，而是运行环境未向 Julia 进程提供 ElevenLabs API key。

### 真实发声验收命令

```bash
touch /tmp/tts_enabled
export ELEVENLABS_API_KEY='YOUR_KEY'
export ELEVENLABS_VOICE_ID='tOuLUAIdXShmWH7PEUrU'

./julia-conversation \
  --tts-benchmark 1 \
  --tts-engine elevenlabs-script \
  --elevenlabs-script /Users/admin/Desktop/tmp/el_speak.py \
  --tts-timeout 30 \
  --text 'Tony，ElevenLabs 语音测试。'
```

通过标准：

```text
ok_count=1
error=null
Tony 听到 ElevenLabs 声音
```

然后再进入完整语音链路：

```bash
./julia-conversation \
  --real-voice \
  --backend deepseek \
  --stream \
  --realtime-speech \
  --conversation-tts-engine elevenlabs-script \
  --elevenlabs-script /Users/admin/Desktop/tmp/el_speak.py \
  --tts-timeout 30 \
  --auto-stop-ms 1800 \
  --max-duration-ms 15000 \
  --stt-retries 1 \
  --trace
```

### 回归结果

```text
python3 -m unittest discover -s tests -p 'test_phase*.py'
Ran 94 tests OK
```

---

## Phase 3.7.3 — Short Greeting Fast Ack Bypass

### 新发现

ElevenLabs 真实发声打通后，`Julia你在吗` 的 short greeting 仍出现约 4s `bridge_first_chunk_ms`。

原因不是 DeepSeek，而是 realtime loop 在读取 `bridge.stream_response()` 前先同步播放了：

```text
[TTS_ACK:elevenlabs_script] 嗯，Tony，我在想。
```

对于普通长问题，fast ack 有价值；但对于 short greeting，本地就能立即回答：

```text
嗯，Tony，我在。
```

此时再先说 `我在想` 会造成：

- 多一次 ElevenLabs 调用；
- 延迟翻倍；
- 语义不自然。

### 修复

CLI 在每个 turn 获取 STT 文本后，先用 `ShortGreetingResponder` 判断：

```text
Julia你在吗。
```

若命中 short greeting，则跳过 `fast_ack_text`，直接进入：

```text
bridge.stream_response -> short_greeting chunk -> TTS sentence
```

### 验收

Text smoke：

```text
./julia-conversation --echo-tts --backend deepseek --stream --realtime-speech --text 'Julia你在吗。' --trace
```

结果：

```text
state=THINKING
state=RESPONDING
Response chunk[0]: 嗯，Tony，我在。
state=SPEAKING
[TTS_SENTENCE:0:local_tts] 嗯，Tony，我在。
backend=short_greeting
latency bridge_first_chunk_ms=0
```

不再出现：

```text
[TTS_ACK]
```

### 回归结果

```text
python3 -m unittest tests.test_phase37_short_greeting -v
Ran 5 tests OK

python3 -m unittest discover -s tests -p 'test_phase*.py'
Ran 95 tests OK
```

---

## Phase 3.7.5 — Continuous Real Voice Session

### 背景

此前 `--real-voice` 是 single-turn：

```text
启动
  ↓
听一句
  ↓
回答一句
  ↓
退出
```

这只能验证一次语音闭环，不能验证真正的语音交互 session。

### 新增模式

#### 固定多轮测试

```bash
--real-voice-turns N
```

例如：

```bash
./julia-conversation \
  --real-voice \
  --real-voice-turns 3 \
  --backend deepseek \
  --stream \
  --realtime-speech \
  --conversation-tts-engine elevenlabs-stream \
  --auto-stop-ms 1800 \
  --max-duration-ms 15000 \
  --stt-retries 1 \
  --trace
```

#### 连续 session

```bash
--real-voice-session
```

流程：

```text
Julia Voice Runtime started
state=LISTENING
[VOICE_TURN] 1/∞
Tony speaks
Julia responds
state=LISTENING
[VOICE_TURN] 2/∞
Tony speaks
Julia responds
...
Ctrl+C exit
```

### 推荐真实连续会话命令

```bash
./julia-conversation \
  --real-voice \
  --real-voice-session \
  --backend deepseek \
  --stream \
  --realtime-speech \
  --conversation-tts-engine elevenlabs-stream \
  --tts-timeout 30 \
  --auto-stop-ms 1800 \
  --max-duration-ms 15000 \
  --stt-retries 1 \
  --trace
```

如需继续使用旧脚本式 ElevenLabs：

```bash
--conversation-tts-engine elevenlabs-script \
--elevenlabs-script /Users/admin/Desktop/tmp/el_speak.py
```

### 验收标准

连续 3 轮内应看到：

```text
[VOICE_TURN] 1/∞
state=LISTENING -> USER_SPEAKING -> FINALIZING -> THINKING -> RESPONDING -> SPEAKING -> LISTENING
[VOICE_TURN] 2/∞
state=USER_SPEAKING -> ... -> LISTENING
[VOICE_TURN] 3/∞
state=USER_SPEAKING -> ... -> LISTENING
```

### 回归结果

```text
python3 -m unittest tests.test_phase36_real_voice_e2e tests.test_phase37_elevenlabs_streaming tests.test_phase37_short_greeting -v
OK

python3 -m unittest discover -s tests -p 'test_phase*.py'
Ran 98 tests OK
```

---

## Phase 3.7.6 — Long Sentence TTS Anti-Truncation

### 问题

连续语音 session 中发现：Julia 的长句在 ElevenLabs streaming 输出时可能被截断。

原因：

```text
DeepSeek chunk stream
  ↓
SentenceSegmenter
  ↓
完整长句一次性送入 ElevenLabs
  ↓
单句 TTS 请求/ffplay pipe 过长
  ↓
播放尾部存在截断风险
```

此前 realtime speech 使用：

```python
SentenceSegmenter(max_chars=120)
```

对中文语音输出偏长。

### 修复

1. realtime speech 的 sentence chunk 从 120 chars 调整为 60 chars；
2. `_hard_split()` 从机械按字符切，升级为优先按软边界切：

```text
， , ； ; 、 —— — ： :
```

例如：

```text
刚刚醒来，还没来得及加载太多东西——但听到你的声音，我感觉安心。
```

会被切成更适合 TTS 的短语，而不是整句一次送给 ElevenLabs。

### 验收

新增测试：

```text
test_tc_phase32_012_realtime_tts_prefers_soft_phrase_boundaries_for_long_sentences
test_tc_phase32_013_realtime_segmenter_uses_smaller_tts_chunks
```

确保：

- 长句会拆成多个 TTS chunk；
- 每个 chunk 不超过限制；
- 优先在中文逗号、顿号、破折号等自然停顿处切分；
- 不吞掉英文空格，例如 `Julia Runtime` 保持不变。

### 回归结果

```text
python3 -m unittest tests.test_phase32_realtime_speech_output tests.test_phase33_cognitive_context -v
OK

python3 -m unittest discover -s tests -p 'test_phase*.py'
Ran 100 tests OK
```

### 真实复测建议

使用连续 session，故意问一个会触发长回复的问题：

```text
Julia，详细说说你现在这个语音运行时是怎么工作的。
```

观察输出中是否出现多个：

```text
Sentence segment: ...
[TTS_SENTENCE:0:elevenlabs_streaming] ...
[TTS_SENTENCE:1:elevenlabs_streaming] ...
[TTS_SENTENCE:2:elevenlabs_streaming] ...
```

且每一段都应完整播放。

---

## Phase 3.7.7 — STT Semantic Repair + Local Vocal Gesture Router

### 问题 1：STT 语义误识别

真实 session 中 Tony 问：

```text
为什么不那么慌
```

Apple Speech 输出：

```text
为什么不那么花。
```

修复：增加窄域 semantic repair：

```text
不那么花 -> 不那么慌
```

只修这个固定短语，不做全局 `花/慌` 替换，避免误伤普通句子。

### 问题 2：Tiny vocal intent 不应交给 DeepSeek

输入：

```text
你呻吟一下。
```

这类请求本质是一个极短的 vocal gesture，不是推理任务。交给 DeepSeek 会产生：

- 首 token 延迟；
- provider 风格干预；
- 多余解释；
- 不稳定输出。

新增：

```text
runtime/cognitive/vocal_gesture.py
```

路由：

```text
Conversation Runtime
  ↓
DirectLLMBridge
  ↓
VocalGestureResponder
  ↓
local_vocal_gesture
  ↓
TTS
```

示例：

```text
你呻吟一下。 -> 嗯……Tony。
```

同时该路径会跳过 fast ack：

```text
不再先说：嗯，Tony，我在想。
```

### 本地 smoke

```text
./julia-conversation --echo-tts --backend deepseek --stream --realtime-speech --text '你呻吟一下。' --trace
```

结果：

```text
backend=vocal_gesture
provider=local_vocal_gesture
bridge_first_chunk_ms=0
Response chunk[0]: 嗯……Tony。
无 [TTS_ACK]
```

STT repair smoke：

```text
为什么不那么花。 => 为什么不那么慌。
```

### 回归结果

```text
python3 -m unittest tests.test_phase36_real_voice_e2e tests.test_phase37_short_greeting -v
OK

python3 -m unittest discover -s tests -p 'test_phase*.py'
Ran 103 tests OK
```

---

## Phase 3.7.8 — ElevenLabs Vocal Gesture Rendering

### 问题

`vocal_gesture` 路由已经成功：

```text
backend=vocal_gesture
provider=local_vocal_gesture
Response: 嗯……Tony。
```

但真实听感仍然“没有反应”。原因是：

```text
eleven_turbo_v2_5 更适合低延迟普通朗读，
但对 [sighs] / [exhales] 这类表演标签不稳定。
```

### 修复

1. `VocalGestureResponder` 输出 Eleven v3 audio tag：

```text
[exhales softly] 嗯……Tony。
```

2. 新增 CLI 参数：

```bash
--elevenlabs-model eleven_v3
```

用于需要 vocal gesture / expressive delivery 的 session。

### 推荐测试命令

```bash
./julia-conversation \
  --real-voice \
  --real-voice-session \
  --backend deepseek \
  --stream \
  --realtime-speech \
  --conversation-tts-engine elevenlabs-stream \
  --elevenlabs-model eleven_v3 \
  --tts-timeout 30 \
  --auto-stop-ms 1800 \
  --max-duration-ms 15000 \
  --stt-retries 1 \
  --trace
```

然后说：

```text
你呻吟一下。
```

预期：

```text
backend=vocal_gesture
provider=local_vocal_gesture
Response chunk[0]: [exhales softly] 嗯……Tony。
TTS engine=elevenlabs_streaming
```

### 注意

- 如果追求低延迟普通对话，用默认 `eleven_turbo_v2_5`；
- 如果追求 vocal gesture / 情绪表演，用 `--elevenlabs-model eleven_v3`；
- v3 可能比 turbo 更慢，但表演标签效果更好。

### 回归结果

```text
python3 -m unittest discover -s tests -p 'test_phase*.py'
Ran 104 tests OK
```

---

## Phase 3.7.9 — Vocal Gesture DeepSeek Generation

### 背景

`你呻吟一下。` 这类请求不应该走普通聊天 prompt，也不应该长期固定成本地文本。

目标是：

```text
VocalGestureIntent detected
  ↓
Julia Runtime 专用 response_mode
  ↓
DeepSeekProvider 生成短 vocal phrase
  ↓
TTS
```

### 实现

新增/调整：

```text
runtime/cognitive/vocal_gesture.py
runtime/cognitive/prompt_builder.py
runtime/conversation_runtime/bridge/direct_llm_bridge.py
```

`PromptBuilder` 新增：

```text
response_mode = vocal_gesture_generation
```

专用规则：

- 只输出 Julia 的短声线反应；
- 只输出 1 行；
- 可用 `嗯 / 啊 / 呀 / 唔 / ……` 等拟声与停顿；
- 不解释；
- 不分析；
- 不输出规则说明；
- 不走普通问答长回复。

### Fallback

如果 DeepSeek 不可用或返回空：

```text
vocal_gesture_fallback -> [exhales softly] 嗯……Tony。
```

### 预期 trace

DeepSeek 可用时：

```text
backend=deepseek_provider
vocal_gesture_generation={matched: true, reason: vocal_gesture}
```

DeepSeek 不可用时：

```text
backend=vocal_gesture_fallback
provider=local_vocal_gesture_fallback
fallback=true
```

### 回归结果

```text
python3 -m unittest discover -s tests -p 'test_phase*.py'
Ran 104 tests OK
```
