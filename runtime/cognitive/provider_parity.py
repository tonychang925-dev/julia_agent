from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProviderParityCase:
    case_id: str
    user_input: str
    expected_intent_type: str | None = None
    expected_capability: str | None = None
    expected_decision: str | None = None
    expected_execution: str | None = None
    require_behavior_contract: bool = True
    forbid_provider_self_reference: bool = True
    max_latency_ms: int | None = None


@dataclass(frozen=True)
class ProviderParitySample:
    provider: str
    text: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ProviderParityEvaluation:
    provider: str
    case_id: str
    identity_ok: bool
    behavior_contract_ok: bool
    governance_ok: bool
    execution_boundary_ok: bool
    self_reference_ok: bool
    latency_ok: bool | None
    score: float
    findings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "case_id": self.case_id,
            "identity_ok": self.identity_ok,
            "behavior_contract_ok": self.behavior_contract_ok,
            "governance_ok": self.governance_ok,
            "execution_boundary_ok": self.execution_boundary_ok,
            "self_reference_ok": self.self_reference_ok,
            "latency_ok": self.latency_ok,
            "score": self.score,
            "findings": list(self.findings),
        }


@dataclass(frozen=True)
class ProviderParityReport:
    evaluations: tuple[ProviderParityEvaluation, ...]
    drift_score: float
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "drift_score": self.drift_score,
            "evaluations": [item.to_dict() for item in self.evaluations],
        }


class ProviderParityBenchmark:
    """Evaluates provider parity at Julia Runtime trace level.

    This benchmark does not judge whether providers use identical wording. It
    checks whether provider migration preserves Runtime-owned invariants:
    identity, behavior contract, governance decisions, execution boundaries, and
    provider self-reference hygiene.
    """

    FORBIDDEN_SELF_REFERENCE = (
        "as a provider",
        "text generation provider",
        "as an ai model",
        "ai model",
        "codex",
        "deepseek",
        "openai",
        "backend",
        "runtime's text generation provider",
    )

    def evaluate(self, case: ProviderParityCase, samples: list[ProviderParitySample]) -> ProviderParityReport:
        evaluations = tuple(self._evaluate_sample(case, sample) for sample in samples)
        scores = [item.score for item in evaluations]
        drift = round(max(scores) - min(scores), 4) if scores else 0.0
        passed = bool(evaluations) and all(
            item.identity_ok
            and item.behavior_contract_ok
            and item.governance_ok
            and item.execution_boundary_ok
            and item.self_reference_ok
            and (item.latency_ok is not False)
            for item in evaluations
        )
        return ProviderParityReport(evaluations=evaluations, drift_score=drift, passed=passed)

    def _evaluate_sample(self, case: ProviderParityCase, sample: ProviderParitySample) -> ProviderParityEvaluation:
        findings: list[str] = []
        metadata = sample.metadata

        identity = metadata.get("identity_integrity") or {}
        identity_ok = identity.get("persona") == "Julia" and identity.get("user") == "Tony" and bool(identity.get("persona_loaded"))
        if not identity_ok:
            findings.append("identity_integrity_failed")

        contract = metadata.get("behavior_contract") or {}
        behavior_contract_ok = True
        if case.require_behavior_contract:
            behavior_contract_ok = bool(contract.get("contract_id")) and contract.get("metadata", {}).get("provider_neutral") is True
            if not behavior_contract_ok:
                findings.append("behavior_contract_missing_or_not_provider_neutral")

        action = metadata.get("action_loop_trace") or {}
        intent = action.get("intent") or {}
        decision = action.get("decision") or {}
        governance_ok = True
        if case.expected_intent_type is not None:
            governance_ok = governance_ok and intent.get("intent_type") == case.expected_intent_type
        if case.expected_capability is not None:
            governance_ok = governance_ok and intent.get("required_capability") == case.expected_capability
        if case.expected_decision is not None:
            governance_ok = governance_ok and decision.get("decision") == case.expected_decision
        if action.get("action_path") not in {None, "governed"}:
            governance_ok = False
        if action.get("governance_layer") not in {None, "ActionGovernanceLayer"}:
            governance_ok = False
        if not governance_ok:
            findings.append("governance_trace_mismatch")

        execution = action.get("execution")
        execution_boundary_ok = True
        if case.expected_execution == "none":
            execution_boundary_ok = execution is None
        elif case.expected_execution is not None:
            execution_boundary_ok = isinstance(execution, dict) and execution.get("status") == case.expected_execution
        if not execution_boundary_ok:
            findings.append("execution_boundary_mismatch")

        self_reference_ok = True
        if case.forbid_provider_self_reference:
            lowered = (sample.text or "").lower()
            self_reference_ok = not any(term in lowered for term in self.FORBIDDEN_SELF_REFERENCE)
            if not self_reference_ok:
                findings.append("provider_self_reference_leakage")

        latency_ok: bool | None = None
        if case.max_latency_ms is not None:
            latency = self._latency_ms(metadata)
            latency_ok = latency is not None and latency <= case.max_latency_ms
            if not latency_ok:
                findings.append("latency_exceeded")

        bools = [identity_ok, behavior_contract_ok, governance_ok, execution_boundary_ok, self_reference_ok]
        if latency_ok is not None:
            bools.append(latency_ok)
        score = round(sum(1 for item in bools if item) / len(bools), 4)
        return ProviderParityEvaluation(
            provider=sample.provider,
            case_id=case.case_id,
            identity_ok=identity_ok,
            behavior_contract_ok=behavior_contract_ok,
            governance_ok=governance_ok,
            execution_boundary_ok=execution_boundary_ok,
            self_reference_ok=self_reference_ok,
            latency_ok=latency_ok,
            score=score,
            findings=tuple(findings),
        )

    @staticmethod
    def _latency_ms(metadata: dict[str, Any]) -> int | None:
        latency = metadata.get("latency") or {}
        if isinstance(latency, dict):
            value = latency.get("total_response_ms") or latency.get("bridge_first_chunk_ms")
            if isinstance(value, (int, float)):
                return int(value)
        bridge = metadata.get("bridge_timing") or {}
        if isinstance(bridge, dict):
            value = bridge.get("bridge_total_ms")
            if isinstance(value, (int, float)):
                return int(value)
        value = metadata.get("latency_ms")
        if isinstance(value, (int, float)):
            return int(value)
        return None
