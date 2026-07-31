from __future__ import annotations

from dataclasses import dataclass

from runtime.context_os.transcript.message_record import ContextMessageRecord, ProvenanceType
from runtime.context_os.transcript.message_state import CognitiveRole

from .compact_schema import CompactDecision, CompactFailure, CompactLevel, ExperienceCompactState


@dataclass(frozen=True)
class StructuredCompactEngine:
    """Deterministic structured distillation for ContextMessageRecord ranges.

    This first implementation is intentionally rule-based and source-preserving.
    LLM summarization can later fill the same schema, but must not remove source
    record IDs or provenance constraints.
    """

    def compact(
        self,
        *,
        session_id: str,
        records: list[ContextMessageRecord],
        level: CompactLevel = "medium",
    ) -> ExperienceCompactState:
        session_records = [r for r in records if r.session_id == session_id]
        if not session_records:
            raise ValueError("records for session must not be empty")

        ordered = sorted(session_records, key=lambda r: (r.turn_id, r.created_at, r.message_id))
        source_ids = [r.message_id for r in ordered]
        period_start = ordered[0].created_at
        period_end = ordered[-1].created_at

        decisions = self._extract_decisions(ordered)
        failures = self._extract_failures(ordered)
        open_loops = self._extract_open_loops(ordered)
        next_actions = self._extract_next_actions(ordered)
        technical = self._extract_by_role_or_terms(ordered, CognitiveRole.TASK, ["实现", "架构", "runtime", "context", "phase", "测试"])
        relationship = self._extract_by_role_or_terms(ordered, CognitiveRole.RELATIONSHIP, ["tony", "关系", "共同", "julia"])
        emotional = self._extract_by_role_or_terms(ordered, CognitiveRole.EMOTION, ["累", "陪", "情绪", "支持"])
        evidence_ids = self._collect_source_refs(ordered)

        current_task = next_actions[-1] if next_actions else (technical[-1] if technical else "")
        main_arc = self._infer_main_arc(ordered, technical, relationship)
        title = self._infer_title(main_arc, current_task)
        confidence = self._estimate_confidence(ordered)

        return ExperienceCompactState.create(
            session_id=session_id,
            period_start=period_start,
            period_end=period_end,
            source_record_ids=source_ids,
            source_evidence_ids=evidence_ids,
            title=title,
            session_goal=main_arc,
            current_task=current_task,
            main_arc=main_arc,
            decisions=decisions,
            known_failures=failures,
            open_loops=open_loops,
            next_actions=next_actions,
            technical_progress=technical,
            relationship_development=relationship,
            emotional_context=emotional,
            confidence=confidence,
            level=level,
            metadata={
                "record_count": len(ordered),
                "assistant_record_count": sum(1 for r in ordered if r.provenance_type == ProvenanceType.ASSISTANT_RESPONSE),
                "explicit_user_record_count": sum(1 for r in ordered if r.provenance_type == ProvenanceType.EXPLICIT_USER),
            },
        )

    @staticmethod
    def _extract_decisions(records: list[ContextMessageRecord]) -> list[CompactDecision]:
        out: list[CompactDecision] = []
        for r in records:
            text = r.content.strip()
            lowered = text.lower()
            if r.cognitive_role == CognitiveRole.DECISION or any(term in lowered for term in ["决定", "冻结", "采用", "不再", "不要"]):
                out.append(CompactDecision(topic="context_os_decision", decision=text, source_record_ids=[r.message_id]))
        return out[:12]

    @staticmethod
    def _extract_failures(records: list[ContextMessageRecord]) -> list[CompactFailure]:
        out: list[CompactFailure] = []
        for r in records:
            lowered = r.content.lower()
            if any(term in lowered for term in ["失败", "错误", "bug", "不对", "胡编", "截断"]):
                out.append(CompactFailure(failure_type="context_issue", summary=r.content.strip(), source_record_ids=[r.message_id]))
        return out[:10]

    @staticmethod
    def _extract_open_loops(records: list[ContextMessageRecord]) -> list[str]:
        loops: list[str] = []
        for r in records:
            text = r.content.strip()
            lowered = text.lower()
            if any(term in lowered for term in ["下一步", "next", "todo", "继续", "待", "需要"]):
                loops.append(text)
        return _dedupe(loops)[-10:]

    @staticmethod
    def _extract_next_actions(records: list[ContextMessageRecord]) -> list[str]:
        actions: list[str] = []
        for r in records:
            text = r.content.strip()
            lowered = text.lower()
            if any(term in lowered for term in ["下一步", "next", "进入", "实现", "继续"]):
                actions.append(text)
        return _dedupe(actions)[-8:]

    @staticmethod
    def _extract_by_role_or_terms(records: list[ContextMessageRecord], role: CognitiveRole, terms: list[str]) -> list[str]:
        values: list[str] = []
        for r in records:
            lowered = r.content.lower()
            if r.cognitive_role == role or any(term in lowered for term in terms):
                values.append(r.content.strip())
        return _dedupe(values)[-12:]

    @staticmethod
    def _collect_source_refs(records: list[ContextMessageRecord]) -> list[str]:
        refs: list[str] = []
        for r in records:
            refs.extend(r.source_refs)
        return _dedupe(refs)

    @staticmethod
    def _infer_main_arc(records: list[ContextMessageRecord], technical: list[str], relationship: list[str]) -> str:
        combined = "\n".join(r.content for r in records).lower()
        if "context os" in combined or "context" in combined:
            return "Julia Context OS development"
        if "memory" in combined or "记忆" in combined:
            return "Julia Memory Runtime evolution"
        if relationship:
            return "Julia relationship continuity"
        if technical:
            return "Julia technical collaboration"
        return "Julia conversation continuity"

    @staticmethod
    def _infer_title(main_arc: str, current_task: str) -> str:
        if current_task:
            return f"{main_arc}: {current_task[:48]}"
        return main_arc

    @staticmethod
    def _estimate_confidence(records: list[ContextMessageRecord]) -> float:
        if not records:
            return 0.0
        avg_authority = sum(r.authority_score for r in records) / len(records)
        user_ratio = sum(1 for r in records if r.provenance_type == ProvenanceType.EXPLICIT_USER) / len(records)
        return max(0.0, min(1.0, avg_authority * 0.65 + user_ratio * 0.35))


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out
