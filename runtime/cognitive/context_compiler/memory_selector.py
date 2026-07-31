from __future__ import annotations

from runtime.memory import MemoryObject, MemoryRuntime


class MemorySelector:
    """Selects relevant memories for JuliaContext v2.

    It intentionally returns top-k relevant memory objects, never the full memory
    store, to avoid raw diary/context overload.
    """

    def __init__(self, memory_runtime: MemoryRuntime):
        self.memory_runtime = memory_runtime

    def select(self, user_input: str, *, limit: int) -> list[MemoryObject]:
        return self.memory_runtime.retrieve(user_input, limit=limit)
