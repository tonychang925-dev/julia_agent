from __future__ import annotations

from dataclasses import dataclass

from runtime.context_os.budget import ContextBlock
from runtime.context_os.evidence import SemanticEvidenceIntegration
from runtime.context_os.planner.context_plan import ContextPlan


@dataclass
class EvidenceProjection:
    integration: SemanticEvidenceIntegration | None = None

    def project(self, plan: ContextPlan) -> list[ContextBlock]:
        if self.integration is None or not plan.evidence_intents:
            return []
        return self.integration.build_blocks(plan)
