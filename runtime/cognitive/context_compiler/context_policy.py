from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContextPolicy:
    """Compilation policy for JuliaContext v2."""

    memory_limit: int = 5
