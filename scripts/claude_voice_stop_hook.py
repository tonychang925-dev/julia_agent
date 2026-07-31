#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

ACTIVE = Path(os.environ.get("JULIA_VOICE_ACTIVE", "/tmp/julia_voice_active.json"))
RESPONSE_JSON = Path(os.environ.get("JULIA_VOICE_RESPONSE_JSON", "/tmp/julia_voice_response.json"))
RESPONSE_TXT = Path(os.environ.get("JULIA_VOICE_RESPONSE_TXT", "/tmp/julia_voice_response.txt"))
STREAM_JSONL = Path(os.environ.get("JULIA_VOICE_STREAM_JSONL", "/tmp/julia_voice_response.stream.jsonl"))
DEBUG = Path(os.environ.get("JULIA_VOICE_HOOK_DEBUG", "/tmp/julia_voice_hook_debug.log"))


def log(msg: str) -> None:
    try:
        DEBUG.parent.mkdir(parents=True, exist_ok=True)
        with DEBUG.open("a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except Exception as exc:
        log(f"invalid json {path}: {exc}")
        return None
    return data if isinstance(data, dict) else None


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_write(path, json.dumps(payload, ensure_ascii=False, indent=2))


def extract_text(data: dict[str, Any]) -> str:
    text = str(data.get("last_assistant_message", "") or "").strip()
    if text:
        return text
    for key in ("response", "last_message", "message"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    messages = data.get("messages")
    if isinstance(messages, list):
        for m in reversed(messages):
            if not isinstance(m, dict):
                continue
            if m.get("role") not in ("assistant", "model"):
                continue
            c = m.get("content", "")
            if isinstance(c, str) and c.strip():
                return c.strip()
            if isinstance(c, list):
                parts: list[str] = []
                for p in c:
                    if isinstance(p, dict) and isinstance(p.get("text"), str):
                        parts.append(p["text"])
                joined = "".join(parts).strip()
                if joined:
                    return joined
    return ""


def main() -> int:
    raw = sys.stdin.read()
    try:
        hook = json.loads(raw) if raw.strip() else {}
    except Exception as exc:
        log(f"hook stdin invalid json: {exc}; raw_len={len(raw)}")
        return 0
    if not isinstance(hook, dict):
        return 0

    active = load_json(ACTIVE)
    if not active or active.get("status") not in {"submitted_to_claude_code", "submit_failed"}:
        log("skip: no active voice request")
        return 0

    text = extract_text(hook)
    if not text:
        log("skip: empty assistant text")
        return 0

    payload = {
        "session_id": str(active.get("session_id", "")),
        "turn_id": int(active.get("turn_id") or 0),
        "text": text,
        "status": "success",
        "reason": None,
        "metadata": {
            "model": str(hook.get("model", "claude-code")),
            "source": "claude_code_stop_hook",
            "correlation_id": active.get("correlation_id"),
            "written_at": time.time(),
        },
    }

    atomic_write_json(RESPONSE_JSON, payload)
    atomic_write(RESPONSE_TXT, text)
    # A final-only stream line is useful for debugging and future tailers, but the bridge can also use response_json.
    stream_line = {
        "type": "response_chunk",
        "session_id": payload["session_id"],
        "turn_id": payload["turn_id"],
        "text": text,
        "is_final": True,
        "status": "success",
        "metadata": payload["metadata"],
    }
    atomic_write(STREAM_JSONL, json.dumps(stream_line, ensure_ascii=False) + "\n")

    active["status"] = "response_written"
    active["response_json"] = str(RESPONSE_JSON)
    active["completed_at"] = time.time()
    atomic_write_json(ACTIVE, active)
    log(f"wrote response for {payload['session_id']}:{payload['turn_id']} len={len(text)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
