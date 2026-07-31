# FEATURE SPEC — P3.phase6.10.2 Context Planner Runtime

## Task `P3.phase6.10.2-T01` — Context Planner Intent Layer

### 1) 目标与边界

目标：将 Context OS 入口从 Memory Search 升级为 Context Planning。Planner 输出抽象 `ContextPlan`，描述本轮需要构造什么认知世界，而不是输出关键词或文件路径。

非目标：不接 Evidence Retriever、不做 embedding、不做 Budget Manager、不做 Context Quality 实现。

### 2) 子功能分解

#### F-P3.phase6.10.2-T01-01 ContextPlan 数据契约
- 输入：query、cognitive_mode、intent_type、blocks、evidence_intents。
- 处理：校验 query、budget、confidence，序列化 enum 值。
- 输出：不可变 `ContextPlan`。
- 失败处理：空 query、非法 budget/confidence 抛错。
- 可观测证据：`to_dict()` 中 intent/evidence_intents 为稳定字符串。
- 测试：TC-36102-001。

#### F-P3.phase6.10.2-T01-02 抽象意图分类
- 输入：自然语言 query + cognitive_mode。
- 处理：分类为 identity/current_task/personal_history/technical/emotional/casual。
- 输出：`ContextIntentType`。
- 失败处理：弱匹配降级 casual，不触发具体检索。
- 可观测证据：identity/current_task/personal_history 测试断言。
- 测试：TC-36102-002/003/004。

#### F-P3.phase6.10.2-T01-03 EvidenceIntent 非关键词化
- 输入：共享经历类 query。
- 处理：输出 shared_story/creative_work/life_experience/relationship_origin。
- 输出：抽象 evidence intents，不包含 xiaohongshu 文件或关键词。
- 失败处理：不生成 search_keyword 字段。
- 可观测证据：`小红书` query 的 plan 不含 concrete search path。
- 测试：TC-36102-001。

#### F-P3.phase6.10.2-T01-04 Query Paraphrase Stability
- 输入：四种“小红书/文章/以前写过/重生故事”问法。
- 处理：生成相同 intent_type 和高度重叠 evidence_intents。
- 输出：overlap >= 0.8。
- 失败处理：如果 paraphrase 走不同 intent，测试失败。
- 可观测证据：intersection/union ratio。
- 测试：TC-36102-002。

### 3) 接口与契约

新增：

```text
runtime/context_os/planner/context_intent.py
runtime/context_os/planner/evidence_intent.py
runtime/context_os/planner/context_plan.py
runtime/context_os/planner/planner_policy.py
runtime/context_os/planner/context_planner.py
```

核心 API：

```python
ContextPlanner().plan(query: str, cognitive_mode: str) -> ContextPlan
```

### 4) 数据模型与状态变更

无持久化状态变更。Planner 是纯函数式规划层。

### 5) 实现步骤

1. 新建 `runtime/context_os/planner` 包。
2. 定义 `ContextIntentType` 与 `EvidenceIntentType`。
3. 定义 `ContextPlan` schema。
4. 实现 `PlannerPolicy.decide()`。
5. 实现 `ContextPlanner.plan()` 门面。
6. 新增 planner 单元测试。
7. 跑 planner 测试与全量回归。

### 6) 测试设计与命令

```bash
python3 -m unittest tests.test_phase36102_context_planner_runtime -v
python3 -m unittest discover -s tests
```

预期：4 个新增测试通过；全量 316 tests OK。

### 7) 风险与回滚

风险：Planner 规则退化为关键词检索。缓解：测试明确禁止具体 search keyword/path，要求 evidence_intents 抽象化。

回滚：删除 `runtime/context_os/planner` 与 `tests/test_phase36102_context_planner_runtime.py`，不影响现有 Context Assembly。

### 8) 验收映射

- ACPT-36102-001：小红书 query 生成 personal_history_recall 且不输出 concrete keyword/path。
- ACPT-36102-002：四种 paraphrase intent 相同且 evidence_intents overlap >= 0.8。
- ACPT-36102-003：当前任务 query 要求 active_task + open_loop/project_state evidence intent。
- ACPT-36102-004：身份 query 要求 core_identity + relationship_anchor。
