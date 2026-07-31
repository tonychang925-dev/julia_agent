# FEATURE SPEC — P3.phase6.10.6 Session Resurrection Runtime

## Task `P3.phase6.10.6-T01` — Session Resurrection Runtime

### 1) 目标与边界
- 目标：从上一个 session 的 `ExperienceCompactState` 与 preserved active tail 重建新会话启动上下文。
- 目标：生成 `compact_state`、`recent_turns`、`open_loops` ContextBlock，恢复任务连续性、关系连续性与未闭环事项。
- 非目标：不做持久化 store、不自动调用 provider、不实现后台 memory worker。

### 2) 子功能分解

#### F-P3.phase6.10.6-T01-01 SessionSnapshot 创建
- 输入：source session id、compacts、preserved records。
- 处理逻辑：保留 compact ids、tail record ids、open loops、next actions、current task、main arc。
- 输出：`SessionSnapshot`。
- 失败处理：缺失 snapshot/source session id 抛出 `ValueError`。
- 可观测证据：`TC-36106-001`, `TC-36106-003`。

#### F-P3.phase6.10.6-T01-02 Resurrection ContextBlock 重建
- 输入：snapshot + compact states + preserved records。
- 处理逻辑：compact 转为 required `compact_state`，tail 转为 `recent_turns`，open loops 转为 required `open_loops`。
- 输出：list[`ContextBlock`]。
- 失败处理：缺失 compact/tail source 时安全跳过，不编造内容。
- 可观测证据：`TC-36106-002`, `TC-36106-004`。

#### F-P3.phase6.10.6-T01-03 Traceability 保真
- 输入：compact source ids、source_evidence_ids、record ids。
- 处理逻辑：写入 block source_refs/evidence_ids/metadata snapshot_id。
- 输出：可追溯恢复上下文。
- 失败处理：不存在的引用不进入 ContextBlock。
- 可观测证据：`TC-36106-002`。

### 3) 接口与契约
- 新增：`runtime/context_os/session/SessionSnapshot`。
- 新增：`SessionResurrectionEngine.create_snapshot(...) -> SessionSnapshot`。
- 新增：`SessionResurrectionEngine.build_blocks(...) -> list[ContextBlock]`。
- 幂等：相同 snapshot/compacts/records 输入下，block 内容与 source refs 稳定。

### 4) 数据模型与状态变更
- 新增包：`runtime/context_os/session/`。
- 不新增数据库或 JSONL 持久化。
- Snapshot 是 resurrection seed，不替代 transcript/compact 原始来源。

### 5) 实现步骤
1. 定义 `SessionSnapshot` schema。
2. 实现 snapshot creation from compact + tail。
3. 实现 resurrection block builder。
4. 编写 session resurrection 单测。
5. 执行单测与全量回归。

### 6) 测试设计与命令
- `TC-36106-001`：snapshot 保留 compact ids、tail、open loops。
- `TC-36106-002`：build_blocks 重建 compact/open_loops/recent_turns。
- `TC-36106-003`：snapshot 必填字段校验。
- `TC-36106-004`：缺失 compact/tail 安全跳过。

必跑命令：
```bash
python3 -m unittest tests.test_phase36106_session_resurrection -v
python3 -m unittest discover -s tests
```

### 7) 风险与回滚
- 风险：恢复上下文过长；缓解：`max_tail_records` 限制 active tail，后续 Budget Manager 再裁剪。
- 风险：compact 错误会影响恢复；缓解：compact/source ids 保留可追溯，后续 Quality/Conflict Resolver 评估。
- 回滚：删除 `runtime/context_os/session/`、相关 export 与测试，不影响 Evidence/Compact 主链路。

### 8) 验收映射
- `ACPT-36106-001`：可创建可追溯 session snapshot。
- `ACPT-36106-002`：可恢复 compact state、open loops、recent tail。
- `ACPT-36106-003`：缺失引用不导致编造。
- `ACPT-36106-004`：恢复 block 可进入 Context OS 后续预算/组装链路。
