# Phase F4.1 — Analyst Chat Text Interface Report

## 1. 目标与范围

本阶段基于冻结的 `docs/project_control/PHASE_CONTRACT_F4.md` 执行 F4.1 test-first implementation，实现 Julia Financial Analyst 的 V0.1 text-only interaction boundary。

范围内：

- `tests/test_financial_f4_analyst_chat.py` 失败测试先行。
- 实现四文件 analyst_chat 骨架：`api.py/session.py/context.py/voice.py`。
- 实现 deterministic keyword intent detection。
- 实现 intent-aware minimal context builder。
- 实现 `AnalystResponseEnvelope`，包含 EvidenceRef、context_scope、confidence、limitations。
- 实现 WebSocket transport shell `/analyst/chat`。
- 保留 voice placeholder。

范围外：

- 不实现前端 React 组件。
- 不实现语音。
- 不调用 LLM。
- 不连接数据库。
- 不写 Memory。
- 不修改策略/Profile。
- 不触发交易。

## 2. 变更文件清单

| 文件路径 | 变更类型 | 说明 |
|---|---|---|
| `tests/test_financial_f4_analyst_chat.py` | 新增 | F4 analyst chat 验收测试。 |
| `runtime/capability/financial/interface/__init__.py` | 新增 | interface package marker。 |
| `runtime/capability/financial/interface/analyst_chat/__init__.py` | 新增 | analyst_chat package marker。 |
| `runtime/capability/financial/interface/analyst_chat/api.py` | 新增 | WebSocket transport shell。 |
| `runtime/capability/financial/interface/analyst_chat/session.py` | 新增 | AnalystSession、intent detection、response envelope。 |
| `runtime/capability/financial/interface/analyst_chat/context.py` | 新增 | Intent-aware context builder。 |
| `runtime/capability/financial/interface/analyst_chat/voice.py` | 新增 | Voice placeholder。 |

## 3. 验证命令与结果

| 命令 | 结果 |
|---|---|
| `.venv/bin/python -m pytest -q tests/test_financial_f4_analyst_chat.py` | PASS — 9 passed |
| `.venv/bin/python -m pytest -q tests/test_financial_f0_contract.py tests/test_financial_f1_premarket.py tests/test_financial_f2_close_validation.py tests/test_financial_f3_tony_review.py tests/test_financial_f4_analyst_chat.py` | PASS — 58 passed |
| `.venv/bin/python -m py_compile runtime/capability/financial/interface/analyst_chat/api.py` | PASS — exit 0 |
| `.venv/bin/python -m py_compile runtime/capability/financial/interface/analyst_chat/session.py` | PASS — exit 0 |
| `.venv/bin/python -m py_compile runtime/capability/financial/interface/analyst_chat/context.py` | PASS — exit 0 |
| `.venv/bin/python -m py_compile runtime/capability/financial/interface/analyst_chat/voice.py` | PASS — exit 0 |

## 4. 风险与限制

| 风险/限制 | 当前处理 |
|---|---|
| WebSocket 未做真实服务集成测试 | F4.1 只提交 transport shell；真实服务/前端联调后置 F4.2。 |
| `api.py` 可能膨胀 | 当前测试禁止 `detect_intent/build_context` 进入 `api.py`。 |
| Context builder 未来可能加载过重 | 当前测试固定 morning_brief/deep_dive/unknown 的 context isolation。 |
| Voice 未实现 | 符合 V0.1 text-only scope。 |

## 5. 对账结论

- Branch: `codex/f4.1/analyst-chat-implementation`
- Base: `phase-f4-contract-frozen` / `main@117f43e`
- Gate status: READY FOR REVIEW
- Changed files limited to F4 test, F4 interface package, and F4 report.

## 6. Review Checklist

- [x] Test-first 顺序满足。
- [x] Text-only chat session 可生成 response。
- [x] Intent deterministic 且 priority 生效。
- [x] Context isolation 生效。
- [x] EvidenceRef requirement 生效。
- [x] ResponseEnvelope 包含 limitations。
- [x] Voice placeholder only。
- [x] F0-F4 回归通过。

### 待验收

请用户选择：`ACCEPT` / `REWORK` / `REQUEST CHANGES` / `APPROVED WITH NOTES`。

## 7. Approval Decision — APPROVED WITH NOTES

Decision: `APPROVED WITH NOTES`

Approval rationale:

- F4.1 成功建立 Julia Financial Analyst 的稳定 Human Interaction Boundary。
- F0-F4 全链路回归通过，证明 Interaction Layer 未破坏金融能力边界、研究层、评价层与治理层。
- `AnalystResponseEnvelope` 已提供 `EvidenceRefs + Context Scope + Limitations`，让 Julia 的回答成为可审计分析接口，而不是普通聊天输出。
- `api.py/session.py/context.py/voice.py` 四文件边界满足 V0.1 contract。

Merge Notes:

1. **F4.1 是 Interface Layer，不是 Intelligence Layer**：F0-F3 是 reasoning capability，F4 是 access layer；不得在 F4 增加金融判断逻辑。
2. **ResponseEnvelope 是长期协议**：未来 Web Chat、Voice、Avatar、Mobile App 都应复用 `AnalystResponseEnvelope`，不要每个入口重新设计输出格式。
3. **Context Scope 必须继续收紧**：`Intent first, Context second, Evidence always` 继续作为 Julia Runtime 交互原则。
4. **Voice 延后**：F4.1 text-only 正确；语音应作为单独 `F4.3 Voice Interaction` 或 voice adapter phase。
5. **UI 单独拆 Phase**：React 面板不混入 F4.1；后续单独进入 `F4.2 Analyst Workbench UI Integration`。

Recommended next phase:

- **F4.2 — Analyst Workbench UI Integration**
- Objective: 将 Julia 接入现有 AI Theme App 分析师工作台，通过 `JuliaCopilot.tsx -> WebSocket -> analyst_chat/api.py -> Julia Runtime` 完成最小文本面板。
