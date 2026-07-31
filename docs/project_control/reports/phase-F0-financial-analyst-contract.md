# Phase F0 — Financial Analyst Contract & Bridge Spike Report

## 1. 目标与范围

本阶段基于 `docs/project_control/PHASE_CONTRACT_F0.md` 执行最小代码迁移，目标是在公开仓库的文档基线之后，建立 Julia Financial Capability 的只读 Typed Contract 与本地 fixture client。

范围内：

- 加固公开仓库 `.gitignore`，避免运行数据、缓存、音频、密钥与私有状态误入 Git。
- 先提交 F0 验收测试：`tests/test_financial_f0_contract.py`。
- 实现最小 F0 contracts/client：
  - `runtime/capability/financial/contracts/`
  - `runtime/capability/financial/client/`
- 验证 EvidenceRef 覆盖、只读边界、无数据库直连、无 `ai_theme_app` 内部 import、无正式交易决策。

范围外：

- 不迁移 legacy runtime 全量目录。
- 不迁移 memory/data/tmp/audio。
- 不迁移 identity 真实内容。
- 不连接真实 ai_theme_app 数据库。
- 不实现 F1+ 报告渲染、盘后验证、审核写入、语音播报或 20 日 Shadow Validation。

## 2. 变更文件清单

| 文件路径 | 变更类型 | 说明 |
|---|---|---|
| `.gitignore` | 修改 | 增加 secret、本地凭据、运行数据、音频、模型权重、数据库文件忽略规则。 |
| `tests/test_financial_f0_contract.py` | 新增 | F0 合同验收测试，覆盖 F0-TC-01 至 F0-TC-11。 |
| `runtime/capability/financial/__init__.py` | 新增 | Julia Financial Capability package marker。 |
| `runtime/capability/financial/contracts/__init__.py` | 新增 | frozen dataclass Typed Contract：EvidenceRef、FinancialBriefingBundle、RiskStateView、ThemeView、CandidateView 等。 |
| `runtime/capability/financial/client/__init__.py` | 新增 | financial client export。 |
| `runtime/capability/financial/client/ai_theme_client.py` | 新增 | 只读 fixture client，提供 F0 read API 与 frozen replayable bundle。 |

## 3. 验证命令与结果

| 命令 | 结果 |
|---|---|
| `.venv/bin/python -m pytest -q tests/test_financial_f0_contract.py` | PASS — 11 passed |
| `.venv/bin/python -m pytest -q tests/test_financial_f0_contract.py --maxfail=1` | PASS — 11 passed |
| `.venv/bin/python -m py_compile runtime/capability/financial/client/ai_theme_client.py` | PASS — exit 0 |

附加核查：

- 测试先行已执行：测试 commit `47d7783` 先于实现 commit `ffda22d`。
- F0 client AST import boundary 通过：未 import `ai_theme_app`。
- F0 client 数据边界通过：未出现数据库连接、ORM、SQL 访问。
- F0 输出边界通过：无正式交易决策对象。
- F0 replay 通过：同一 fixture 重复调用结果等价，dataclass frozen。

## 4. 风险与限制

| 风险/限制 | 当前处理 |
|---|---|
| 本地 legacy `runtime/`、`tests/`、`scripts/` 存在绝对路径和环境变量访问痕迹 | 本阶段未 bulk-add，仅新增隔离 F0 financial skeleton。扫描摘要保存在 `tmp/security/f0_migration_scan.json`（未提交）。 |
| `identity/` 含真实身份/人格内容 | 本阶段不提交；后续仅允许 schema/template 单独审查后进入 Git。 |
| F0 当前使用 fixture client，不接真实 gateway | 符合 Contract & Bridge Spike；真实 adapter/API 接入留给后续小步 PR。 |
| `docs/project_control/EXECUTION_GUARDRAILS.md` 当前未在仓库中 | F0 合同已引用该 guardrail；后续若使用 Notion/dev-orchestrator 状态同步，应补齐或确认该文件。 |

## 5. 对账结论

- Branch: `codex/f0/financial-analyst-contract`
- Base: `main` documentation baseline `9b23967`
- Head at validation: `ffda22d`
- Changed files are limited to `.gitignore` + F0 financial contracts/client + F0 test.
- Gate status: READY FOR REVIEW

## 6. Review Checklist

### 功能完整性

- [x] F0 Typed Contract 已实现。
- [x] F0 read-only client 已实现。
- [x] 每条关键结论携带 EvidenceRef。
- [x] 结果可冻结、可回放。

### 质量门禁

- [x] F0 pytest 通过。
- [x] py_compile 通过。
- [x] 测试先行提交顺序满足。

### 架构合规

- [x] 不直连数据库。
- [x] 不 import `ai_theme_app` 内部模块。
- [x] 不产生正式交易决策。
- [x] 未提交 memory/data/tmp/audio/identity 私有内容。

### 待验收

请用户选择：`ACCEPT` / `REWORK` / `REQUEST CHANGES` / `APPROVED WITH NOTES`。

## 7. Approval Decision — APPROVED WITH NOTES

Decision: `APPROVED WITH NOTES`

Approval rationale:

- Phase Contract 对齐：通过。
- Scope 控制：通过。
- Contract-first / Test-first：通过。
- Read-only Boundary：通过。
- EvidenceRef 基础：通过。
- Repository Hygiene：通过。
- 可回滚性：通过。

Merge Notes for PR / main history:

1. **保持 Gateway 只读边界**：`ai_theme_client.py` 后续不得直接 import `ai_theme_app.database` 或查询 raw tables；只能通过 Analyst Gateway Contract。
2. **Contract Versioning**：F1 前建议加入明确 `CONTRACT_VERSION = "0.1"`，覆盖 `FinancialBriefingBundle`、`EvidenceRef`、`InvestmentCase` 等核心 contract。
3. **EvidenceRef 是长期核心资产**：后续 Market Thesis、InvestmentCase、Research Request 必须保持 `Conclusion -> EvidenceRef -> Source Snapshot` 链路；不得出现 `LLM opinion -> memory`。
4. **不扩大 F0 功能**：F0 完成不代表 Julia 金融分析师完成；新闻理解、题材推理、股票筛选、InvestmentCase、Memory Learning、Voice Briefing 均属于 F1+。
5. **PR 合并后打 Tag**：建议合并后创建 `phase-f0-complete` 或 `v0.1.0-financial-contract`，标记 Julia Financial Capability 第一个架构里程碑。

Next recommended phase:

- **F1 — Market Intelligence Read Layer**
- Objective: 让 Julia 第一次看到真实市场，即通过 `ai_theme_app -> DailyMarketState / Attention Radar / Theme Ranking / W2S Candidate Pool / Risk State -> Julia Morning Analyst Context` 形成真实市场观察层。
