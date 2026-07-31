from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class TTSQueue:
    """FIFO sentence queue for realtime speech output and future barge-in clear()."""

    _items: deque[str] = field(default_factory=deque)

    def enqueue(self, sentence: str) -> None:
        clean = sentence.strip()
        if clean:
            self._items.append(clean)

    def extend(self, sentences: list[str]) -> None:
        for sentence in sentences:
            self.enqueue(sentence)

    def play_next(self) -> str | None:
        if not self._items:
            return None
        return self._items.popleft()

    def clear(self) -> None:
        self._items.clear()

    def __len__(self) -> int:
        return len(self._items)
