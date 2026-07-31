from __future__ import annotations

import re
from dataclasses import dataclass

from .context_state import OpenLoopState


@dataclass
class OpenLoopTracker:
    def create_loop(self, *, text: str, source_turn_id: str) -> OpenLoopState | None:
        if any(marker in text for marker in ["下一步", "继续", "待办", "需要", "研究"]):
            title = self._clean_title(text)
            return OpenLoopState(loop_id=f"open_loop_{abs(hash((source_turn_id, title))) % 10**10}", title=title, source_turn_id=source_turn_id)
        return None

    def resolve_loops(self, *, text: str, loops: list[OpenLoopState]) -> list[OpenLoopState]:
        if not any(marker in text for marker in ["完成", "已完成", "解决", "分析完成"]):
            return loops
        resolved: list[OpenLoopState] = []
        for loop in loops:
            if loop.status == "open" and self._overlaps(text, loop.title):
                resolved.append(OpenLoopState(loop_id=loop.loop_id, title=loop.title, status="resolved", source_turn_id=loop.source_turn_id))
            else:
                resolved.append(loop)
        return resolved

    @staticmethod
    def _clean_title(text: str) -> str:
        compact = re.sub(r"\s+", " ", text).strip("。？！ ")
        return compact[:80] or "open loop"

    @staticmethod
    def _overlaps(text: str, title: str) -> bool:
        text_terms = {x for x in re.findall(r"[A-Za-z][A-Za-z0-9_\-]*|[\u4e00-\u9fff]{2,}", text.lower())}
        title_terms = {x for x in re.findall(r"[A-Za-z][A-Za-z0-9_\-]*|[\u4e00-\u9fff]{2,}", title.lower())}
        return bool(text_terms & title_terms)
