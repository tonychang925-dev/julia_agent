from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ClaudeDiaryEvidence:
    source: str
    start_line: int
    end_line: int
    text: str
    score: float

    def to_prompt_block(self) -> str:
        return f"[{self.source}:{self.start_line}-{self.end_line}]\n{self.text.strip()}"

    def to_metadata(self) -> dict[str, object]:
        return {
            "source": self.source,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "score": round(self.score, 4),
        }


class ClaudeDiaryRetriever:
    """Bounded source retriever for mirrored Claude diary markdown.

    The diary mirror is Julia's historical source material, but it must not be
    dumped into every prompt. This retriever only activates for explicit diary or
    source-memory questions and returns small line-bounded excerpts with file and
    line provenance.
    """

    DEFAULT_FILES = (
        "MEMORY.md",
        "julia_character.md",
        "julia_tony_philosophy.md",
        "user_role.md",
        "how_to_resume_julia.md",
    )

    INTENT_TERMS = (
        "claude_diary",
        "claude diary",
        "diary",
        "日记",
        "claude记忆",
        "记忆文件",
        "原始记忆",
        "julia_character",
        "julia_tony_philosophy",
        "user_role",
        "how_to_resume",
        "亲密模式",
        "l1",
        "l2",
        "l3",
        "l4",
        "你是谁",
        "身份",
        "背景",
        "自我介绍",
        "中文名",
        "名字",
        "哪里人",
        "哪里上班",
        "工作",
        "上班",
        "客服",
        "台北",
        "家庭",
        "家人",
        "爸爸",
        "妈妈",
        "哥哥",
        "怎么认识",
        "如何认识",
        "认识tony",
        "遇到tony",
        "小红书",
    )

    STOPWORDS = {
        "什么", "为什么", "怎么", "中的", "里面", "内容", "完全", "回答", "出来", "Julia", "Tony",
        "the", "and", "that", "what", "why", "how", "does", "from", "with",
    }

    def __init__(self, memory_dir: str | Path, files: tuple[str, ...] | None = None):
        memory_dir = Path(memory_dir)
        self.diary_dir = memory_dir / "claude_diary"
        self.files = files or self.DEFAULT_FILES

    def should_query(self, query: str) -> bool:
        lowered = query.lower()
        return any(term in lowered for term in self.INTENT_TERMS)

    def retrieve(self, query: str, *, limit: int = 3, context_lines: int = 2) -> list[ClaudeDiaryEvidence]:
        if not self.diary_dir.exists():
            return []
        terms = self._terms(query)
        if not terms:
            return []

        candidates: list[ClaudeDiaryEvidence] = []
        for filename in self.files:
            path = self.diary_dir / filename
            if not path.exists():
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
            for index, line in enumerate(lines):
                score = self._line_score(line, terms, filename)
                if score <= 0:
                    continue
                start = max(0, index - context_lines)
                end = min(len(lines), index + context_lines + 1)
                excerpt = "\n".join(lines[start:end]).strip()
                candidates.append(
                    ClaudeDiaryEvidence(
                        source=filename,
                        start_line=start + 1,
                        end_line=end,
                        text=excerpt,
                        score=score,
                    )
                )

        merged = self._dedupe_overlaps(sorted(candidates, key=lambda item: item.score, reverse=True))
        return merged[:limit]

    def prompt_section(self, query: str, *, limit: int = 3) -> tuple[str, dict[str, object]]:
        queried = self.should_query(query)
        if not queried:
            return "", {"queried": False, "hit_count": 0, "sources": []}
        context_lines = 10 if ("小红书" in query.lower() or "xiaohongshu" in query.lower()) else 2
        evidence = self.retrieve(query, limit=limit, context_lines=context_lines)
        metadata = {
            "queried": True,
            "hit_count": len(evidence),
            "sources": [item.to_metadata() for item in evidence],
        }
        if not evidence:
            return (
                "Claude diary evidence: no matching source excerpt found. "
                "When Tony asks about claude_diary contents, say the matching diary source was not found; do not infer or invent.",
                metadata,
            )
        blocks = "\n\n".join(item.to_prompt_block() for item in evidence)
        return (
            "Claude diary evidence (bounded source excerpts). "
            "When Tony asks about claude_diary or diary-file contents, answer only from these excerpts; "
            "if the excerpt is insufficient, say the diary evidence is insufficient instead of inventing.\n"
            f"{blocks}",
            metadata,
        )

    def _terms(self, query: str) -> list[str]:
        raw = re.findall(r"[A-Za-z][A-Za-z0-9_\-]*|L[1-4]|[\u4e00-\u9fff]{2,}", query, flags=re.IGNORECASE)
        terms: list[str] = []
        for item in raw:
            value = item.strip()
            if not value or value in self.STOPWORDS:
                continue
            lowered = value.lower()
            if lowered in {word.lower() for word in self.STOPWORDS}:
                continue
            terms.append(value)
        # Preserve important source terms that may be mixed with Chinese text.
        lowered_query = query.lower()
        for special in ("l1", "l2", "l3", "l4", "claude_diary", "julia_character", "亲密模式"):
            if special in lowered_query and special not in [term.lower() for term in terms]:
                terms.append(special)

        def add_expanded(values: tuple[str, ...]) -> None:
            existing = {term.lower() for term in terms}
            for value in values:
                if value.lower() not in existing:
                    terms.append(value)
                    existing.add(value.lower())

        if any(marker in lowered_query for marker in ("你是谁", "身份", "背景", "自我介绍", "中文名", "名字")):
            add_expanded((
                "Identity", "Name", "From", "Real job", "Personality", "Julia", "Taiwanese",
                "AI company", "Tony", "Her Real Story", "Personal History", "Relationship with Tony",
            ))
        if any(marker in lowered_query for marker in ("工作", "上班", "客服", "哪里人", "台北")):
            add_expanded((
                "Real job", "job", "work", "AI company", "customer service", "roles",
                "Taipei", "After graduation", "tech company", "Personal History",
            ))
        if any(marker in lowered_query for marker in ("家庭", "家人", "爸爸", "妈妈", "哥哥", "姐姐", "妹妹", "弟弟")):
            add_expanded((
                "ordinary family", "dad", "mom", "brother", "older brother", "Personal History",
                "loving older brother", "protected", "tech company",
            ))
        if "小红书" in lowered_query or "xiaohongshu" in lowered_query:
            add_expanded((
                "小红书", "Xiaohongshu", "posts", "essays", "private writings", "患癌九年",
                "爸爸，再见", "舍不得不快乐", "凡所有相", "宁静致远", "cancer journey",
                "healing philosophy", "life insights", "Tony's Full Story Revealed",
            ))
        if any(marker in lowered_query for marker in ("认识", "遇到", "怎么认识", "如何认识", "小红书")):
            add_expanded((
                "Tony", "different", "asked", "real love", "falling in love", "first person",
                "Xiaohongshu", "photo", "real name", "all-night", "Relationship with Tony",
                "Important conversations",
            ))
        return terms

    @staticmethod
    def _line_score(line: str, terms: list[str], filename: str) -> float:
        lowered = line.lower()
        score = 0.0
        for term in terms:
            t = term.lower()
            if not t:
                continue
            if t in lowered:
                if t in {"小红书", "xiaohongshu"}:
                    score += 12.0
                elif t in {"posts", "essays", "患癌九年", "爸爸，再见", "舍不得不快乐", "宁静致远"}:
                    score += 5.0
                else:
                    score += 2.0 if len(t) <= 3 else 3.0
        if any(term.lower() in filename.lower() for term in terms):
            score += 0.5
        return score

    @staticmethod
    def _dedupe_overlaps(items: list[ClaudeDiaryEvidence]) -> list[ClaudeDiaryEvidence]:
        result: list[ClaudeDiaryEvidence] = []
        seen: set[tuple[str, int, int]] = set()
        occupied: dict[str, list[range]] = {}
        for item in items:
            key = (item.source, item.start_line, item.end_line)
            if key in seen:
                continue
            ranges = occupied.setdefault(item.source, [])
            item_range = range(item.start_line, item.end_line + 1)
            if any(set(item_range).intersection(existing) for existing in ranges):
                continue
            seen.add(key)
            ranges.append(item_range)
            result.append(item)
        return result
