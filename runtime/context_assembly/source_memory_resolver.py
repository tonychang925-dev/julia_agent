from __future__ import annotations

from pathlib import Path

from runtime.cognitive.context_compiler import JuliaContext
from runtime.conversation_archive import TranscriptStore
from runtime.evidence import SemanticContextRetriever

from .models import AssemblySection


class SourceAwareMemoryResolver:
    """Resolve evidence each turn through the unified Semantic Evidence Layer."""

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.semantic_retriever = SemanticContextRetriever(self.project_root)
        self.transcript_store = TranscriptStore.default(self.project_root)

    def resolve(self, user_input: str, *, session_id: str, julia_context: JuliaContext) -> tuple[list[AssemblySection], dict[str, object]]:
        sections: list[AssemblySection] = []
        recent_section, recent_meta = self._recent_conversation_recall(user_input, session_id=session_id)
        if recent_section:
            sections.append(AssemblySection(
                name="recent_conversation_recall_pack",
                content=recent_section,
                source="conversation_archive_recent_recall_runtime",
                priority=96,
                max_chars=1800,
            ))
        semantic_section, semantic_meta = self.semantic_retriever.prompt_section(
            user_input,
            limit=8,
            cognitive_mode=julia_context.cognitive_mode.mode.name,
        )
        if semantic_section:
            sections.append(AssemblySection(
                name="semantic_evidence_pack",
                content=semantic_section,
                source="semantic_context_retrieval_runtime",
                priority=92,
                max_chars=4200,
            ))
        return sections, {
            "recent_conversation_recall": recent_meta,
            "semantic_evidence": semantic_meta,
            # Compatibility keys for existing trace readers. These are now
            # derived from the unified semantic evidence layer rather than three
            # independent retrievers.
            "claude_diary": self._source_summary(semantic_meta, "diary"),
            "conversation_archive": self._source_summary(semantic_meta, "archive"),
            "structured_memory": self._source_summary(semantic_meta, "memory"),
        }
    def _recent_conversation_recall(self, user_input: str, *, session_id: str, limit: int = 5) -> tuple[str, dict[str, object]]:
        if not self._is_recent_recall_query(user_input):
            return "", {"queried": False, "triggered": False, "hit_count": 0, "sources": []}

        records = [record for record in self.transcript_store.tail(30) if record.session_id != session_id]
        selected = records[-max(0, limit):]
        sources = [
            {
                "session_id": record.session_id,
                "turn_id": record.turn_id,
                "timestamp": record.timestamp,
                "cognitive_mode": record.cognitive_mode,
                "user_chars": len(record.user or ""),
                "assistant_chars": len(record.assistant or ""),
            }
            for record in selected
        ]
        meta = {
            "queried": True,
            "triggered": True,
            "hit_count": len(selected),
            "source": "TranscriptStore.tail",
            "excluded_current_session": session_id,
            "sources": sources,
        }
        if not selected:
            return (
                "Recent conversation recall: no prior archived turns found. Say you do not have a concrete recent record instead of inventing one.",
                meta,
            )

        lines = [
            "Recent conversation recall (chronological; use before semantic long-term memory for questions about 上次/刚才/上一轮):",
            "Instruction: answer recent-recall questions from these turns first. If the user asks what happened last time, summarize the newest concrete archived turns rather than defaulting to stable identity/project memories.",
        ]
        for record in selected:
            user = self._compact(record.user, 220)
            assistant = self._compact(record.assistant, 260)
            lines.append(
                f"- {record.timestamp} session={record.session_id} turn={record.turn_id} mode={record.cognitive_mode or 'unknown'}\n"
                f"  Tony: {user}\n"
                f"  Julia: {assistant}"
            )
        return "\n".join(lines), meta

    @staticmethod
    def _is_recent_recall_query(text: str) -> bool:
        lowered = (text or "").lower()
        recall_markers = ("上次", "上一轮", "上轮", "刚才", "刚刚", "之前", "上个会话", "上轮会话", "还记得")
        activity_markers = ("做了什么", "说了什么", "聊了什么", "讲了什么", "谈了什么", "继续", "内容", "事情", "记得")
        return any(marker in lowered for marker in recall_markers) and any(marker in lowered for marker in activity_markers)

    @staticmethod
    def _compact(text: str, limit: int) -> str:
        cleaned = " ".join((text or "").split())
        if len(cleaned) <= limit:
            return cleaned
        return cleaned[:limit].rstrip() + "…"


    @staticmethod
    def _source_summary(meta: dict[str, object], source_type: str) -> dict[str, object]:
        sources = meta.get("sources") if isinstance(meta, dict) else []
        if not isinstance(sources, list):
            sources = []
        filtered = [item for item in sources if isinstance(item, dict) and item.get("source_type") == source_type]
        return {"queried": True, "hit_count": len(filtered), "sources": filtered}
