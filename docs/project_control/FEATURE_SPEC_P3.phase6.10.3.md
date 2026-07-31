# FEATURE SPEC — P3.phase6.10.3 Context Budget Manager

## Task `P3.phase6.10.3-T01` — ContextPlan Block Budget Allocation

### 1) 目标与边界

目标：根据 `ContextPlan` 对候选 `ContextBlock` 做 required/optional 分配、intent priority boost、excluded block 过滤和 trace 输出。

非目标：不接真实 provider token counter、不做 Compact、不修改 DirectLLMBridge。

### 2) 子功能分解

#### F-P3.phase6.10.3-T01-01 ContextBlock 契约
- 输入：block_id/block_type/priority/content/required/authority。
- 处理：估算 token，校验 priority/authority。
- 输出：ContextBlock included/excluded/clipped 表示。
- 失败处理：非法字段抛 ValueError。
- 可观测证据：to_dict/trace。
- 测试：TC-36103-001。

#### F-P3.phase6.10.3-T01-02 Required Block 保留
- 输入：identity/relationship/active_task required blocks。
- 处理：required 优先保留，必要时允许小范围 overflow 或 clip。
- 输出：required blocks included。
- 失败处理：极端超预算 clip required block。
- 可观测证据：tight budget 下 identity/relationship 保留。
- 测试：TC-36103-001。

#### F-P3.phase6.10.3-T01-03 Intent-aware Priority Boost
- 输入：ContextPlan.intent_type + candidate blocks。
- 处理：personal_history_recall 提升 semantic_evidence；current_task 提升 active_task/open_loops/recent_turns。
- 输出：更符合 intent 的 included set。
- 失败处理：低优先 optional 超预算 excluded。
- 可观测证据：personal history 中 semantic_evidence 胜过 recent_turns。
- 测试：TC-36103-002。

#### F-P3.phase6.10.3-T01-04 Exclusion 与 Trace
- 输入：plan.excluded_blocks + allocation result。
- 处理：runtime_trace 等显式排除；输出 included/excluded/clipped trace。
- 输出：BudgetAllocation.to_trace()。
- 失败处理：excluded reason 保留。
- 可观测证据：runtime_trace excluded_by_context_plan；trace 可审计。
- 测试：TC-36103-003/004。

### 3) 接口与契约

新增：

```text
runtime/context_os/budget/context_block.py
runtime/context_os/budget/token_estimator.py
runtime/context_os/budget/budget_policy.py
runtime/context_os/budget/budget_allocator.py
```

核心 API：

```python
ContextBudgetManager().allocate(plan=ContextPlan, blocks=list[ContextBlock]) -> BudgetAllocation
```

### 4) 数据模型与状态变更

无持久化状态。BudgetAllocation 是每轮派生结果。

### 5) 实现步骤

1. 新建 `runtime/context_os/budget` 包。
2. 实现 ContextBlock 和 token estimator。
3. 实现 BudgetPolicy effective_budget/priority_boosts。
4. 实现 ContextBudgetManager.allocate。
5. 新增预算单元测试。
6. 跑单测和全量回归。

### 6) 测试设计与命令

```bash
python3 -m unittest tests.test_phase36103_context_budget_manager -v
python3 -m unittest discover -s tests
```

预期：4 个新增测试通过；全量 324 tests OK。

### 7) 风险与回滚

风险：粗略 token 估算与真实 provider token 不一致。缓解：本阶段 dependency-free，后续 provider token counter 可替换 token_estimator。

回滚：删除 `runtime/context_os/budget` 与测试，不影响 planner/quality/truth layer。

### 8) 验收映射

- ACPT-36103-001：required identity/relationship blocks 在 tight budget 下保留。
- ACPT-36103-002：personal_history_recall 优先 semantic_evidence。
- ACPT-36103-003：runtime_trace 按 ContextPlan 排除。
- ACPT-36103-004：allocation trace 包含 included/excluded/budget utilization。
