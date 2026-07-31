# Phase Execution Contract — F4.2 Analyst Workbench UI Integration Layer

## 1. Phase Identity

- **Phase Name**: Analyst Workbench UI Integration Layer
- **Phase Code**: F4.2
- **Parent Milestone**: Julia Financial Analyst Integration / Analyst Workbench Interaction
- **Risk Level**: Medium
- **Baseline Dependency**: F4.1 complete at `phase-f4.1-complete` / `2d5fea0`
- **Source Documents**:
  - `docs/project_control/PHASE_CONTRACT_F4.md` — Julia Interaction Boundary Contract
  - `docs/project_control/reports/phase-F4.1-analyst-chat-interface.md` — F4.1 APPROVED WITH NOTES
  - User F4.2 guidance — Workbench UI integration, not direct React implementation before contract

## 2. Phase Objective

F4.2 的目标是把 Julia Financial Analyst 接入现有 Analyst Workbench，建立 Human Workbench → Analyst Chat Interface 的前端交互入口。F4.2 不是“聊天窗口功能”，而是 **Julia Financial Analyst 在分析师工作台中的交互入口**。

核心链路：

```text
React Analyst Workbench
        ↓
JuliaCopilot.tsx
        ↓
WebSocket Client
        ↓
analyst_chat/api.py
        ↓
AnalystSession
        ↓
Financial Capability
```

F4.2 必须保持：

- 不新增金融判断能力；
- 不在前端实现 intent/context/financial logic；
- 不接语音、Avatar、长期记忆 UI；
- 不加入交易按钮或仓位管理；
- 只做 text panel + WebSocket + EvidenceRef display。

## 3. UI Boundary

F4.2 建立的是：

```text
Human Workbench
        ↓
JuliaCopilot UI
        ↓
Analyst Chat Protocol
        ↓
F4.1 Runtime Interface
```

不是：

```text
Chat UI
        ↓
LLM
```

前端不得绕过 F4.1 `analyst_chat/api.py` 直接访问 F0-F3 runtime modules。

## 4. Scope

### 4.1 In Scope

- `JuliaCopilot.tsx` 单组件；
- `JuliaMessage.tsx` 最小消息展示；
- `EvidenceRefCard.tsx` 最小证据链接展示；
- `analystChatClient.ts` WebSocket client；
- `analystChat.ts` protocol/message types；
- text input、send、receive、disconnect/reconnect；
- EvidenceRef clickable/displayable；
- limitations display；
- voice icon placeholder only。

### 4.2 Out of Scope

- Voice；
- Avatar；
- Chat history persistence；
- Memory UI；
- Investment decision button；
- Buy/Sell button；
- Portfolio management；
- Real-time notification；
- LLM calls；
- Financial logic in frontend；
- Direct database/API calls outside analyst chat WebSocket。

## 5. Directory Contract

V0.1 前端目录保持小而明确：

```text
frontend/
  components/
    JuliaCopilot/
      JuliaCopilot.tsx
      JuliaMessage.tsx
      EvidenceRefCard.tsx
  services/
    analystChatClient.ts
  types/
    analystChat.ts
```

禁止在 F4.2 引入：

```text
hooks/
stores/
providers/
contexts/
avatar/
voice/
memory/
portfolio/
trading/
```

这些复杂度后续按阶段拆分。

## 6. Analyst Chat Protocol

F4.2 前端不直接依赖 Python 内部 dataclass，而依赖稳定 WebSocket protocol。

### 6.1 Client → Server Message

```json
{
  "type": "message",
  "payload": {
    "session_id": "abc",
    "text": "今天怎么看AI",
    "timestamp": "2026-07-31T08:00:00"
  }
}
```

### 6.2 Server → Client Response

```json
{
  "type": "response",
  "payload": {
    "session_id": "abc",
    "intent": "morning_brief",
    "text": "今天AI方向...",
    "evidence_refs": [
      {
        "id": "theme_001",
        "title": "AI主题",
        "source_type": "theme",
        "url": null
      }
    ],
    "context_scope": ["market_state", "top_themes", "risk_state"],
    "confidence": 0.72,
    "limitations": ["当前为研究观察，不是正式推荐"],
    "timestamp": "2026-07-31T08:00:01"
  }
}
```

### 6.3 Error Message

```json
{
  "type": "error",
  "payload": {
    "message": "connection interrupted",
    "recoverable": true,
    "timestamp": "2026-07-31T08:00:02"
  }
}
```

## 7. Frontend Message Model

```ts
export type JuliaMessage = {
  id: string;
  role: "user" | "julia";
  text: string;
  intent?: "morning_brief" | "deep_dive" | "research" | "unknown";
  evidenceRefs?: EvidenceRefDisplay[];
  contextScope?: string[];
  confidence?: number;
  limitations?: string[];
  timestamp: string;
};

export type EvidenceRefDisplay = {
  id: string;
  title: string;
  sourceType?: string;
  url?: string | null;
};
```

## 8. Component Contract

### 8.1 JuliaCopilot.tsx

Responsibilities:

- render title `Julia Analyst`;
- render message list;
- render text input;
- send user message through `analystChatClient`;
- render Julia response;
- render voice icon placeholder;
- handle connection states: connecting / connected / disconnected / error.

Must not:

- perform intent detection;
- build financial context;
- call financial APIs directly;
- contain stock-specific rules such as `if (stock === "xxx")`;
- show trading action buttons.

### 8.2 JuliaMessage.tsx

Responsibilities:

- render user/julia message text;
- render intent label if present;
- render limitations;
- pass evidence refs to `EvidenceRefCard`.

### 8.3 EvidenceRefCard.tsx

Responsibilities:

- render EvidenceRef id/title/source type;
- make ref clickable/displayable;
- if url is null, show non-navigation evidence badge;
- no data fetching in card V0.1.

### 8.4 analystChatClient.ts

Responsibilities:

- connect;
- send;
- receive;
- disconnect;
- reconnect once or expose reconnect callback;
- parse protocol message types.

Must not:

- detect intent;
- transform financial logic;
- call memory/database/trading APIs.

## 9. Workbench Layout Contract

F4.2 should integrate as a bottom dock, not a fourth major column.

Target layout:

```text
┌──────────────────────────────────────────┐
│              Analyst Workbench            │
│                                          │
│ Theme Radar   AI Cognition   Validation  │
│                                          │
├──────────────────────────────────────────┤
│ Julia Analyst Copilot                    │
│                                          │
│ Tony: 为什么关注AI?                      │
│ Julia: 因为...                           │
│ Evidence: Theme/Event/Risk               │
│                                          │
│ [ input............................. ] 🎙 │
└──────────────────────────────────────────┘
```

## 10. Acceptance Targets

- [ ] **F4.2-AT-01 JuliaCopilot 加载**：`JuliaCopilot.tsx` 可以被导入并渲染基本标题/输入框。
- [ ] **F4.2-AT-02 用户输入发送**：用户输入文字后，component 调用 `analystChatClient.send(...)`，不在 UI 内判断 intent。
- [ ] **F4.2-AT-03 WebSocket 建立**：`analystChatClient` 可建立/关闭 WebSocket，并暴露 connection state。
- [ ] **F4.2-AT-04 收到 AnalystResponseEnvelope**：client 能解析 `type="response"` protocol message，并转为 `JuliaMessage`。
- [ ] **F4.2-AT-05 Julia 回复渲染**：UI 能展示 Julia response text、intent、timestamp。
- [ ] **F4.2-AT-06 EvidenceRef 展示**：EvidenceRef 可点击或以 badge/card 形式展示；url 为 null 时不跳转。
- [ ] **F4.2-AT-07 Limitations 展示**：UI 必须展示 limitations，且不隐藏“证据不足/研究观察”类限制。
- [ ] **F4.2-AT-08 断线恢复**：断线后 UI 显示 disconnected/error 状态，并允许 reconnect 或自动重连一次。
- [ ] **F4.2-AT-09 Frontend 无金融逻辑**：前端代码不包含 stock-specific condition、strategy rule、intent detection 或 context building。
- [ ] **F4.2-AT-10 禁止 Memory/Database/Trading API**：前端不调用 memory/database/trading/portfolio/order 相关 API；不出现 buy/sell/order action button。
- [ ] **F4.2-AT-11 Voice placeholder only**：voice icon 可以显示但不得启用语音能力。
- [ ] **F4.2-AT-12 F4.1 protocol compatibility**：前端 protocol 与 F4.1 `AnalystResponseEnvelope` 字段兼容。

## 11. Acceptance ↔ Test Mapping

| TC-ID | Acceptance | Required Test / Expected Result |
|---|---|---|
| F4.2-TC-01 | F4.2-AT-01 | `JuliaCopilot` render smoke: title/input present。 |
| F4.2-TC-02 | F4.2-AT-02 | 输入后 mock client `send` called with protocol message。 |
| F4.2-TC-03 | F4.2-AT-03 | `analystChatClient` connect/disconnect state test。 |
| F4.2-TC-04 | F4.2-AT-04 | response protocol parse -> JuliaMessage。 |
| F4.2-TC-05 | F4.2-AT-05 | Julia response text/intent/timestamp rendered。 |
| F4.2-TC-06 | F4.2-AT-06 | EvidenceRefCard renders id/title/source and handles null url。 |
| F4.2-TC-07 | F4.2-AT-07 | limitations rendered visibly。 |
| F4.2-TC-08 | F4.2-AT-08 | disconnected/error UI state appears and reconnect callable exists。 |
| F4.2-TC-09 | F4.2-AT-09 | static scan: no stock-specific if/rules, no intent detection/context builder in frontend。 |
| F4.2-TC-10 | F4.2-AT-10 | static scan: no memory/database/trading/portfolio/order API calls/buttons。 |
| F4.2-TC-11 | F4.2-AT-11 | voice button has disabled/placeholder semantics。 |
| F4.2-TC-12 | F4.2-AT-12 | protocol type matches `AnalystResponseEnvelope` fields。 |

## 12. Required Commands

Commands depend on the target frontend package once located. Required command shape:

```bash
npm test -- JuliaCopilot
npm test -- analystChatClient
npm run typecheck
npm run lint
```

If the repository does not yet contain a frontend package, F4.2 implementation must first add the minimal package/test harness in a separate small commit and document exact commands in the phase report.

Python regression must still pass:

```bash
.venv/bin/python -m pytest -q tests/test_financial_f0_contract.py tests/test_financial_f1_premarket.py tests/test_financial_f2_close_validation.py tests/test_financial_f3_tony_review.py tests/test_financial_f4_analyst_chat.py
```

## 13. Risk Matrix

| Risk | Impact | Likelihood | Trigger | Mitigation |
|---|---|---:|---|---|
| UI embeds financial logic | Breaks F4 interaction boundary | Medium | stock-specific if / strategy rules in TSX | Static scan + review gate |
| UI introduces trading affordance | Safety/governance break | Medium | Buy/Sell/Order buttons | Non-goal + static scan |
| Protocol drifts from F4.1 envelope | Runtime/UI mismatch | Medium | Missing evidence/limitations/context fields | Protocol compatibility test |
| Overbuilt frontend architecture | Slows iteration | Medium | hooks/stores/providers introduced early | Directory contract blocks |
| Voice drags scope | Delays text interaction | Medium | microphone/Web Speech code | voice placeholder only |

## 14. Rollback Plan

### 14.1 Code Rollback

- Trigger: frontend tests fail after one minimal fix; protocol mismatch; UI introduces forbidden financial/trading logic.
- Rollback: remove F4.2 frontend files only.
- Compatibility: F4.1 runtime interface remains intact.

### 14.2 Data Rollback

- No data migration in F4.2.
- No chat history persistence in V0.1.

### 14.3 Sync Rollback

- If phase status is advanced before evidence exists, return to Doing and attach failed command output.

## 15. Non-Goals

- No Voice.
- No Avatar.
- No Chat History Persistence.
- No Memory UI.
- No Investment Decision Button.
- No Buy/Sell Button.
- No Portfolio Management.
- No Real-time Notification.
- No LLM calls.
- No Financial logic in frontend.
- No direct database / memory / trading API calls.

## 16. Implementation Order

After contract approval:

1. Locate or create minimal frontend package boundary.
2. Add test-first specs for `JuliaCopilot`, `analystChatClient`, protocol types, evidence card, static boundary scans.
3. Implement `types/analystChat.ts`.
4. Implement `services/analystChatClient.ts`.
5. Implement `EvidenceRefCard.tsx`.
6. Implement `JuliaMessage.tsx`.
7. Implement `JuliaCopilot.tsx`.
8. Run frontend tests/typecheck/lint and Python F0-F4 regression.
9. Generate phase report and wait for review.

## 17. Review Decision

Current status: `DESIGN DRAFT`

Waiting for user review before F4.2 test-first implementation.

## 18. Approval Decision — APPROVED WITH NOTES

Decision: `APPROVED WITH NOTES`

Approval rationale:

- F4.2 正确引入 human-facing workbench interaction layer，但不把金融智能移动到 frontend。
- `JuliaCopilot.tsx` 被定位为 Analyst Workbench 中的 interaction dock，不是独立 Chat UI 或第四业务栏。
- `AnalystChatProtocol` 独立于 Python dataclass，保持 Web / Mobile / Voice / Avatar 后续入口的协议稳定性。
- Acceptance Targets 覆盖 component mount、protocol parsing、WebSocket lifecycle、EvidenceRef rendering、limitations rendering 与 frontend boundary scan。

Required Notes before/during implementation:

1. **Frontend 只消费 ResponseEnvelope**：禁止 React 自己拼接 Julia 回答、Evidence、Risk；必须由 backend response envelope 提供内容，frontend 只 render。
2. **EvidenceRefCard 不做解释**：允许展示 EvidenceRef id/title/source；不允许 React 自己生成“这个主题很强，因为...”等金融解释。
3. **不要引入全局状态管理**：F4.2 V0.1 不引入 Redux/Zustand/MobX，除非现有 Workbench 已强制使用；优先 component state + websocket state。
4. **UI 不持久化聊天历史**：不创建 chat history table，不写 localStorage permanent memory；F4.2 只展示当前交互。
5. **Keep ResponseEnvelope stable**：WebSocket response protocol 必须兼容 F4.1 `AnalystResponseEnvelope` 字段，不重新设计 runtime output。

Implementation order:

1. `tests` / frontend test-first specs：component mount、protocol parsing、websocket mock、evidence render、limitations render、forbidden API scan。
2. `frontend/types/analystChat.ts`。
3. `frontend/services/analystChatClient.ts`。
4. `frontend/components/JuliaCopilot/EvidenceRefCard.tsx`。
5. `frontend/components/JuliaCopilot/JuliaMessage.tsx`。
6. `frontend/components/JuliaCopilot/JuliaCopilot.tsx`。
7. Run frontend tests and Python F0-F4 regression.
