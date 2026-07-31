# Phase F4.2 — Analyst Workbench UI Integration Report

## 1. 目标与范围

本阶段基于冻结的 `docs/project_control/PHASE_CONTRACT_F4.2.md` 执行 F4.2.1 test-first implementation，实现 Julia Financial Analyst 在 Analyst Workbench 中的 V0.1 text-only UI entry。

范围内：

- 新增 frontend test harness：Vitest、React Testing Library、TypeScript、静态边界检查。
- 新增 `JuliaCopilot` workbench dock component。
- 新增 `AnalystChatProtocol` TypeScript contract。
- 新增 WebSocket client adapter 与 deterministic mock client。
- 新增 `JuliaMessage` 与 `EvidenceRefCard` 渲染组件。
- 展示 `AnalystResponseEnvelope` 的 text、intent、EvidenceRef、context scope、limitations。
- 保留 voice placeholder。

范围外：

- 不实现语音。
- 不实现 Avatar。
- 不持久化聊天历史。
- 不引入全局状态管理。
- 不在前端做 intent detection、context building 或金融推理。
- 不调用 Memory、Database、Trading API。
- 不加入交易、组合、买卖按钮。

## 2. 变更文件清单

| 文件路径 | 变更类型 | 说明 |
|---|---|---|
| `.gitignore` | 修改 | 忽略 `frontend/node_modules/`、`frontend/dist/`、`frontend/coverage/`。 |
| `frontend/package.json` | 新增/修改 | F4.2 frontend test/typecheck/lint scripts 与 React/Vitest deps。 |
| `frontend/package-lock.json` | 新增 | 锁定 Node 20 兼容依赖版本。 |
| `frontend/tsconfig.json` | 新增 | TypeScript strict config。 |
| `frontend/vitest.config.ts` | 新增 | Vitest jsdom config。 |
| `frontend/tests/setup.ts` | 新增 | jest-dom setup。 |
| `frontend/scripts/static-boundary-check.mjs` | 新增 | 前端边界静态检查。 |
| `frontend/tests/JuliaCopilot.test.tsx` | 新增 | JuliaCopilot UI acceptance tests。 |
| `frontend/tests/analystChatClient.test.ts` | 新增 | AnalystChatProtocol/client tests。 |
| `frontend/types/analystChat.ts` | 新增 | F4.2 protocol/message TypeScript contract。 |
| `frontend/services/analystChatClient.ts` | 新增 | WebSocket client adapter + mock client。 |
| `frontend/components/JuliaCopilot/JuliaCopilot.tsx` | 新增 | Workbench dock component。 |
| `frontend/components/JuliaCopilot/JuliaMessage.tsx` | 新增 | Message renderer。 |
| `frontend/components/JuliaCopilot/EvidenceRefCard.tsx` | 新增 | EvidenceRef display card。 |

## 3. 验证命令与结果

| 命令 | 结果 |
|---|---|
| `npm test -- JuliaCopilot analystChatClient` | PASS — 2 files / 11 tests passed |
| `npm run typecheck` | PASS — `tsc --noEmit` exit 0 |
| `npm run lint` | PASS — static boundary check exit 0 |
| `.venv/bin/python -m pytest -q tests/test_financial_f0_contract.py tests/test_financial_f1_premarket.py tests/test_financial_f2_close_validation.py tests/test_financial_f3_tony_review.py tests/test_financial_f4_analyst_chat.py` | PASS — 58 passed |

## 4. 风险与限制

| 风险/限制 | 当前处理 |
|---|---|
| 尚未接入真实 Analyst Workbench 页面 | 本阶段只提交可复用 dock component 与 client；实际页面挂载可后置。 |
| WebSocket client 未做浏览器 E2E | V0.1 通过 protocol parser + mock client 验证；真实联调后置。 |
| 前端可能承载金融逻辑 | `npm run lint` 静态检查 `components/services/types`，禁止金融动作、Memory/DB/Trading/API 边界词。 |
| Evidence 展示可能变成解释层 | `EvidenceRefCard` 只展示 id/title/source/url，不生成金融解释。 |
| Voice 未实现 | 保留 disabled placeholder，符合 F4.2 non-goal。 |

## 5. 对账结论

- Branch: `codex/f4.2.1/analyst-workbench-ui`
- Base: `phase-f4.2-contract-frozen`
- Gate status: READY FOR REVIEW
- Commit sequence:
  - `51da471` — Add F4.2 frontend test harness
  - `64119d5` — Add F4.2 UI acceptance tests
  - `9510a88` — Extend F4.2 analyst chat protocol tests
  - `5ad6859` — Implement F4.2 JuliaCopilot workbench UI
- Changed files limited to F4.2 frontend harness, protocol, UI component, tests, and phase report.
- Legacy untracked runtime/memory/data/audio/identity assets remain outside this phase scope.

## 6. Review Checklist

- [x] Contract-first / test-first sequence preserved.
- [x] JuliaCopilot loads as a workbench interaction dock.
- [x] User input sends `AnalystChatProtocol` message through client.
- [x] `AnalystResponseEnvelope` is parsed into `JuliaMessage`.
- [x] Julia response text, intent, EvidenceRef, context scope, limitations render.
- [x] EvidenceRef card does not generate financial explanation.
- [x] Disconnected state and reconnect action render.
- [x] Voice remains disabled placeholder.
- [x] Frontend boundary lint passes.
- [x] F0-F4 backend regression passes.

### 待验收

请用户选择：`ACCEPT` / `REWORK` / `REQUEST CHANGES` / `APPROVED WITH NOTES`。
