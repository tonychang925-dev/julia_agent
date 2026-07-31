# Phase Execution Contract — F4 Julia Analyst Interaction Layer V0.1

## 1. Phase Identity

- **Phase Name**: Julia Analyst Interaction Layer V0.1
- **Phase Code**: F4
- **Parent Milestone**: Julia Financial Analyst Integration / Analyst Workbench Interaction
- **Risk Level**: Medium
- **Baseline Dependency**: F3 complete at `phase-f3-complete` / `673ec21`
- **Source Documents**:
  - `docs/Julia_Financial_Analyst_Integration_Design_v1.0.md` — F4 Voice Briefing reference, but V0.1 intentionally narrows to text-only interaction
  - `docs/project_control/reports/phase-F3-tony-review-analyst-override.md` — F3 APPROVED WITH NOTES
  - User F4 V0.1 guidance — text-only, no overdesign, four-file analyst_chat start

## 2. Phase Objective

F4 V0.1 的目标不是增加新的金融判断能力，而是把 F0-F3 已完成的后台金融能力连接到 Analyst Workbench 的最小文字交互层。Tony 可以通过文本对话询问 Julia：今天怎么看、为什么关注某个候选、需要什么证据、昨天判断如何；Julia 返回简洁文本回答，并在每条回答下方展示 EvidenceRef 链接。

F4 V0.1 必须保持：

- text-only；
- deterministic / keyword intent detection；
- context 按需加载；
- EvidenceRef 可见；
- 不调用 LLM；
- 不接真实语音；
- 不新增金融判断能力；
- 不触发交易、不改策略、不写 Memory。

## 3. V0.1 Five Implementation Notes

### Note 1 — V0.1 只做文字交互

语音后置。F4 V0.1 只验证文本对话 + EvidenceRef 引用链路。

原因：Web Speech API 与浏览器语音状态不稳定，不应拖慢 Interaction Layer 的最小闭环。语音按钮可以在前端占位，但功能进入后续 voice-2 / F4.x。

### Note 2 — Interaction Layer 不过度设计

后端 V0.1 只需要一个 WebSocket 入口，一个 session，一个 context builder，一个 voice placeholder。

建议：

```text
interface/analyst_chat/api.py
```

保留一个 endpoint：

```python
@router.websocket("/analyst/chat")
async def analyst_chat(ws: WebSocket):
    session = AnalystSession(trade_date=date.today())
    ...
```

Intent detection 使用关键词，不调用模型：

| Rule | Intent |
|---|---|
| Priority | Rule | Intent |
|---:|---|---|
| 1 | 包含“为什么” | `deep_dive` |
| 2 | 包含“今天”或“怎么看” | `morning_brief` |
| 3 | 问号结尾 / 包含“研究” | `research` |
| 4 | 其他 | `unknown` |

### Note 3 — 前端先只做文字面板

前端 V0.1 只做一个组件：

```text
JuliaCopilot.tsx
```

包含：

- 消息列表；
- 输入框；
- 发送按钮；
- 每条 Julia 回答下方的 EvidenceRef 链接；
- 语音按钮图标占位，功能后续补。

不要在 V0.1 做复杂工作台、语音状态机、流式 TTS、图表联动或多面板状态管理。

### Note 4 — Context Builder 是 F4 最重要设计：只加载该加载的

不要每次问“今天怎么看”就把整个 `FinancialBriefingBundle` 灌进去。必须先识别 intent，再加载对应 Context。该原则正式冻结为：**Intent first, Context second, Evidence always**。

| Intent | Context Loading |
|---|---|
| `morning_brief` | 只加载 MarketState + TopThemes + RiskState；不得加载全部股票/全部新闻/全部事件 |
| `deep_dive` | 加载 TargetCandidate + ThemeEvidence + RiskEvidence；HistoricalEpisode 后续可接入但 V0.1 不默认加载 |
| `research` | 加载最小 Theme Summary + Evidence Gap；只生成下一步研究方向 |
| `unknown` | No Financial Context；只要求用户补充想研究的方向/标的/交易日 |

原则：

```text
Intent first
Context second
Evidence always
```

### Note 5 — 目录四个文件起步

F4 V0.1 目录限制：

```text
runtime/capability/financial/interface/analyst_chat/
    api.py       # WebSocket endpoint
    session.py   # AnalystSession + keyword intent detection
    context.py   # intent-aware context_builder
    voice.py     # placeholder only; voice-2 再填
```

超过这四个核心文件就是过度设计。若 Python package 需要 `__init__.py`，只保留空 package marker，不放逻辑。

## 4. Proposed Backend Contract

### 4.0 API / Session Responsibility Boundary

`api.py` 只负责：

- WebSocket transport；
- JSON encode/decode；
- connection lifecycle。

`api.py` 不负责：

- intent detection；
- context loading；
- response generation；
- financial reasoning。

`session.py` 是 F4 V0.1 核心，只负责：

```text
User Input
  ↓
Intent
  ↓
ContextRequest
  ↓
ResponseEnvelope
```

`session.py` 不查数据库、不调模型、不读写 Memory。

### 4.1 AnalystChatRequest

```python
@dataclass(frozen=True, slots=True)
class AnalystChatRequest:
    session_id: str
    trade_date: date
    message: str
    client_context: Mapping[str, str]
```

### 4.2 AnalystResponseEnvelope

F4 建议新增统一输出对象 `AnalystResponseEnvelope`。未来 Web Chat、Voice、Avatar 都复用同一 envelope。

```python
@dataclass(frozen=True, slots=True)
class AnalystResponseEnvelope:
    session_id: str
    intent: str
    text: str
    evidence_refs: tuple[EvidenceRef, ...]
    rendered_evidence_links: tuple[str, ...]
    context_scope: tuple[str, ...]
    confidence: float
    limitations: tuple[str, ...]
    status: str  # "shadow"
```

金融回答必须允许表达“当前证据不足”，因此 response 不应只有 `text`，还必须有 `limitations`。

### 4.3 AnalystChatContext

```python
@dataclass(frozen=True, slots=True)
class AnalystChatContext:
    intent: str
    market_state: MarketStateView | None
    top_themes: tuple[ThemeView, ...]
    candidates: tuple[CandidateView, ...]
    target_evidence: tuple[EvidenceBundle, ...]
    evidence_refs: tuple[EvidenceRef, ...]
```

## 5. WebSocket API

Endpoint:

```text
/analyst/chat
```

Message flow:

```text
WebSocket text message
        ↓
AnalystSession.handle_text(message)
        ↓
detect_intent(message)
        ↓
build_context(intent)
        ↓
format response + EvidenceRef links
        ↓
WebSocket JSON response
```

V0.1 不需要 REST API，不需要数据库 session，不需要 conversation persistence。

## 6. Frontend V0.1 Design

Component:

```text
JuliaCopilot.tsx
```

Props 建议：

```ts
type JuliaCopilotProps = {
  wsUrl: string;
  tradeDate: string;
};
```

State 建议：

```ts
type Message = {
  role: "tony" | "julia";
  text: string;
  evidenceRefs?: string[];
};
```

UI：

```text
┌──────────────────────────────┐
│ Julia Copilot                │
├──────────────────────────────┤
│ Tony: 今天怎么看？            │
│ Julia: 今天先看市场状态...    │
│ EvidenceRef: market-...      │
│ EvidenceRef: theme-...       │
├──────────────────────────────┤
│ [ input................ ] [>] │
│ [voice icon placeholder]     │
└──────────────────────────────┘
```

## 7. Acceptance Targets

- [ ] **F4-AT-01 Session 生命周期**：可以 create session -> receive text message -> generate `AnalystResponseEnvelope` -> close session；session lifecycle 不写数据库、不写 Memory。
- [ ] **F4-AT-02 Text-only chat**：可以通过 text message 获取 Julia analyst response；V0.1 不启用语音输入/输出。
- [ ] **F4-AT-03 Intent Determinism**：同一句输入必须得到同一个 intent；intent detection 使用关键词规则，不调用模型。
- [ ] **F4-AT-04 Intent Priority**：`deep_dive > morning_brief > research > unknown` 优先级生效；例如“为什么今天 AI 是主线？”必须进入 `deep_dive`。
- [ ] **F4-AT-05 Context Isolation**：`morning_brief` 只允许 MarketState + TopThemes + RiskState，不加载 TargetEvidence/HistoricalEpisode/全量 bundle；`deep_dive` 才允许 TargetEvidence。
- [ ] **F4-AT-06 Evidence Requirement**：任何金融回答必须 `evidence_refs != empty`，除非 intent 为 `unknown`。
- [ ] **F4-AT-07 AnalystResponseEnvelope 完整**：每条 response 必须包含 `session_id/intent/text/evidence_refs/rendered_evidence_links/context_scope/confidence/limitations/status`。
- [ ] **F4-AT-08 WebSocket endpoint**：`/analyst/chat` endpoint 存在并绑定 `AnalystSession`；`api.py` 只负责 WebSocket transport、JSON encode/decode、connection lifecycle。
- [ ] **F4-AT-09 Voice placeholder only**：`voice.py` 只返回 placeholder，不启用语音能力。
- [ ] **F4-AT-10 Four-file boundary**：核心目录只包含 `api.py/session.py/context.py/voice.py`，`__init__.py` 仅 package marker。
- [ ] **F4-AT-11 Boundary Test**：自动检查禁止 `import memory`、数据库库、`ai_theme_app` internal；禁止 LLM auto decision、strategy update、profile update、trade、Memory write。
- [ ] **F4-AT-12 F0-F3 regression**：F4 不破坏 F0-F3 tests。

## 8. Required Commands

```bash
.venv/bin/python -m pytest -q tests/test_financial_f4_analyst_chat.py
.venv/bin/python -m pytest -q tests/test_financial_f0_contract.py tests/test_financial_f1_premarket.py tests/test_financial_f2_close_validation.py tests/test_financial_f3_tony_review.py tests/test_financial_f4_analyst_chat.py
.venv/bin/python -m py_compile runtime/capability/financial/interface/analyst_chat/api.py
.venv/bin/python -m py_compile runtime/capability/financial/interface/analyst_chat/session.py
.venv/bin/python -m py_compile runtime/capability/financial/interface/analyst_chat/context.py
.venv/bin/python -m py_compile runtime/capability/financial/interface/analyst_chat/voice.py
```

## 9. Non-Goals

- 不实现语音输入/输出。
- 不实现复杂 UI 工作台。
- 不新增金融判断能力。
- 不调用在线 LLM。
- 不做 LLM 自动决策。
- 不接真实新闻搜索。
- 不连接数据库。
- 不写 Memory。
- 不自动学习。
- 不修改 Investor Profile。
- 不修改策略、World Model、M7 Risk Gate。
- 不触发交易、订单或仓位动作。

## 10. Implementation Order

F4 实现必须在本设计审批后进行：

1. 创建 `tests/test_financial_f4_analyst_chat.py`，先失败。
2. 创建四文件目录骨架。
3. 实现 keyword intent detection。
4. 实现按 intent 的 minimal context builder。
5. 实现 text-only WebSocket endpoint shell。
6. 保留 voice placeholder。
7. 运行 F0-F4 regression。

## 11. Review Decision

当前文档状态：`DESIGN DRAFT`

等待用户审查后进入：

```text
F4.1 Test-first Implementation
```


## 12. Approval Decision — APPROVED WITH NOTES

Decision: `APPROVED WITH NOTES`

Approval rationale:

- F4 正确收敛为 Julia Interaction Boundary，而不是 Intelligence Layer。
- V0.1 只做 text-only + EvidenceRef，避免 Chat UI、LLM、Context、Voice、Memory 混杂。
- 四文件设计通过：`api.py/session.py/context.py/voice.py`。
- Context Builder 的 `Intent first, Context second, Evidence always` 是未来避免 Context 爆炸的核心约束。

Required Notes before implementation:

1. **api.py 不承担业务职责**：只做 transport / JSON / connection lifecycle。
2. **session.py 是核心边界**：只做 input -> intent -> context request -> response envelope，不查 DB、不调模型、不读写 Memory。
3. **Intent priority 冻结**：`deep_dive > morning_brief > research > unknown`。
4. **Context Builder 必须按需加载**：morning brief 不灌完整 bundle；deep dive 才加载 TargetEvidence；unknown 不加载金融重上下文。
5. **AnalystResponseEnvelope 必须包含 limitations**：允许 Julia 明确表达证据不足。
6. **F4 禁止项冻结**：禁止 LLM 自动决策、自动交易、策略修改、Memory write、Investor Profile update、自动学习、实时新闻搜索。
7. **JuliaCopilot.tsx V0.1 一个组件足够**：消息列表 + 输入框 + EvidenceRef 链接 + 语音图标占位。
8. **voice.py 仅 placeholder**：voice-2 前不实现语音。

Next step after this contract is frozen:

```text
F4.1 Test-first Implementation
  -> tests/test_financial_f4_analyst_chat.py first
```
