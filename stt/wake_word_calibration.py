from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WakeWordSample:
    raw_text: str
    normalized_text: str
    intended_wake_word: str = "Julia"
    accepted: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class WakeWordCalibrationStore:
    """Stores Tony-specific wake-word STT observations as JSONL.

    A sample is useful only when the raw STT output preserves the intended
    sentence tail. For example:

        raw:        对啊你在吗
        normalized: Julia你在吗。

    teaches both an exact alias (对啊 -> Julia) and, after repeated samples, a
    wake-query template (<short-prefix>你在吗 -> Julia你在吗). Bad captures such
    as "嗯" or "你在吗" are kept for audit but excluded from learning.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, sample: WakeWordSample) -> None:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(sample.to_dict(), ensure_ascii=False) + "\n")

    def load(self) -> list[WakeWordSample]:
        if not self.path.exists():
            return []
        samples: list[WakeWordSample] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            samples.append(
                WakeWordSample(
                    raw_text=str(data.get("raw_text", "")),
                    normalized_text=str(data.get("normalized_text", "")),
                    intended_wake_word=str(data.get("intended_wake_word", "Julia")),
                    accepted=bool(data.get("accepted", True)),
                    metadata=dict(data.get("metadata", {})),
                )
            )
        return samples

    @staticmethod
    def _strip_terminal_punctuation(text: str) -> str:
        return text.strip().rstrip("。！？.!?").replace("，", "").replace(",", "").replace(" ", "")

    @classmethod
    def sample_learning_parts(cls, sample: WakeWordSample, *, intended_wake_word: str = "Julia") -> tuple[str, str] | None:
        raw = cls._strip_terminal_punctuation(sample.raw_text)
        normalized = cls._strip_terminal_punctuation(sample.normalized_text)
        if not sample.accepted or not raw or not normalized:
            return None
        if not normalized.startswith(intended_wake_word):
            return None
        suffix = normalized[len(intended_wake_word):]
        if not suffix or not raw.endswith(suffix):
            return None
        alias = raw[: -len(suffix)]
        # Empty alias means STT omitted the wake word entirely; it is evidence of
        # capture failure, not a learnable pronunciation.
        if not alias:
            return None
        # Single filler outputs should not become aliases.
        if alias in {"嗯", "啊", "呃", "额", "哦"}:
            return None
        return alias, suffix

    @classmethod
    def is_trainable_sample(cls, raw_text: str, normalized_text: str, *, intended_wake_word: str = "Julia") -> bool:
        return cls.sample_learning_parts(
            WakeWordSample(raw_text=raw_text, normalized_text=normalized_text, intended_wake_word=intended_wake_word),
            intended_wake_word=intended_wake_word,
        ) is not None

    def aliases(self, *, intended_wake_word: str = "Julia") -> list[str]:
        aliases: set[str] = set()
        for sample in self.load():
            parts = self.sample_learning_parts(sample, intended_wake_word=intended_wake_word)
            if parts:
                aliases.add(parts[0])
        return sorted(aliases, key=len, reverse=True)

    def learned_suffixes(self, *, intended_wake_word: str = "Julia", min_support: int = 2) -> list[str]:
        counts: dict[str, int] = {}
        for sample in self.load():
            parts = self.sample_learning_parts(sample, intended_wake_word=intended_wake_word)
            if not parts:
                continue
            _, suffix = parts
            counts[suffix] = counts.get(suffix, 0) + 1
        return sorted([suffix for suffix, count in counts.items() if count >= min_support], key=len, reverse=True)


class WakeWordAliasCorrector:
    """Applies persisted Tony-specific wake-word training before fixed rules."""

    def __init__(self, store: WakeWordCalibrationStore, intended_wake_word: str = "Julia"):
        self.store = store
        self.intended_wake_word = intended_wake_word

    def correct(self, text: str) -> str:
        value = text.strip()
        compact = WakeWordCalibrationStore._strip_terminal_punctuation(value)

        # 1) Exact learned aliases.
        for alias in self.store.aliases(intended_wake_word=self.intended_wake_word):
            if compact.startswith(alias):
                corrected_compact = self.intended_wake_word + compact[len(alias):]
                return self._restore_terminal_punctuation(corrected_compact, value)

        # 2) Learned wake-query templates. If Tony has repeatedly trained
        # "Julia你在吗。", then unseen short homophones like "助力呀你在吗" should
        # normalize without adding another hardcoded alias.
        for suffix in self.store.learned_suffixes(intended_wake_word=self.intended_wake_word):
            if compact == suffix:
                # Fast English wake-word pronunciations can be dropped entirely
                # by Apple Speech: "Julia你在吗" -> "你在吗". Only recover
                # suffixes already learned from at least two valid supervised
                # samples, so a random untrained sentence is not rewritten.
                corrected_compact = self.intended_wake_word + suffix
                return self._restore_terminal_punctuation(corrected_compact, value)
            if compact.endswith(suffix):
                prefix = compact[: -len(suffix)]
                if prefix.startswith(("你好", "Tony", "托尼")):
                    continue
                if 1 <= len(prefix) <= 4 and self.intended_wake_word.lower() not in prefix.lower():
                    corrected_compact = self.intended_wake_word + suffix
                    return self._restore_terminal_punctuation(corrected_compact, value)
        return value

    @staticmethod
    def _restore_terminal_punctuation(compact: str, original: str) -> str:
        original = original.strip()
        if original.endswith(("。", "！", "？", ".", "!", "?")):
            return compact + original[-1]
        return compact
