# FEATURE SPEC — P3.phase6.10.2.1 Context Quality Evaluation

## Task `P3.phase6.10.2.1-T01` — Context OS Health Monitor

### 1) 目标与边界

目标：在 Context Planner 后、Budget/Compact 前增加 Context Quality Evaluation，使 Julia 能判断当前上下文是否健康、可信、过载或高幻觉风险。

非目标：不接 Provider、不阻断实际回答链路、不做 Conflict Resolver 实现，只输出 quality signal。

### 2) 子功能分解

#### F-P3.phase6.10.2.1-T01-01 ContextQuality 数据契约
- 输入：plan_id、coverage、confidence、risk、authority、evidence_count。
- 处理：校验 0~1 区间与非负计数。
- 输出：不可变 `ContextQuality`。
- 失败处理：非法指标抛 `ValueError`。
- 可观测证据：`to_dict()`。
- 测试：TC-361021-001。

#### F-P3.phase6.10.2.1-T01-02 Coverage 评估
- 输入：ContextPlan + ContextBlock-like blocks。
- 处理：检查 core_identity/relationship_anchor/active_task/session_state 覆盖。
- 输出：identity_coverage/relationship_coverage/task_coverage。
- 失败处理：缺块返回 0，不异常。
- 可观测证据：identity plan gate pass。
- 测试：TC-361021-001。

#### F-P3.phase6.10.2.1-T01-03 Evidence Confidence 与 hallucination risk
- 输入：semantic_evidence/compact/recent_turns blocks。
- 处理：统计 highest_authority、assistant_generated_ratio、low_authority_count。
- 输出：evidence_confidence/hallucination_risk/warnings。
- 失败处理：historical query 无高权威 evidence 时 gate fail。
- 可观测证据：assistant-only evidence high risk。
- 测试：TC-361021-002。

#### F-P3.phase6.10.2.1-T01-04 Budget 与 Conflict Health Signal
- 输入：estimated_tokens、target_budget_tokens、conflict_topics。
- 处理：计算 budget_utilization 与 conflict_count。
- 输出：budget_utilization_too_high/context_conflict_detected warnings。
- 失败处理：只告警，不修改 blocks。
- 可观测证据：over budget 和 conflict 单测。
- 测试：TC-361021-003/004。

### 3) 接口与契约

新增：

```text
runtime/context_os/quality/context_quality.py
runtime/context_os/quality/quality_policy.py
runtime/context_os/quality/quality_evaluator.py
```

核心 API：

```python
ContextQualityEvaluator().evaluate(plan=ContextPlan, blocks=list[Any]) -> ContextQuality
```

### 4) 数据模型与状态变更

无持久化状态。Quality 是每轮派生 health signal。

### 5) 实现步骤

1. 新建 `runtime/context_os/quality` 包。
2. 定义 `ContextQuality` schema。
3. 定义 `ContextQualityPolicy` gate rules。
4. 实现 `ContextQualityEvaluator.evaluate()`。
5. 新增质量评估单元测试。
6. 跑新增测试与全量回归。

### 6) 测试设计与命令

```bash
python3 -m unittest tests.test_phase361021_context_quality_evaluation -v
python3 -m unittest discover -s tests
```

预期：4 个新增测试通过；全量 320 tests OK。

### 7) 风险与回滚

风险：Quality gate 过早接入主链路可能阻断回答。缓解：本阶段只输出信号，不接 DirectLLMBridge。

回滚：删除 `runtime/context_os/quality` 与新增测试，不影响 planner/truth layer。

### 8) 验收映射

- ACPT-361021-001：身份问题具备 identity/relationship blocks 时 gate pass。
- ACPT-361021-002：历史事实问题只有 assistant claims 时 high hallucination risk 且 gate fail。
- ACPT-361021-003：budget_utilization > 0.92 时输出告警。
- ACPT-361021-004：冲突 evidence 输出 conflict_count 与 warning。
