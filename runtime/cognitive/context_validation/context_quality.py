from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ContextQualityReport:
    """Quality gate result for JuliaContext v2 before provider rendering."""

    passed: bool
    errors: list[str]
    warnings: list[str]
    metrics: dict[str, Any]
