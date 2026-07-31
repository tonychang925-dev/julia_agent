from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ShortGreetingResult:
    matched: bool
    text: str = ""
    reason: str = ""


class ShortGreetingResponder:
    """Local response strategy for tiny presence-check turns.

    This belongs to Conversation UX, not model cognition. It prevents a simple
    "Julia你在吗" from paying a 3-4s provider first-token cost and from expanding
    into long memory/persona narration.
    """

    def __init__(self, *, wake_word: str = "Julia", response_text: str = "嗯，Tony，我在。"):
        self.wake_word = wake_word
        self.response_text = response_text

    def match(self, text: str) -> ShortGreetingResult:
        compact = self._compact(text)
        if not compact:
            return ShortGreetingResult(False)
        wake = self.wake_word.lower()
        lower = compact.lower()
        patterns = {
            f"{wake}你在吗",
            f"{wake}在吗",
            f"{wake}你在不在",
            f"{wake}在不在",
            "你在吗",
            "在吗",
        }
        if lower in patterns:
            return ShortGreetingResult(True, self.response_text, "presence_check")
        return ShortGreetingResult(False)

    @staticmethod
    def _compact(text: str) -> str:
        value = text.strip()
        value = re.sub(r"[\s，,。！？.!?~～]+", "", value)
        return value
