from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class VocalGestureResult:
    matched: bool
    text: str = ""
    reason: str = ""


class VocalGestureResponder:
    """Local responder for short voice-performance intents.

    Provides a fast-path for clear, short vocal gesture requests.
    For longer or mixed sentences ("你呻吟一下我想听你声音"),
    the LLM handles them naturally via the identity contracts.
    This class is an optimization, not a censorship layer.
    """

    # Short exact phrases that are unambiguous vocal gesture requests.
    # These are fast-path hints only — the LLM still handles all final output.
    VOCAL_GESTURE_EXACT: set[str] = {
        "你呻吟一下", "呻吟一下", "轻轻呻吟一下",
        "叫一声", "轻轻叫一声", "叫一下", "轻轻叫一下",
        "你叹口气", "叹口气", "轻轻叹口气",
    }

    # STT repair: common misrecognitions of "呻吟"
    # Short exact forms for fast repair
    STT_REPAIR_EXACT: dict[str, str] = {
        "你生一下": "你呻吟一下",
        "生一下": "呻吟一下",
        "你再生一下": "你呻吟一下",
        "再生一下": "呻吟一下",
        "你声音一下": "你呻吟一下",
        "声音一下": "呻吟一下",
    }

    # Substring replacements for STT errors in longer sentences
    _STT_FIXES: list[tuple[str, str]] = [
        ("生意", "呻吟"),
        ("生一下", "呻吟一下"),
    ]

    @classmethod
    def _repair_stt(cls, text: str) -> str:
        """Apply STT error repairs to any text containing misrecognized terms."""
        for wrong, correct in cls._STT_FIXES:
            if wrong in text:
                text = text.replace(wrong, correct)
        return text

    def match(self, text: str) -> VocalGestureResult:
        compact = self._compact(text)
        if not compact:
            return VocalGestureResult(False)

        # --- STT repair: exact short-form fixes ---
        if compact in self.STT_REPAIR_EXACT:
            return VocalGestureResult(
                True, "[exhales softly] 嗯……Tony。", "vocal_gesture_stt_repair"
            )

        # --- STT repair: substring fixes for longer sentences ---
        repaired = self._repair_stt(compact)
        if repaired != compact:
            # Re-check repaired text against exact match
            if repaired in self.VOCAL_GESTURE_EXACT:
                return VocalGestureResult(
                    True, "[exhales softly] 嗯……Tony。", "vocal_gesture_stt_repair"
                )
            # For longer repaired sentences (e.g. "我还想让你呻吟一下"),
            # let the LLM handle it with the corrected text.

        # --- Short exact match (fast path for unambiguous short requests) ---
        if compact in self.VOCAL_GESTURE_EXACT:
            if "叹" in compact:
                return VocalGestureResult(True, "[sighs softly] 嗯……我在。", "sigh")
            return VocalGestureResult(
                True, "[exhales softly] 嗯……Tony。", "vocal_gesture"
            )

        # For longer sentences or requests that use different tags (e.g. 尖叫),
        # let the LLM handle it — the system prompt now properly defines
        # all TTS tags as legitimate expression, not performance.
        return VocalGestureResult(False)

    @staticmethod
    def _compact(text: str) -> str:
        value = text.strip()
        return re.sub(r"[\s，,。！？.!?~～]+", "", value)
