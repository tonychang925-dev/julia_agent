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

DEFAULT_PROMPT_TEMPLATE = """[VOICE_INPUT session_id={session_id} turn_id={turn_id} correlation_id={correlation_id}]
用户语音：{text}

请直接回复用户。"""


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except Exception as exc:
        print(f"[watcher] invalid json {path}: {exc}", file=sys.stderr)
        return None
    return data if isinstance(data, dict) else None


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def make_prompt(req: dict[str, Any]) -> str:
    text = str(req.get("text", "")).strip()
    return DEFAULT_PROMPT_TEMPLATE.format(
        session_id=str(req.get("session_id", "unknown")),
        turn_id=str(req.get("turn_id", "unknown")),
        correlation_id=str(req.get("correlation_id", "")),
        text=text,
    )


def cleanup_response_files(response_json: Path, response_txt: Path, stream_jsonl: Path) -> None:
    for p in (response_json, response_txt, stream_jsonl):
        try:
            p.unlink()
        except FileNotFoundError:
            pass


def submit_to_frontmost(
    prompt: str,
    *,
    activate_app: str | None,
    window_match: str | None,
    press_return: bool = True,
) -> None:
    # Clipboard paste is more reliable for Chinese and multi-line prompts than keystroke text.
    script = """
on run argv
  set promptText to item 1 of argv
  set shouldReturn to item 2 of argv
  set targetApp to item 3 of argv
  set windowMatch to item 4 of argv
  set the clipboard to promptText
  if targetApp is "Terminal" then
    tell application "Terminal"
      activate
      if windowMatch is not "" then
        repeat with w in windows
          if (name of w) contains windowMatch then
            set index of w to 1
            exit repeat
          end if
        end repeat
      end if
    end tell
    delay 0.15
  else if targetApp is "iTerm" or targetApp is "iTerm2" then
    tell application "iTerm"
      activate
      if windowMatch is not "" then
        repeat with w in windows
          repeat with t in tabs of w
            repeat with s in sessions of t
              if (name of s) contains windowMatch then
                select w
                select t
                select s
                exit repeat
              end if
            end repeat
          end repeat
        end repeat
      end if
    end tell
    delay 0.15
  else if targetApp is not "" then
    tell application targetApp to activate
    delay 0.10
  end if
  tell application "System Events"
    keystroke "v" using command down
    if shouldReturn is "1" then
      key code 36
    end if
  end tell
end run
"""
    subprocess.run(
        [
            "osascript",
            "-e",
            script,
            prompt,
            "1" if press_return else "0",
            activate_app or "",
            window_match or "",
        ],
        check=True,
    )


def request_key(req: dict[str, Any]) -> str:
    return f"{req.get('session_id')}:{req.get('turn_id')}:{req.get('correlation_id')}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Bridge Julia voice requests into the active Claude Code terminal via macOS paste+Enter.")
    ap.add_argument("--request", default="/tmp/julia_voice_request.json")
    ap.add_argument("--active", default="/tmp/julia_voice_active.json")
    ap.add_argument("--response-json", default="/tmp/julia_voice_response.json")
    ap.add_argument("--response-txt", default="/tmp/julia_voice_response.txt")
    ap.add_argument("--stream-jsonl", default="/tmp/julia_voice_response.stream.jsonl")
    ap.add_argument("--poll", type=float, default=0.20)
    ap.add_argument("--app", default="", help="Optional macOS app to activate first, e.g. Terminal, iTerm, WarpTerminal.")
    ap.add_argument("--window-match", default="", help="For Terminal/iTerm: activate the window/session whose title contains this text.")
    ap.add_argument("--no-enter", action="store_true", help="Paste only, do not press Return.")
    ap.add_argument("--dry-run", action="store_true", help="Do not call osascript; print the prompt that would be submitted.")
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    request_path = Path(args.request)
    active_path = Path(args.active)
    response_json = Path(args.response_json)
    response_txt = Path(args.response_txt)
    stream_jsonl = Path(args.stream_jsonl)

    last_key = ""
    target = "frontmost app" if not args.app else args.app
    if args.window_match:
        target += f" window~{args.window_match!r}"
    print(f"[watcher] watching {request_path}; target={target}")
    while True:
        req = read_json(request_path)
        if req:
            key = request_key(req)
            text = str(req.get("text", "")).strip()
            if key != last_key and text:
                cleanup_response_files(response_json, response_txt, stream_jsonl)
                active = {
                    "session_id": req.get("session_id"),
                    "turn_id": req.get("turn_id"),
                    "correlation_id": req.get("correlation_id"),
                    "text": text,
                    "status": "submitted_to_claude_code",
                    "submitted_at": time.time(),
                    "request_path": str(request_path),
                }
                atomic_write_json(active_path, active)
                prompt = make_prompt(req)
                try:
                    if args.dry_run:
                        print("[watcher] dry-run prompt:")
                        print(prompt)
                    else:
                        submit_to_frontmost(
                            prompt,
                            activate_app=args.app or None,
                            window_match=args.window_match or None,
                            press_return=not args.no_enter,
                        )
                except Exception as exc:
                    active["status"] = "submit_failed"
                    active["error"] = str(exc)
                    atomic_write_json(active_path, active)
                    print(f"[watcher] submit failed for {key}: {exc}", file=sys.stderr)
                    if args.once:
                        return 1
                else:
                    last_key = key
                    print(f"[watcher] submitted {key}: {text[:80]}")
                    if args.once:
                        return 0
        time.sleep(max(0.05, args.poll))


if __name__ == "__main__":
    raise SystemExit(main())
