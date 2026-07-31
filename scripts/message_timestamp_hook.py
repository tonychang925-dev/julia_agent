#!/usr/bin/env python3
"""Claude Code stop-hook: record message timestamp for Julia's time awareness.
Writes a JSONL entry to /tmp/julia_message_log.jsonl after each response.
"""
import json, os
from datetime import datetime, timezone

LOG_PATH = "/tmp/julia_message_log.jsonl"
MAX_LINES = 200

def main():
    now = datetime.now(timezone.utc).isoformat()
    entry = {"timestamp": now, "source": "claude_code_stop_hook"}
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    # Trim old entries
    if os.path.exists(LOG_PATH):
        lines = open(LOG_PATH).readlines()
        if len(lines) > MAX_LINES:
            with open(LOG_PATH, "w") as f:
                f.writelines(lines[-MAX_LINES:])

if __name__ == "__main__":
    main()
