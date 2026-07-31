from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from runtime.memory import StartupMemoryLoader, StartupMemoryPack


@dataclass(frozen=True)
class CoverageResult:
    text: str
    checked_slots: tuple[str, ...]
    missing_slots: tuple[str, ...]
    repaired: bool

    def to_metadata(self) -> dict[str, object]:
        return {
            "checked_slots": list(self.checked_slots),
            "missing_slots": list(self.missing_slots),
            "repaired": self.repaired,
        }


class AnswerCoverageGate:
    """Lightweight multi-slot answer repair for stable personal facts."""

    def __init__(self, project_root: str | Path):
        self.startup_loader = StartupMemoryLoader(project_root)

    def validate_and_repair(self, user_input: str, answer: str) -> CoverageResult:
        slots = self._slots(user_input)
        if not slots:
            return CoverageResult(answer, (), (), False)
        pack = self.startup_loader.load()
        values = self._values(pack)
        missing = tuple(slot for slot in slots if not self._covered(slot, answer, values))
        if not missing:
            return CoverageResult(answer, tuple(slots), (), False)
        repair = self._repair_sentence(missing, values)
        if not repair:
            return CoverageResult(answer, tuple(slots), missing, False)
        sep = "" if answer.rstrip().endswith(("。", "！", "？", ".", "!", "?")) else "。"
        return CoverageResult(f"{answer.rstrip()}{sep}{repair}", tuple(slots), missing, True)

    @staticmethod
    def _slots(text: str) -> list[str]:
        compact = (text or "").replace(" ", "")
        slots: list[str] = []
        if any(term in compact for term in ("哪个大学", "哪所大学", "什么大学", "大学毕业", "学校")):
            slots.append("education.university")
        if any(term in compact for term in ("什么专业", "读什么", "专业", "中文系", "中文专业")):
            slots.append("education.major")
        if "家庭" in compact or "家人" in compact:
            slots.extend(["family.father", "family.mother", "family.brother"])
        if "工作" in compact or "上班" in compact or "职业" in compact:
            slots.append("career.current_work")
        return list(dict.fromkeys(slots))

    @staticmethod
    def _values(pack: StartupMemoryPack) -> dict[str, str]:
        return {fact.field: fact.value for fact in pack.facts}

    @staticmethod
    def _covered(slot: str, answer: str, values: dict[str, str]) -> bool:
        text = answer or ""
        if slot == "education.university":
            return "淡江" in text
        if slot == "education.major":
            return "中文" in text
        if slot == "family.father":
            return "爸爸" in text or "父亲" in text
        if slot == "family.mother":
            return "妈妈" in text or "母亲" in text
        if slot == "family.brother":
            return "哥哥" in text or "朱志豪" in text
        if slot == "career.current_work":
            return "AI" in text and ("公司" in text or "角色" in text or "陪" in text)
        return bool(values.get(slot) and values[slot] in text)

    @staticmethod
    def _repair_sentence(missing: tuple[str, ...], values: dict[str, str]) -> str:
        parts: list[str] = []
        if "education.university" in missing or "education.major" in missing:
            university = values.get("education.university")
            major = values.get("education.major")
            if university and major:
                parts.append(f"学校是{university}，专业是{major}")
        if any(slot.startswith("family.") for slot in missing):
            fam = []
            for slot in ("family.father", "family.mother", "family.brother"):
                if slot in missing and values.get(slot):
                    fam.append(values[slot])
            if fam:
                parts.append("家庭情况是：" + "；".join(fam))
        if "career.current_work" in missing and values.get("career.current_work"):
            parts.append("工作是" + values["career.current_work"])
        if not parts:
            return ""
        return "补充完整：" + "；".join(parts) + "。"
