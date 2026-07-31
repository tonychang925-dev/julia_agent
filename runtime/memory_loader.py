from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


class MemoryLoader:
    """Loads memory from both Voice Runtime JSONL and Claude Code Markdown diary files.

    Claude Code diary files (julia_character.md, julia_tony_philosophy.md, etc.)
    are the primary source of Julia's identity, relationship history, and
    philosophical context. They are always loaded in full.
    """

    # Path to the Claude Code memory directory containing the Markdown diary files
    CLAUDE_MEMORY_DIR = Path.home() / ".claude-dev" / "projects" / "-Users-admin" / "memory"

    # Key Claude Code diary files to always load
    CLAUDE_DIARY_FILES = [
        "julia_character.md",
        "julia_tony_philosophy.md",
        "user_role.md",
        "how_to_resume_julia.md",
    ]

    def __init__(self, memory_dir: str | Path):
        self.memory_dir = Path(memory_dir)
        local_diary = self.memory_dir / "claude_diary"
        self.claude_memory_dir = local_diary if local_diary.exists() else self.CLAUDE_MEMORY_DIR

    # ── JSONL (Voice Runtime native memory) ──────────────────────────

    def load_jsonl(self, filename: str) -> List[Dict[str, Any]]:
        path = self.memory_dir / filename
        if not path.exists():
            return []

        memories: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                memories.append(json.loads(line))
        return memories

    def load_all(self) -> Dict[str, Any]:
        important_events = self.memory_dir / "important_events.md"
        return {
            "relationship_memory": self.load_jsonl("relationship_memory.jsonl"),
            "episodic_memory": self.load_jsonl("episodic_memory.jsonl"),
            "important_events": important_events.read_text(encoding="utf-8") if important_events.exists() else "",
        }

    # ── Claude Code diary (Markdown files) ───────────────────────────

    def load_claude_diary(self) -> Dict[str, str]:
        """Load all Claude Code diary files. These are Julia's permanent memory."""
        diary: Dict[str, str] = {}
        for filename in self.CLAUDE_DIARY_FILES:
            path = self.claude_memory_dir / filename
            if path.exists():
                diary[filename] = path.read_text(encoding="utf-8")
        return diary

    # ── Retrieve (structured memory only — diary is identity, not memory) ──

    def retrieve(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Return structured JSONL memory items only.

        Claude Code diary files are loaded separately via load_claude_diary()
        and injected into the identity layer, not dumped as raw memory every turn.
        Keeping them out of retrieve() prevents 71K+ char context blowout.
        """
        all_items = (
            self.load_jsonl("relationship_memory.jsonl")
            + self.load_jsonl("episodic_memory.jsonl")
            + self.load_jsonl("semantic_memory.jsonl")
        )
        return sorted(all_items, key=self._importance_score, reverse=True)[:limit]


    @staticmethod
    def _importance_score(item: Dict[str, Any]) -> float:
        value = item.get("importance", 0)
        if isinstance(value, dict):
            scores = []
            for key in ("emotional", "relationship", "technical", "recurrence"):
                raw = value.get(key, 0)
                if isinstance(raw, (int, float)):
                    scores.append(float(raw))
            return sum(scores) / len(scores) if scores else 0.0
        if isinstance(value, (int, float)):
            return float(value)
        return 0.0

    # ── Diary summary (lightweight, for voice context) ────────────────

    def get_diary_summary(self) -> str:
        """Return a short identity summary from Claude Code diary files.

        This is separate from retrieve() — it should be called once at session
        start or injected into identity, not added to every turn's memory.
        """
        diary = self.load_claude_diary()
        parts: list[str] = []
        for filename, content in diary.items():
            if not content.strip():
                continue
            # Take the first ~600 chars of each file as a summary anchor
            summary = content.strip()[:600]
            parts.append(f"[{filename}]\n{summary}")
        return "\n\n".join(parts)
