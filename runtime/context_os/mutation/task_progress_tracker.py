from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TaskProgressTracker:
    def infer_task(self, text: str) -> str | None:
        lowered = text.lower()
        if "context projection" in lowered or "projection" in lowered or "投影" in text:
            return "Context Projection Runtime"
        if "context mutation" in lowered or "mutation" in lowered or "状态转换" in text:
            return "Context Mutation & State Transition Runtime"
        if "claude compact" in lowered or "compact" in lowered:
            return "Claude Compact Analysis"
        if "action runtime" in lowered:
            return "Action Runtime"
        if "下一步" in text or "继续" in text:
            return "Continue current Julia Runtime work"
        return None
