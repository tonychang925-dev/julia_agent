#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

PROMPT_TEMPLATE = """[VOICE_INPUT session_id={session_id} turn_id={turn_id} correlation_id={correlation_id}]
用户语音：{text}

请以当前项目/记忆中的 Julia/婉婉身份直接回复用户。不要解释桥接机制，不要复述标签。"""


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except Exception as exc:
        print(f"[headless] invalid json {path}: {exc}", file=sys.stderr)
        return None
    return data if isinstance(data, dict) else None


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2))


def cleanup_response_files(*paths: Path) -> None:
    for p in paths:
        try:
            p.unlink()
        except FileNotFoundError:
            pass


def req_key(req: dict[str, Any]) -> str:
    return f"{req.get('session_id')}:{req.get('turn_id')}:{req.get('correlation_id')}"


def build_prompt(req: dict[str, Any]) -> str:
    return PROMPT_TEMPLATE.format(
        session_id=str(req.get("session_id", "unknown")),
        turn_id=str(req.get("turn_id", "unknown")),
        correlation_id=str(req.get("correlation_id", "")),
        text=str(req.get("text", "")).strip(),
    )


def run_claude(
    prompt: str,
    *,
    claude_bin: str,
    cwd: Path,
    timeout_s: float,
    settings: str,
    resume: bool,
    extra_args: list[str],
) -> tuple[bool, str, str, int, int]:
    cmd = [claude_bin]
    if settings:
        cmd += ["--settings", settings]
    # --print/-p is the stable non-interactive path. --continue is optional and
    # useful if the user wants continuity across headless calls.
    if resume:
        cmd += ["--continue"]
    cmd += ["-p", prompt]
    cmd += extra_args
    started = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.time() - started) * 1000)
        out = exc.stdout if isinstance(exc.stdout, str) else ""
        err = exc.stderr if isinstance(exc.stderr, str) else ""
        return False, out, f"timeout after {timeout_s}s\n{err}".strip(), 124, duration_ms
    duration_ms = int((time.time() - started) * 1000)
    return proc.returncode == 0, proc.stdout.strip(), proc.stderr.strip(), proc.returncode, duration_ms


def main() -> int:
    ap = argparse.ArgumentParser(description="Headless Claude Code watcher for Julia voice bridge; no GUI paste or Stop hook required.")
    ap.add_argument("--request", default="/tmp/julia_voice_request.json")
    ap.add_argument("--active", default="/tmp/julia_voice_active.json")
    ap.add_argument("--response-json", default="/tmp/julia_voice_response.json")
    ap.add_argument("--response-txt", default="/tmp/julia_voice_response.txt")
    ap.add_argument("--stream-jsonl", default="/tmp/julia_voice_response.stream.jsonl")
    ap.add_argument("--poll", type=float, default=0.20)
    ap.add_argument("--claude-bin", default=os.environ.get("CLAUDE_BIN", "/Users/admin/bin/claude"))
    ap.add_argument("--cwd", default=os.environ.get("CLAUDE_VOICE_CWD", "/Users/admin/julia_agent"))
    ap.add_argument("--settings", default=os.environ.get("CLAUDE_SETTINGS", ""))
    ap.add_argument("--timeout", type=float, default=float(os.environ.get("CLAUDE_VOICE_TIMEOUT", "180")))
    ap.add_argument("--continue-session", action="store_true", default=os.environ.get("CLAUDE_VOICE_CONTINUE", "0") in {"1", "true", "yes"})
    ap.add_argument("--extra-arg", action="append", default=[], help="Extra arg appended to claude command; repeatable.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    request_path = Path(args.request)
    active_path = Path(args.active)
    response_json = Path(args.response_json)
    response_txt = Path(args.response_txt)
    stream_jsonl = Path(args.stream_jsonl)
    cwd = Path(args.cwd)

    last_key = ""
    print(f"[headless] watching {request_path}; claude={args.claude_bin}; cwd={cwd}; continue={args.continue_session}")
    while True:
        req = read_json(request_path)
        if req:
            key = req_key(req)
            text = str(req.get("text", "")).strip()
            if key != last_key and text:
                cleanup_response_files(response_json, response_txt, stream_jsonl)
                active = {
                    "session_id": req.get("session_id"),
                    "turn_id": req.get("turn_id"),
                    "correlation_id": req.get("correlation_id"),
                    "text": text,
                    "status": "running_claude_headless",
                    "started_at": time.time(),
                    "request_path": str(request_path),
                }
                atomic_write_json(active_path, active)
                prompt = build_prompt(req)
                if args.dry_run:
                    print("[headless] dry-run prompt:")
                    print(prompt)
                    ok, out, err, code, duration_ms = True, "dry-run response", "", 0, 0
                else:
                    print(f"[headless] running claude for {key}: {text[:80]}")
                    ok, out, err, code, duration_ms = run_claude(
                        prompt,
                        claude_bin=args.claude_bin,
                        cwd=cwd,
                        timeout_s=args.timeout,
                        settings=args.settings,
                        resume=args.continue_session,
                        extra_args=args.extra_arg,
                    )
                response_text = out.strip()
                status = "success" if ok and response_text else "error"
                reason = None if status == "success" else (err or f"claude exited {code}" or "empty response")
                payload = {
                    "session_id": str(req.get("session_id", "")),
                    "turn_id": int(req.get("turn_id") or 0),
                    "status": status,
                    "text": response_text,
                    "reason": reason,
                    "metadata": {
                        "model": os.environ.get("ANTHROPIC_MODEL", "claude-code-headless"),
                        "source": "claude_code_headless_watcher",
                        "correlation_id": req.get("correlation_id"),
                        "duration_ms": duration_ms,
                        "returncode": code,
                    },
                }
                atomic_write_json(response_json, payload)
                atomic_write_text(response_txt, response_text)
                atomic_write_text(stream_jsonl, json.dumps({
                    "type": "response_chunk",
                    "session_id": payload["session_id"],
                    "turn_id": payload["turn_id"],
                    "text": response_text,
                    "is_final": True,
                    "status": status,
                    "reason": reason,
                    "metadata": payload["metadata"],
                }, ensure_ascii=False) + "\n")
                active.update({
                    "status": "response_written" if status == "success" else "response_error",
                    "completed_at": time.time(),
                    "response_json": str(response_json),
                    "returncode": code,
                    "error": err[-2000:] if err else None,
                })
                atomic_write_json(active_path, active)
                last_key = key
                print(f"[headless] wrote {status} for {key}; len={len(response_text)}; ms={duration_ms}")
                if reason:
                    print(f"[headless] reason: {reason[:300]}", file=sys.stderr)
                if args.once:
                    return 0 if status == "success" else 1
        time.sleep(max(0.05, args.poll))


if __name__ == "__main__":
    raise SystemExit(main())
