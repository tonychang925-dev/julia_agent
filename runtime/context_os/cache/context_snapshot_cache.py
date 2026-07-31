from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Generic, TypeVar

from .context_cache_key import ContextCacheKey

T = TypeVar("T")


@dataclass(frozen=True)
class ContextCacheEntry(Generic[T]):
    key_digest: str
    value: T
    created_at: float
    hits: int = 0

    def hit(self) -> "ContextCacheEntry[T]":
        return ContextCacheEntry(
            key_digest=self.key_digest,
            value=self.value,
            created_at=self.created_at,
            hits=self.hits + 1,
        )


@dataclass
class ContextSnapshotCache(Generic[T]):
    """Small deterministic in-memory cache for stable Context OS snapshots."""

    max_entries: int = 64
    _items: dict[str, ContextCacheEntry[T]] = field(default_factory=dict)
    hits: int = 0
    misses: int = 0
    writes: int = 0
    invalidations: int = 0

    def get(self, key: ContextCacheKey) -> T | None:
        digest = key.digest
        entry = self._items.get(digest)
        if entry is None:
            self.misses += 1
            return None
        updated = entry.hit()
        self._items[digest] = updated
        self.hits += 1
        return updated.value

    def set(self, key: ContextCacheKey, value: T) -> None:
        if len(self._items) >= self.max_entries and key.digest not in self._items:
            oldest = min(self._items.values(), key=lambda item: item.created_at)
            self._items.pop(oldest.key_digest, None)
        self._items[key.digest] = ContextCacheEntry(key_digest=key.digest, value=value, created_at=time())
        self.writes += 1

    def invalidate(self, *, reason: str = "manual") -> dict[str, object]:
        count = len(self._items)
        self._items.clear()
        self.invalidations += 1
        return {"invalidated": count, "reason": reason, "invalidations": self.invalidations}

    def stats(self) -> dict[str, int]:
        return {
            "entries": len(self._items),
            "hits": self.hits,
            "misses": self.misses,
            "writes": self.writes,
            "invalidations": self.invalidations,
        }
