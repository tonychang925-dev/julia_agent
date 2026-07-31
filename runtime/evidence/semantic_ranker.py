from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone

from .evidence_chunk import EvidenceChunk


@dataclass(frozen=True)
class RankedEvidence:
    chunk: EvidenceChunk
    semantic_similarity: float
    authority: float
    memory_importance: float
    recency: float
    final_score: float
    reason: list[str]


class AuthorityAwareSemanticRanker:
    """Dependency-free semantic-ish ranker for v1.

    It uses normalized lexical/char ngram overlap as a local fallback while
    keeping the scoring contract ready for real embeddings.
    """

    def rank(self, query: str, chunks: list[EvidenceChunk], *, limit: int = 8) -> list[RankedEvidence]:
        query_terms = self._terms(query)
        ranked: list[RankedEvidence] = []
        for chunk in chunks:
            similarity = self._similarity(query, query_terms, chunk.content)
            topic_bonus = self._topic_bonus(query_terms, chunk.topics)
            semantic = min(1.0, similarity + topic_bonus)
            if semantic <= 0 and not self._must_keep(query, chunk):
                continue
            if semantic < 0.08 and not self._must_keep(query, chunk):
                # Authority resolves conflicts among relevant evidence; it must
                # not make weakly related generic memories outrank source facts.
                continue
            memory_importance = self._memory_importance(chunk)
            recency = self._recency(chunk)
            final = semantic * 0.45 + chunk.authority * 0.30 + memory_importance * 0.15 + recency * 0.10
            reason: list[str] = []
            if semantic > 0:
                reason.append("semantic_match")
            if chunk.authority >= 0.9:
                reason.append("high_authority")
            if memory_importance > 0:
                reason.append("memory_importance")
            if recency > 0:
                reason.append("recency")
            ranked.append(RankedEvidence(
                chunk=chunk,
                semantic_similarity=round(semantic, 4),
                authority=chunk.authority,
                memory_importance=round(memory_importance, 4),
                recency=round(recency, 4),
                final_score=round(final, 4),
                reason=reason,
            ))
        ranked.sort(key=lambda item: item.final_score, reverse=True)
        return ranked[: max(0, limit)]

    @staticmethod
    def _terms(text: str) -> list[str]:
        raw = re.findall(r"[A-Za-z][A-Za-z0-9_\-]*|[\u4e00-\u9fff]{2,}", text, flags=re.IGNORECASE)
        terms: list[str] = []
        lowered = text.lower()
        for value in raw:
            v = value.strip()
            if v and v not in {"什么", "怎么", "为什么", "一下", "这个", "那个"}:
                terms.append(v)
        expansions = {
            "小红书": ("xiaohongshu", "posts", "essays", "患癌九年", "爸爸，再见", "故事"),
            "故事": ("story", "posts", "essays", "journey"),
            "帖子": ("小红书", "xiaohongshu", "posts", "essays", "患癌九年", "爸爸，再见"),
            "看过": ("shared", "posts", "essays", "xiaohongshu"),
            "讲了": ("story", "journey", "posts", "essays"),
            "认识": ("met", "first", "different", "love", "tony", "小红书", "xiaohongshu", "story"),
            "工作": ("job", "work", "company", "客服"),
        }
        existing = {term.lower() for term in terms}
        for marker, values in expansions.items():
            if marker in lowered:
                for item in values:
                    if item.lower() not in existing:
                        terms.append(item)
                        existing.add(item.lower())
        return terms

    def _similarity(self, query: str, terms: list[str], content: str) -> float:
        lowered = content.lower()
        hits = 0.0
        for term in terms:
            t = term.lower()
            if t and t in lowered:
                hits += 2.0 if t in {"小红书", "xiaohongshu"} else 1.0
        char_overlap = self._char_bigram_overlap(query, content)
        term_score = min(1.0, hits / max(3.0, len(terms)))
        return max(term_score, char_overlap)

    @staticmethod
    def _char_bigram_overlap(a: str, b: str) -> float:
        def grams(s: str) -> set[str]:
            compact = re.sub(r"\s+", "", s.lower())
            return {compact[i:i+2] for i in range(max(0, len(compact) - 1)) if compact[i:i+2].strip()}
        ga, gb = grams(a), grams(b)
        if not ga or not gb:
            return 0.0
        return len(ga & gb) / len(ga | gb)

    @staticmethod
    def _topic_bonus(query_terms: list[str], topics: list[str]) -> float:
        if not topics:
            return 0.0
        joined = " ".join(topics).lower()
        hits = sum(1 for term in query_terms if term.lower() in joined)
        return min(0.2, hits * 0.05)

    @staticmethod
    def _memory_importance(chunk: EvidenceChunk) -> float:
        raw = chunk.provenance.get("importance") if isinstance(chunk.provenance, dict) else None
        if isinstance(raw, (int, float)):
            return max(0.0, min(1.0, float(raw)))
        if isinstance(raw, dict):
            values = [float(v) for v in raw.values() if isinstance(v, (int, float))]
            return max(0.0, min(1.0, sum(values) / len(values))) if values else 0.0
        return 0.0

    @staticmethod
    def _recency(chunk: EvidenceChunk) -> float:
        if not chunk.timestamp:
            return 0.0
        try:
            ts = datetime.fromisoformat(chunk.timestamp.replace("Z", "+00:00"))
        except ValueError:
            return 0.0
        days = max(0.0, (datetime.now(timezone.utc) - ts).total_seconds() / 86400)
        return math.exp(-days / 30.0)

    @staticmethod
    def _must_keep(query: str, chunk: EvidenceChunk) -> bool:
        lowered_query = query.lower()
        lowered_content = chunk.content.lower()
        return "小红书" in lowered_query and ("小红书" in lowered_content or "xiaohongshu" in lowered_content)
