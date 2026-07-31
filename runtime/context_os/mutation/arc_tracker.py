from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class CurrentArcTracker:
    def infer_arc(self, text: str) -> str | None:
        lowered = text.lower()
        if any(term in lowered for term in ["context os", "projection", "mutation", "claude", "上下文"]):
            return "Julia Context OS Architecture"
        if any(term in lowered for term in ["action runtime", "agent", "行动"]):
            return "Julia Autonomous Action Runtime"
        if any(term in lowered for term in ["累", "压力", "难受", "情绪"]):
            return "Emotional Support"
        if re.search(r"phase\s*3\.6\.10", lowered):
            return "Julia Context OS Architecture"
        return None
