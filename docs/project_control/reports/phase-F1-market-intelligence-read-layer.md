# Phase F1 — Market Intelligence Read Layer / Shadow Morning Analyst Report

## 1. 目标与范围

本阶段基于 `docs/project_control/PHASE_CONTRACT_F1.md` 与 F1 `APPROVED WITH NOTES` 执行 test-first implementation，让 Julia 从 F0 的“接口存在”进入 deterministic Shadow Morning Analyst：读取冻结 `FinancialBriefingBundle`，生成结构化 `PremarketResearchReport`，并渲染 Markdown《Julia盘前研究》。

范围内：

- 记录 F1 Contract approval notes。
- 新增 F1 failing acceptance tests。
- 扩展金融 contracts：`ConclusionWithEvidence`、`PremarketResearchReport`，并为 `InvestmentCase` 增加 `case_type="shadow_research"`。
- 新增 deterministic premarket workflow：`run_premarket_research(...)`。
- 新增 Markdown renderer：`render_premarket_report(...)`。
- 验证 EvidenceRef 全覆盖、shadow/draft 语义、无交易动作、无 memory 正式写入、无数据库/ai_theme_app 内部 import。

范围外：

- 不连接真实市场或真实数据库。
- 不调用在线 LLM、实时新闻搜索或随机采样。
- 不实现 F2 收盘验证、F3 审核写入、F4 语音播报、F5 20 日 Shadow Validation。
- 不迁移 `identity/`、`memory/`、`data/`、`audio/`、legacy runtime/tests/scripts 全量目录。

## 2. 变更文件清单

| 文件路径 | 变更类型 | 说明 |
|---|---|---|
| `docs/project_control/PHASE_CONTRACT_F1.md` | 修改 | 追加 `APPROVED WITH NOTES` 与 5 条实现治理备注。 |
| `tests/test_financial_f1_premarket.py` | 新增 | F1 验收测试，覆盖 12 个 Acceptance Targets 与 renderer/boundary 附加审计。 |
| `runtime/capability/financial/contracts/__init__.py` | 修改 | 新增 F1 report contracts；补充 InvestmentCase `case_type`。 |
| `runtime/capability/financial/workflows/__init__.py` | 新增 | workflow package marker。 |
| `runtime/capability/financial/workflows/premarket.py` | 新增 | deterministic F1 premarket report workflow。 |
| `runtime/capability/financial/rendering/__init__.py` | 新增 | rendering package marker。 |
| `runtime/capability/financial/rendering/report_renderer.py` | 新增 | Markdown《Julia盘前研究》renderer。 |

## 3. 验证命令与结果

| 命令 | 结果 |
|---|---|
| `.venv/bin/python -m pytest -q tests/test_financial_f1_premarket.py` | PASS — 14 passed |
| `.venv/bin/python -m pytest -q tests/test_financial_f0_contract.py tests/test_financial_f1_premarket.py` | PASS — 25 passed |
| `.venv/bin/python -m py_compile runtime/capability/financial/workflows/premarket.py` | PASS — exit 0 |
| `.venv/bin/python -m py_compile runtime/capability/financial/rendering/report_renderer.py` | PASS — exit 0 |

附加核查：

- F1 test-first 顺序满足：`17abde2 Add F1 premarket acceptance tests` 先于实现 commit `cce39ad`。
- Workflow deterministic：只执行 `FinancialBriefingBundle -> PremarketResearchReport`，使用稳定 `input_hash`。
- Renderer 不输出“今日推荐股票”等荐股语言。
- InvestmentCase 状态为 `shadow`，`case_type="shadow_research"`。
- 未提交 memory/data/tmp/audio/identity 私有内容。

## 4. 风险与限制

| 风险/限制 | 当前处理 |
|---|---|
| F1 仍使用 F0 fixture 数据，不代表真实市场接入 | 符合 F1 approval notes；真实接入应作为 F1.5 Real Data Adapter Spike。 |
| InvestmentCase 可能被未来误用为交易建议 | 当前 status/case_type 均为 shadow/shadow_research；测试禁止交易动作词。 |
| EvidenceRef 链路未来可能断裂 | F1 tests 已强制 report conclusion 与 case evidence 非空。 |
| CONTRACT_VERSION 目前在 workflow 中定义为 `0.1`，contracts 字段仍用 schema_version | 下一阶段可统一抽出常量模块。 |

## 5. 对账结论

- Branch: `codex/f1/market-intelligence-read-layer`
- Base: `phase-f0-complete` / `main@f5517a7`
- Gate status: READY FOR REVIEW
- Changed files limited to F1 contract, F1 tests, F1 financial contracts/workflow/renderer, and F1 report.

## 6. Review Checklist

### 功能完整性

- [x] 每日盘前研究报告可生成。
- [x] Market State / Top Themes / Conditional Watchlist / Risk / Auction Points 覆盖。
- [x] 每个候选有 draft/shadow InvestmentCase。
- [x] EvidenceRef 全覆盖。
- [x] Markdown《Julia盘前研究》可渲染。

### 质量门禁

- [x] F1 pytest 通过。
- [x] F0+F1 回归通过。
- [x] py_compile 通过。
- [x] 测试先行提交顺序满足。

### 架构合规

- [x] deterministic workflow。
- [x] 不连接真实市场/数据库。
- [x] 不调用 LLM。
- [x] 不触发交易。
- [x] 不修改策略/World Model/M7 Risk Gate。
- [x] 不写入正式 Memory。

### 待验收

请用户选择：`ACCEPT` / `REWORK` / `REQUEST CHANGES` / `APPROVED WITH NOTES`。
