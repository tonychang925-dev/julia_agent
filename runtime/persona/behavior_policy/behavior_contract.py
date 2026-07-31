from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BehaviorContract:
    contract_id: str
    mode: str
    directives: tuple[str, ...]
    provider_drift_guards: tuple[str, ...]
    boundary_style: tuple[str, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def render_lines(self) -> list[str]:
        lines = [
            f"Behavior Contract: {self.contract_id}",
            f"Mode: {self.mode}",
            "Directives:",
            *[f"- {item}" for item in self.directives],
            "Provider drift guards:",
            *[f"- {item}" for item in self.provider_drift_guards],
            "Boundary style:",
            *[f"- {item}" for item in self.boundary_style],
        ]
        return lines

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "mode": self.mode,
            "directives": list(self.directives),
            "provider_drift_guards": list(self.provider_drift_guards),
            "boundary_style": list(self.boundary_style),
            "metadata": dict(self.metadata),
        }
