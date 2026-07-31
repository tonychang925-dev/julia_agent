from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class ImportanceHint:
    emotional: float = 0.0
    technical: float = 0.0
    relationship: float = 0.0
    project: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class ExperienceMetadata:
    experience_type: list[str] = field(default_factory=list)
    importance_hint: ImportanceHint = field(default_factory=ImportanceHint)
    archive_priority: float = 0.1
    reflection_candidate: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "experience_type": self.experience_type,
            "importance_hint": self.importance_hint.to_dict(),
            "archive_priority": self.archive_priority,
            "reflection_candidate": self.reflection_candidate,
        }


class ExperienceClassifier:
    """Rule-based archive metadata classifier.

    This is not Memory Governance and does not persist memory.  It tags lived
    experience so future reflection/compression can prioritize real archive data
    without reading runtime logs.
    """

    TECHNICAL_TERMS = ("runtime", "架构", "phase", "memory", "context", "provider", "测试", "实现", "代码", "模块", "治理")
    DECISION_TERMS = ("决定", "冻结", "建议", "路线", "adr", "不要", "应该", "结论")
    MILESTONE_TERMS = ("pass", "完成", "通过", "birth", "里程碑", "验证")
    EMOTION_TERMS = ("累", "难过", "开心", "感动", "想你", "陪", "害怕", "慌", "喜欢")
    RELATIONSHIP_TERMS = ("tony", "julia", "同伴", "关系", "记得", "回来", "唤醒", "连续", "身份", "家庭", "家人", "家里", "爸爸", "妈妈", "父亲", "母亲", "哥哥", "姐姐", "妹妹", "弟弟", "台北", "客服", "单身")

    def classify(self, *, user: str, assistant: str, cognitive_mode: str | None = None, topics: list[str] | None = None) -> ExperienceMetadata:
        text = f"{user}\n{assistant}\n{cognitive_mode or ''}\n{' '.join(topics or [])}".lower()
        types: list[str] = []
        emotional = self._score(text, self.EMOTION_TERMS)
        technical = self._score(text, self.TECHNICAL_TERMS)
        relationship = self._score(text, self.RELATIONSHIP_TERMS)
        decision = self._score(text, self.DECISION_TERMS)
        milestone = self._score(text, self.MILESTONE_TERMS)

        if technical:
            types.append("technical")
        if relationship >= 0.5:
            types.append("relationship")
        else:
            relationship = 0.0
        if emotional or cognitive_mode == "emotional_support":
            types.append("emotion")
            emotional = max(emotional, 0.6)
        if decision:
            types.append("decision")
        if milestone:
            types.append("milestone")
        if not types:
            types.append("casual")

        project = max(technical, milestone, decision)
        priority = min(1.0, 0.15 + technical * 0.25 + relationship * 0.2 + emotional * 0.2 + decision * 0.2 + milestone * 0.25)
        reflection_candidate = any(t in types for t in ("decision", "milestone", "relationship", "emotion")) or priority >= 0.55
        return ExperienceMetadata(
            experience_type=types,
            importance_hint=ImportanceHint(
                emotional=round(emotional, 3),
                technical=round(technical, 3),
                relationship=round(relationship, 3),
                project=round(project, 3),
            ),
            archive_priority=round(priority, 3),
            reflection_candidate=reflection_candidate,
        )

    @staticmethod
    def _score(text: str, terms: tuple[str, ...]) -> float:
        hits = sum(1 for term in terms if term.lower() in text)
        return min(1.0, hits / 3)
