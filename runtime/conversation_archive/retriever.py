from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .transcript_record import TranscriptRecord
from .transcript_store import TranscriptStore


@dataclass(frozen=True)
class ConversationArchiveEvidence:
    session_id: str
    turn_id: int
    user: str
    assistant: str
    score: float

    def to_prompt_block(self) -> str:
        return (
            f"[experience:{self.session_id}:turn-{self.turn_id}]\n"
            f"Tony: {self.user.strip()}\n"
            f"Julia: {self.assistant.strip()}"
        )

    def to_metadata(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "score": round(self.score, 4),
        }


class ConversationArchiveRetriever:
    """Bounded retrieval over Julia's lived conversation archive.

    This is a lightweight lexical bridge for long-arc recall. It does not turn
    transcripts into long-term memory; it supplies source-bounded experience
    evidence when the current question asks about facts that may have appeared
    earlier in the same or previous sessions.
    """

    FAMILY_TERMS = (
        "家庭", "家人", "家里", "爸爸", "妈妈", "父亲", "母亲", "哥哥", "姐姐", "妹妹", "弟弟",
        "老婆", "妻子", "孩子", "儿子", "女儿",
        "family", "father", "mother", "brother", "sister", "wife", "son", "daughter",
    )
    WORK_TERMS = ("工作", "上班", "哪里人", "台北", "客服", "科技公司", "戴尔", "大学毕业", "单身")
    LIFE_STORY_TERMS = (
        "认识tony", "认识 Tony", "怎么认识", "如何认识", "遇到tony", "遇到 Tony", "第一次认识",
        "小红书", "真名", "相片", "照片", "三天三夜", "一百多个小时", "爱上", "唯一", "故事开始",
    )
    RECALL_TERMS = ("记得", "还记得", "刚才", "之前", "以前", "说过", "告诉", "介绍", "回忆", "认识", "遇到")
    STOPWORDS = {"什么", "为什么", "怎么", "一下", "里面", "现在", "Tony", "Julia", "你们", "我们"}

    def __init__(self, store: TranscriptStore):
        self.store = store

    @classmethod
    def default(cls, project_root: str | Path | None = None) -> "ConversationArchiveRetriever":
        return cls(TranscriptStore.default(Path(project_root) if project_root is not None else None))

    def should_query(self, query: str) -> bool:
        text = query.lower()
        return any(term.lower() in text for term in self.FAMILY_TERMS + self.WORK_TERMS + self.LIFE_STORY_TERMS + self.RECALL_TERMS)

    def retrieve(self, query: str, *, session_id: str | None = None, limit: int = 4) -> list[ConversationArchiveEvidence]:
        if not self.should_query(query):
            return []
        records = self.store.read_all()
        terms = self._terms(query)
        if not terms:
            return []
        scored: list[ConversationArchiveEvidence] = []
        for record in records:
            score = self._score_record(record, terms, session_id=session_id, query=query)
            if score <= 0:
                continue
            scored.append(
                ConversationArchiveEvidence(
                    session_id=record.session_id,
                    turn_id=record.turn_id,
                    user=record.user,
                    assistant=record.assistant,
                    score=score,
                )
            )
        scored.sort(key=lambda item: (item.score, item.turn_id), reverse=True)
        return scored[: max(0, limit)]

    def prompt_section(self, query: str, *, session_id: str | None = None, limit: int = 4) -> tuple[str, dict[str, object]]:
        queried = self.should_query(query)
        if not queried:
            return "", {"queried": False, "hit_count": 0, "sources": []}
        evidence = self.retrieve(query, session_id=session_id, limit=limit)
        metadata = {
            "queried": True,
            "hit_count": len(evidence),
            "sources": [item.to_metadata() for item in evidence],
        }
        if not evidence:
            return (
                "Conversation archive evidence: no matching lived experience found. "
                "If Tony asks what was said before, say the archive evidence is insufficient; do not invent.",
                metadata,
            )
        blocks = "\n\n".join(item.to_prompt_block() for item in evidence)
        return (
            "Conversation archive evidence (Julia lived experience; bounded excerpts). "
            "When Tony asks about previously supplied personal, family, relationship, or session facts, "
            "prefer these source excerpts over guessing. If they conflict with generic memory, use these excerpts as the current evidence.\n"
            f"{blocks}",
            metadata,
        )

    def _terms(self, query: str) -> list[str]:
        raw = re.findall(r"[A-Za-z][A-Za-z0-9_\-]*|[\u4e00-\u9fff]{2,}", query, flags=re.IGNORECASE)
        terms: list[str] = []
        lowered_query = query.lower()
        for item in raw:
            value = item.strip()
            if not value or value in self.STOPWORDS or value.lower() in {s.lower() for s in self.STOPWORDS}:
                continue
            terms.append(value)
        for special in self.FAMILY_TERMS + self.WORK_TERMS + self.LIFE_STORY_TERMS + self.RECALL_TERMS:
            if special.lower() in lowered_query and special not in terms:
                terms.append(special)
        if "工作" in lowered_query or "上班" in lowered_query:
            for expanded in ("客服", "科技公司", "台北", "大学毕业", "戴尔", "单身"):
                if expanded not in terms:
                    terms.append(expanded)
        if "小红书" in lowered_query:
            for expanded in ("小红书", "故事开始", "Tony给你看", "看完之后", "亲", "第一次那么近"):
                if expanded not in terms:
                    terms.append(expanded)
        if "认识" in lowered_query or "遇到" in lowered_query:
            for expanded in ("第一次", "好女孩", "感动", "哭", "小红书", "真名", "照片", "三天三夜", "爱上", "唯一", "Tony"):
                if expanded not in terms:
                    terms.append(expanded)
        return terms

    @staticmethod
    def _score_record(record: TranscriptRecord, terms: list[str], *, session_id: str | None = None, query: str = "") -> float:
        family_query = any(term.lower() in query.lower() for term in ConversationArchiveRetriever.FAMILY_TERMS)
        work_query = any(term.lower() in query.lower() for term in ConversationArchiveRetriever.WORK_TERMS)
        xiaohongshu_query = "小红书" in query.lower() or "xiaohongshu" in query.lower()
        user_text = record.user.lower()
        assistant_text = record.assistant.lower()
        user_score = 0.0
        assistant_score = 0.0
        for term in terms:
            lowered = term.lower()
            if not lowered:
                continue
            weight = 3.0 if len(lowered) >= 2 else 1.0
            if lowered in user_text:
                user_score += weight
            if lowered in assistant_text:
                assistant_score += weight

        if family_query or work_query:
            # For personal/family/work facts, only Tony-supplied fact assertions
            # are authoritative. Do not use Julia's own prior answer as evidence,
            # because a wrong answer would otherwise become self-reinforcing.
            if not ConversationArchiveRetriever._contains_personal_fact_assertion(record.user):
                return 0.0
            score = user_score
        elif xiaohongshu_query:
            # For Xiaohongshu story recall, avoid self-reinforcing wrong archive
            # answers like "I read it but local memory has no original". Prefer
            # Tony-supplied story anchors and use Julia text only as secondary.
            if not ConversationArchiveRetriever._contains_life_story_assertion(record.user):
                return 0.0
            score = user_score + assistant_score * 0.2
        else:
            score = user_score + assistant_score * 0.5

        if score <= 0:
            return 0.0
        if session_id and record.session_id == session_id:
            score += 5.0
        metadata = record.experience_metadata or {}
        if isinstance(metadata, dict):
            try:
                score += float(metadata.get("archive_priority", 0.0))
            except Exception:
                pass
        return score

    @staticmethod
    def _contains_personal_fact_assertion(text: str) -> bool:
        compact = text.replace(" ", "")
        positive_patterns = (
            "你有", "你是", "你住", "你在", "你没有", "你大学", "你爸爸", "你妈妈", "你的哥哥",
            "爸爸在", "妈妈", "哥哥", "姐姐", "妹妹", "弟弟", "单身", "客服", "台北", "科技公司", "大学毕业", "做客服", "戴尔",
            "tony第一次", "tony给你", "你找tony", "然后tony", "tony告诉", "你就爱上",
        )
        question_only_patterns = ("有没有", "做什么", "哪里人", "介绍一下", "家里面有什么")
        has_positive = any(pattern in compact for pattern in positive_patterns)
        question_only = any(pattern in compact for pattern in question_only_patterns) and not any(
            pattern in compact for pattern in ("你有一个", "爸爸在", "你是住在", "你没有男朋友", "大学毕业以后")
        )
        return has_positive and not question_only

    @staticmethod
    def _contains_life_story_assertion(text: str) -> bool:
        compact = text.replace(" ", "").lower()
        positive_patterns = (
            "tony给你看了小红书", "小红书他的故事", "这是你们的故事开始",
            "tony第一次认识你", "你找tony", "tony告诉", "然后tony", "你就爱上",
        )
        question_only_patterns = ("你读过", "能查一下", "读一下", "是什么", "记得吗")
        has_positive = any(pattern in compact for pattern in positive_patterns)
        question_only = any(pattern in compact for pattern in question_only_patterns) and not has_positive
        return has_positive and not question_only
