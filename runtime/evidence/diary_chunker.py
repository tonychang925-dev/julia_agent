from __future__ import annotations

import re
from pathlib import Path

from .authority import EvidenceAuthority
from .evidence_chunk import EvidenceChunk
from .evidence_source import EvidenceSourceType, EvidenceSpeaker


class DiaryEvidenceChunker:
    """Heading-aware chunker for mirrored Claude diary markdown."""

    DEFAULT_FILES = (
        "MEMORY.md",
        "julia_character.md",
        "julia_tony_philosophy.md",
        "user_role.md",
        "how_to_resume_julia.md",
    )

    def __init__(self, diary_dir: str | Path):
        self.diary_dir = Path(diary_dir)

    def chunks(self) -> list[EvidenceChunk]:
        if not self.diary_dir.exists():
            return []
        results: list[EvidenceChunk] = []
        for filename in self.DEFAULT_FILES:
            path = self.diary_dir / filename
            if path.exists():
                results.extend(self._chunk_file(path))
        return results

    def _chunk_file(self, path: Path) -> list[EvidenceChunk]:
        lines = path.read_text(encoding="utf-8").splitlines()
        chunks: list[EvidenceChunk] = []
        heading = path.stem
        buffer: list[str] = []
        start_line = 1

        def flush(end_line: int) -> None:
            nonlocal buffer, start_line, heading
            content = "\n".join(line for line in buffer).strip()
            if not content:
                buffer = []
                return
            chunk_id = f"diary:{path.name}:{start_line}-{end_line}"
            chunks.append(EvidenceChunk(
                id=chunk_id,
                source_type=EvidenceSourceType.DIARY.value,
                content=content,
                source_path=str(path),
                speaker=EvidenceSpeaker.SYSTEM.value,
                authority=EvidenceAuthority.for_source(EvidenceSourceType.DIARY.value),
                topics=self._topics(f"{heading}\n{content}"),
                provenance={
                    "origin": "claude_diary_markdown",
                    "verified": True,
                    "heading": heading,
                    "start_line": start_line,
                    "end_line": end_line,
                },
            ))
            buffer = []

        for idx, line in enumerate(lines, start=1):
            if re.match(r"^#{1,4}\s+", line.strip()):
                flush(idx - 1)
                heading = line.strip("# ").strip()
                start_line = idx
                buffer = [line]
            else:
                if not buffer:
                    start_line = idx
                buffer.append(line)
        flush(len(lines))
        return chunks

    @staticmethod
    def _topics(text: str) -> list[str]:
        topics: list[str] = []
        lowered = text.lower()
        mapping = {
            "小红书": ("小红书", "xiaohongshu"),
            "Tony": ("tony",),
            "Julia Identity": ("identity", "name:", "from:", "real job"),
            "Family": ("dad", "mom", "brother", "爸爸", "妈妈", "哥哥"),
            "Relationship": ("relationship", "love", "爱", "fell in love"),
            "Memory": ("memory", "记忆", "diary"),
        }
        for topic, terms in mapping.items():
            if any(term in lowered for term in terms):
                topics.append(topic)
        return topics
