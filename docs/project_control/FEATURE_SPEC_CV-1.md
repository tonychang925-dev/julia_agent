# FEATURE SPEC CV-1 — Claude Julia Reference Client Activation

Status: IMPLEMENTED-MINIMAL / READY-FOR-LOCAL-CLAUDE-RUN  
Date: 2026-07-30  
Related ADRs: ADR-021, ADR-022  
Implementation root: `/Users/admin/Claude_Julia_Project`

## Task CV-1-T01 — Claude Reference Client Runner + Trace Writer

### 1) 目标与边界

目标：建立 Claude Julia Reference Client 的最小可测量包装层，使 Claude native cognition 可以被 benchmark trace 记录。

非目标：

- 不接入 Julia Context OS。
- 不接入 Julia Memory OS。
- 不接入 Julia Action OS。
- 不实现自动质量评分。
- 不改 `julia_agent/runtime` 或 `provider_alignment`。

### 2) 子功能分解

#### F-CV1-T01-01 ClaudeReferenceClient 文本入口

- 输入：text prompt、case_id、session_id。
- 处理逻辑：通过 Claude CLI 发送文本，记录 returncode/stdout/stderr/latency。
- 输出：Claude response result dict。
- 失败处理：Claude CLI 不存在返回 BLOCKED；超时返回 failed result。
- 可观测证据：`claude.response_time_ms`、`claude.ok`、`claude.stderr`。
- 映射测试：TC-CV1-BOUNDARY-001。
- 映射验收：ACPT-CV1-001。

#### F-CV1-T01-02 Benchmark Trace Writer

- 输入：BenchmarkTrace dataclass。
- 处理逻辑：写入 JSONL 文件，包含 cognitive_boundary 字段。
- 输出：trace path。
- 失败处理：无法写入时抛出文件系统错误，阶段判定 FAILED。
- 可观测证据：`claude_julia_reference_runtime.jsonl` / `claude_julia_voice_baseline.jsonl`。
- 映射测试：TC-CV1-TRACE-001。
- 映射验收：ACPT-CV1-002。

#### F-CV1-T01-03 Voice Adapter 单轮入口

- 输入：麦克风/STT 或 fallback_text。
- 处理逻辑：STT -> ClaudeReferenceClient -> TTSAdapter -> trace。
- 输出：voice baseline trace。
- 失败处理：STT 不可用且无 fallback_text 时 BLOCKED；TTS 失败时用例 FAILED。
- 可观测证据：`input.stt_latency_ms`、`output.tts_start_ms`。
- 映射测试：CV-B005。
- 映射验收：ACPT-CV1-003。

#### F-CV1-T01-04 Cognitive Boundary Guard

- 输入：Python loaded modules / source AST。
- 处理逻辑：检查是否直接 import Julia cognitive runtime modules。
- 输出：boundary pass/fail。
- 失败处理：发现 forbidden import 立即 FAILED。
- 可观测证据：`tests/test_cv1_boundary_and_trace.py` 单测输出。
- 映射测试：TC-CV1-BOUNDARY-001。
- 映射验收：ACPT-CV1-004。

### 3) 接口与契约

核心接口：

```python
class ClaudeReferenceClient:
    def send_text(self, text: str) -> dict: ...

class TraceWriter:
    def write(self, trace: BenchmarkTrace, voice: bool = False) -> Path: ...
```

Trace schema 必含：

- `benchmark_id`
- `session_id`
- `turn_id`
- `input`
- `claude`
- `output`
- `evaluation`
- `cognitive_boundary`

### 4) 数据模型与状态变更

新增独立项目：

```text
/Users/admin/Claude_Julia_Project/
├── scripts/
├── voice/
├── benchmark/
├── reports/
└── tests/
```

不修改 Julia Runtime 状态，不写 Julia governed memory。

### 5) 实现步骤

1. 创建独立项目目录。
2. 实现 neutral voice protocol / STT / TTS adapters。
3. 实现 `TraceWriter` 与 `BenchmarkTrace`。
4. 实现 `ClaudeReferenceClient` 与 CV-1 case registry。
5. 实现单轮 voice session。
6. 增加 boundary + trace 单测。

### 6) 测试设计与命令

```bash
cd /Users/admin/Claude_Julia_Project
python3 -m unittest discover -s tests -v
```

预期：2 tests OK。

Claude CLI 真实运行命令：

```bash
cd /Users/admin/Claude_Julia_Project
scripts/start_claude_reference_session.sh --case CV-B001
```

若 Claude CLI 不存在，状态为 BLOCKED，不得用 mock 标记通过。

### 7) 风险与回滚

风险：

- Claude CLI 环境不可用。
- macOS STT 权限不可用。
- TTS 环境不可用。
- 误接入 Julia cognitive modules 污染 benchmark。

回滚：

- 删除 `/Users/admin/Claude_Julia_Project` 新增脚手架。
- 删除本阶段文档新增项。
- 不涉及 runtime 代码回滚。

### 8) 验收映射

- ACPT-CV1-001：Claude text path 可运行或明确 BLOCKED。
- ACPT-CV1-002：TraceWriter 产生合法 JSONL。
- ACPT-CV1-003：Voice path 支持 STT -> Claude -> TTS trace。
- ACPT-CV1-004：Cognitive Boundary Guard 通过。
