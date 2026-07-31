from __future__ import annotations

from dataclasses import dataclass

from .context_snapshot_cache import ContextSnapshotCache


@dataclass(frozen=True)
class CacheInvalidationDecision:
    invalidate: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {"invalidate": self.invalidate, "reason": self.reason}


@dataclass(frozen=True)
class ContextCacheInvalidator:
    """Explicit invalidation helper for cache owners."""

    def decide(self, *, previous_version: str | None, current_version: str | None, reason: str) -> CacheInvalidationDecision:
        if previous_version is None:
            return CacheInvalidationDecision(False, "no_previous_version")
        if previous_version != current_version:
            return CacheInvalidationDecision(True, reason)
        return CacheInvalidationDecision(False, "version_unchanged")

    def apply(self, cache: ContextSnapshotCache, decision: CacheInvalidationDecision) -> dict[str, object]:
        if decision.invalidate:
            return cache.invalidate(reason=decision.reason)
        return {"invalidated": 0, "reason": decision.reason, "invalidations": cache.invalidations}
