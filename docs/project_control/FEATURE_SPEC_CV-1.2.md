# FEATURE SPEC CV-1.2 — Claude Native PTT Voice + TTS Auto-Rearm

Status: IMPLEMENTED-SPIKE / MANUAL PTT GATE PENDING  
Date: 2026-07-30  
Implementation root: `/Users/admin/Claude_Julia_Project`

## Task CV-1.2-T01 — Native PTT Auto-Rearm after Stop Hook TTS

### 1) 目标与边界

目标：保留 Claude Code 原生 `/voice tap` 作为唯一语音输入能力，在 Claude Stop Hook 完成 TTS 播放后，受控触发一次 PTT 快捷键，使下一轮语音输入自动进入 armed/recording 状态。

非目标：

- 不实现自定义 STT。
- 不创建外部 Claude client。
- 不调用 `claude -p`。
- 不做 AppleScript prompt 注入 watcher。
- 不接入 `julia_agent/runtime/*`。
- 不实现完全无人值守连续语音循环。

### 2) 子功能分解

#### F-CV12-T01-01 PTT Auto-Rearm State Control

- 输入：`scripts/claude_ptt_rearm_ctl.sh on|off|status [tap] [key]`。
- 处理逻辑：写入 `tmp/ptt_rearm/state.json`，声明 `auto_rearm_enabled`、`voice_mode=tap`、`ptt_key`。
- 输出：状态 JSON 或简短状态文本。
- 失败处理：未知命令返回 exit=2，不改变状态。
- 可观测证据：`tests/test_cv12_native_ptt_auto_rearm.py::test_cv_ptt_001_ctl_on_off_status_state_file`。

#### F-CV12-T01-02 Stop Hook TTS Output

- 输入：Claude Stop Hook JSON，优先读取 `last_assistant_message`。
- 处理逻辑：通过 `claude_native_tts_hook.py` 执行 `say|dry_run|off` TTS；播放期间写 `/tmp/claude_tts_speaking` 锁。
- 输出：`tmp/ptt_rearm/native_tts_hook_trace.jsonl`。
- 失败处理：空消息/递归 Stop Hook 跳过；TTS 失败只记 trace，Hook exit=0。
- 可观测证据：CV-PTT-004 / CV-PTT-008 单测。

#### F-CV12-T01-03 Guarded PTT Rearm Helper

- 输入：`rearm_claude_ptt.py --turn-key <session:digest> --delay-ms <N>`。
- 处理逻辑：检查 auto-rearm 状态、重复锁、前台 app allowlist，再通过 `osascript` 发送 PTT key。
- 输出：`tmp/ptt_rearm/ptt_rearm_trace.jsonl`。
- 失败处理：状态关闭、重复 turn、前台 app 不匹配、快捷键不支持均 skip 并记录 reason。
- 可观测证据：CV-PTT-002 / CV-PTT-007 单测。

#### F-CV12-T01-04 Project Slash Commands for Rearm Only

- 输入：Claude Code 项目命令 `/ptt-auto-rearm`、`/ptt-auto-rearm-off`、`/ptt-auto-rearm-status`。
- 处理逻辑：只调用 `claude_ptt_rearm_ctl.sh` 控制 rearm 状态。
- 输出：命令结果文本。
- 失败处理：不触碰 Claude cognition，不遮蔽原生 `/voice`。
- 可观测证据：`.claude/commands/ptt-auto-rearm*.md` 存在，旧 daemon voice 命令改名为 `/voice-daemon*`。

### 3) 接口与契约

用户流程：

```text
cd /Users/admin/Claude_Julia_Project
claude
/voice tap
/ptt-auto-rearm
```

运行链路：

```text
Claude native PTT input
  -> Claude native session/context/tools
  -> Stop Hook last_assistant_message
  -> claude_native_tts_hook.py TTS
  -> detached rearm_claude_ptt.py
  -> one-shot PTT key trigger
```

状态文件：

```json
{
  "auto_rearm_enabled": true,
  "voice_mode": "tap",
  "ptt_key": "space"
}
```

### 4) 数据模型与状态变更

新增：

```text
/Users/admin/Claude_Julia_Project/tmp/ptt_rearm/state.json
/Users/admin/Claude_Julia_Project/tmp/ptt_rearm/native_tts_hook_trace.jsonl
/Users/admin/Claude_Julia_Project/tmp/ptt_rearm/ptt_rearm_trace.jsonl
/Users/admin/Claude_Julia_Project/tmp/ptt_rearm/last_rearm.lock
```

Claude cognitive state 不变；Julia Runtime state 不变。

### 5) 实现步骤

1. 新增 `scripts/claude_ptt_rearm_ctl.sh`。
2. 新增 `scripts/claude_native_tts_hook.py`。
3. 新增 `scripts/rearm_claude_ptt.py`。
4. 新增 `.claude/commands/ptt-auto-rearm*.md`。
5. 将旧项目 `/voice` daemon 命令改名为 `/voice-daemon*`，避免遮蔽 Claude 原生 `/voice`。
6. 在 `.claude/settings.local.json` 注册 Stop Hook。
7. 增加 CV-1.2 单测。

### 6) 测试设计与命令

```bash
cd /Users/admin/Claude_Julia_Project
python3 -m unittest tests/test_cv12_native_ptt_auto_rearm.py -v
```

预期：6 tests OK。

手动 gate：

```text
cd /Users/admin/Claude_Julia_Project
claude
/voice tap
/ptt-auto-rearm
```

连续三轮：

1. 用户手动 PTT：`Julia，你能听见我吗？`
2. Hook TTS 播放完成后自动 rearm。
3. 用户说完后按 PTT 提交下一轮。
4. 重复 3 轮，确认 session 不变、无 TTS 回采、无旁路 session。

### 7) 风险与回滚

风险：

- Claude 原生 `/voice` 受账号、feature gate、OAuth、macOS 麦克风权限影响。
- `osascript` 需要 Accessibility 权限。
- Terminal 焦点错误导致 rearm skip。
- `space` 作为 PTT key 可能与输入框行为冲突；可改为 `cmd+k` 等专用绑定。

回滚：

```bash
cd /Users/admin/Claude_Julia_Project
scripts/claude_ptt_rearm_ctl.sh off
```

如需完全回滚，移除 `.claude/settings.local.json` 中的 `claude_native_tts_hook.py` Stop Hook 条目。

### 8) 验收映射

- ACPT-CV12-001：原生 `/voice tap` 是唯一语音输入入口。
- ACPT-CV12-002：Stop Hook TTS 可读取 `last_assistant_message` 并播放。
- ACPT-CV12-003：TTS 成功后只触发一次 PTT rearm。
- ACPT-CV12-004：可通过 `/ptt-auto-rearm-off` 停止。
- ACPT-CV12-005：不调用 `julia_agent/runtime/*`。
- ACPT-CV12-006：不调用 `claude -p`。
