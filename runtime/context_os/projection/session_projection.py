from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from runtime.context_os.budget import ContextBlock
from runtime.context_os.compact import ExperienceCompactState
from runtime.context_os.session import SessionResurrectionEngine, SessionSnapshot
from runtime.context_os.transcript.message_record import ContextMessageRecord


@dataclass
class SessionProjection:
    resurrection: SessionResurrectionEngine

    def project(
        self,
        *,
        snapshot: SessionSnapshot | None = None,
        compacts: Iterable[ExperienceCompactState] = (),
        preserved_records: Iterable[ContextMessageRecord] = (),
    ) -> list[ContextBlock]:
        if snapshot is None:
            return []
        return self.resurrection.build_blocks(snapshot=snapshot, compacts=compacts, preserved_records=preserved_records)
