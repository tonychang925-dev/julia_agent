from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Protocol
from uuid import uuid4

from runtime.context_os.budget import BudgetPressureLevel, CompactPreparationCandidate
from runtime.context_os.transcript.message_record import ContextMessageRecord

from .compact_engine import StructuredCompactEngine
from .compact_schema import CompactLevel, ExperienceCompactState
from .compact_store import InMemoryCompactStore


class CompactExecutionStatus(str, Enum):
    APPLIED = "applied"
    SKIPPED = "skipped"
    REJECTED = "rejected"


@dataclass(frozen=True)
class CompactExecutionRequest:
    """Explicit request to execute a prepared structured compact.

    Phase 3.6.10.11 only prepared candidates. Phase 3.6.10.12 is the first
    runtime that may execute compact, but only when a candidate is explicitly
    supplied and source records are available. Recent tail records remain active
    and are excluded from the compact source range.
    """

    request_id: str
    session_id: str
    candidate: CompactPreparationCandidate
    source_block_ids: list[str] = field(default_factory=list)
    preserve_tail_record_ids: list[str] = field(default_factory=list)
    level: CompactLevel = "medium"
    idempotency_key: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        candidate: CompactPreparationCandidate,
        source_block_ids: list[str] | None = None,
        preserve_tail_record_ids: list[str] | None = None,
        level: CompactLevel = "medium",
        idempotency_key: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> "CompactExecutionRequest":
        key = idempotency_key or f"compact_exec_{candidate.candidate_id}"
        return cls(
            request_id=f"compact_request_{uuid4().hex}",
            session_id=session_id,
            candidate=candidate,
            source_block_ids=list(source_block_ids or candidate.source_block_ids),
            preserve_tail_record_ids=list(preserve_tail_record_ids or []),
            level=level,
            idempotency_key=key,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["candidate"] = self.candidate.to_dict()
        return data


@dataclass(frozen=True)
class CompactExecutionTrace:
    request_id: str
    candidate_id: str
    status: CompactExecutionStatus
    input_record_ids: list[str] = field(default_factory=list)
    compacted_record_ids: list[str] = field(default_factory=list)
    preserved_tail_record_ids: list[str] = field(default_factory=list)
    compact_id: str | None = None
    reason: str = ""
    idempotency_key: str | None = None

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass(frozen=True)
class CompactExecutionResult:
    status: CompactExecutionStatus
    compact: ExperienceCompactState | None
    trace: CompactExecutionTrace

    @property
    def applied(self) -> bool:
        return self.status == CompactExecutionStatus.APPLIED

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "compact": self.compact.to_dict() if self.compact else None,
            "trace": self.trace.to_dict(),
        }


class CompactStore(Protocol):
    def save(self, compact: ExperienceCompactState) -> None: ...
    def get(self, compact_id: str) -> ExperienceCompactState | None: ...


@dataclass
class StructuredCompactRuntime:
    engine: StructuredCompactEngine = field(default_factory=StructuredCompactEngine)
    store: CompactStore = field(default_factory=InMemoryCompactStore)
    min_records: int = 2
    _idempotency_index: dict[str, CompactExecutionResult] = field(default_factory=dict)

    def execute(
        self,
        *,
        request: CompactExecutionRequest,
        records: list[ContextMessageRecord],
    ) -> CompactExecutionResult:
        if request.idempotency_key and request.idempotency_key in self._idempotency_index:
            previous = self._idempotency_index[request.idempotency_key]
            return CompactExecutionResult(
                status=CompactExecutionStatus.SKIPPED,
                compact=previous.compact,
                trace=CompactExecutionTrace(
                    request_id=request.request_id,
                    candidate_id=request.candidate.candidate_id,
                    status=CompactExecutionStatus.SKIPPED,
                    input_record_ids=previous.trace.input_record_ids,
                    compacted_record_ids=previous.trace.compacted_record_ids,
                    preserved_tail_record_ids=previous.trace.preserved_tail_record_ids,
                    compact_id=previous.trace.compact_id,
                    reason="idempotency_key_already_applied",
                    idempotency_key=request.idempotency_key,
                ),
            )

        rejection = self._validate_request(request)
        if rejection:
            return self._result(
                request=request,
                status=CompactExecutionStatus.REJECTED,
                input_records=records,
                compact_records=[],
                reason=rejection,
            )

        session_records = [r for r in records if r.session_id == request.session_id]
        preserve_tail = set(request.preserve_tail_record_ids)
        compact_records = [r for r in session_records if r.message_id not in preserve_tail]
        if request.source_block_ids:
            compact_records = [
                r for r in compact_records
                if r.message_id in request.source_block_ids or any(ref in request.source_block_ids for ref in r.source_refs)
            ]

        compact_records = sorted(compact_records, key=lambda r: (r.turn_id, r.created_at, r.message_id))
        if len(compact_records) < self.min_records:
            return self._result(
                request=request,
                status=CompactExecutionStatus.REJECTED,
                input_records=session_records,
                compact_records=compact_records,
                reason="insufficient_source_records_after_tail_preservation",
            )

        compact = self.engine.compact(session_id=request.session_id, records=compact_records, level=request.level)
        self.store.save(compact)
        result = self._result(
            request=request,
            status=CompactExecutionStatus.APPLIED,
            input_records=session_records,
            compact_records=compact_records,
            reason="structured_compact_applied",
            compact=compact,
        )
        if request.idempotency_key:
            self._idempotency_index[request.idempotency_key] = result
        return result

    @staticmethod
    def _validate_request(request: CompactExecutionRequest) -> str | None:
        if not request.session_id:
            return "session_id_required"
        if not request.candidate.source_block_ids and not request.source_block_ids:
            return "candidate_source_blocks_required"
        if request.candidate.estimated_reclaim_tokens <= 0:
            return "candidate_reclaim_tokens_required"
        if request.candidate.urgency not in {BudgetPressureLevel.HIGH, BudgetPressureLevel.CRITICAL}:
            return "budget_pressure_not_high_enough"
        return None

    @staticmethod
    def _result(
        *,
        request: CompactExecutionRequest,
        status: CompactExecutionStatus,
        input_records: list[ContextMessageRecord],
        compact_records: list[ContextMessageRecord],
        reason: str,
        compact: ExperienceCompactState | None = None,
    ) -> CompactExecutionResult:
        trace = CompactExecutionTrace(
            request_id=request.request_id,
            candidate_id=request.candidate.candidate_id,
            status=status,
            input_record_ids=[r.message_id for r in input_records],
            compacted_record_ids=[r.message_id for r in compact_records],
            preserved_tail_record_ids=list(request.preserve_tail_record_ids),
            compact_id=compact.compact_id if compact else None,
            reason=reason,
            idempotency_key=request.idempotency_key,
        )
        return CompactExecutionResult(status=status, compact=compact, trace=trace)
