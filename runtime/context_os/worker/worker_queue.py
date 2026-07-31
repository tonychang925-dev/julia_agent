from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from .worker_event import WorkerEvent


@dataclass
class WorkerQueue:
    """Non-blocking in-memory queue for context maintenance events."""

    _events: deque[WorkerEvent] = field(default_factory=deque)

    def enqueue(self, event: WorkerEvent) -> None:
        self._events.append(event)

    def drain(self, limit: int | None = None) -> list[WorkerEvent]:
        drained: list[WorkerEvent] = []
        while self._events and (limit is None or len(drained) < limit):
            drained.append(self._events.popleft())
        return drained

    def __len__(self) -> int:
        return len(self._events)
