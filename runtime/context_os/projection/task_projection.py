from __future__ import annotations

from dataclasses import dataclass

from .projection_block import ContextProjectionBlock


@dataclass
class TaskProjection:
    def project(self, current_task: str | None) -> list[ContextProjectionBlock]:
        if not current_task:
            return []
        return [ContextProjectionBlock(
            block_id="projection_active_task",
            block_type="active_task",
            source_refs=["task_state"],
            content=current_task,
            priority=92,
            authority=0.85,
            required=False,
            metadata={"projection": "task"},
        )]
