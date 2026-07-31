from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.context_compiler import ContextCompiler, ContextPolicy, RuntimeEnvelope
from runtime.cognitive.context_validation import ContextValidator
from runtime.memory import MemoryObject


def envelope() -> RuntimeEnvelope:
    return RuntimeEnvelope(
        session_id="conv_phase356",
        turn_id=1,
        provider="deepseek",
        backend="deepseek-chat",
        timestamp="2026-07-27T00:00:00Z",
        latency_target_ms=1500,
    )


class Phase35ContextValidationTests(unittest.TestCase):
    def test_tc_phase356_001_valid_context_passes_quality_gate(self):
        # TC-PHASE356-001
        context = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=3)).compile(
            envelope(),
            "为什么 Tony 要做 Julia Runtime？",
        ).julia_context

        report = ContextValidator(max_memory_items=5).validate(context)

        self.assertTrue(report.passed, report.errors)
        self.assertEqual(report.errors, [])
        self.assertGreaterEqual(report.metrics["memory_count"], 1)
        self.assertIn("relationship", report.metrics["memory_types"])

    def test_tc_phase356_002_runtime_contamination_fails_gate(self):
        # TC-PHASE356-002
        context = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=1)).compile(
            envelope(),
            "Julia，你是谁？",
        ).julia_context
        contaminated = replace(context, conversation_context={"provider": "deepseek", "backend": "deepseek-chat"})

        report = ContextValidator().validate(contaminated)

        self.assertFalse(report.passed)
        self.assertTrue(any(error.startswith("runtime_contamination:") for error in report.errors))

    def test_tc_phase356_003_excessive_memory_fails_quality_gate(self):
        # TC-PHASE356-003
        context = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=1)).compile(
            envelope(),
            "Julia，你是谁？",
        ).julia_context
        memory = MemoryObject(
            id="memory_extra",
            type="semantic",
            summary="extra memory",
            content={},
            topics=["Julia Runtime"],
            importance={"emotional": 0.1, "relationship": 0.1, "technical": 0.9, "recurrence": 0.1},
            timestamp="2026-07-27",
            source="test",
        )
        overloaded = replace(context, memory_context=[memory, memory, memory])

        report = ContextValidator(max_memory_items=2).validate(overloaded)

        self.assertFalse(report.passed)
        self.assertIn("memory.too_many_items", report.errors)

    def test_tc_phase356_004_situation_memory_mismatch_warns_not_fails(self):
        # TC-PHASE356-004
        context = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=1)).compile(
            envelope(),
            "Julia，你是谁？",
        ).julia_context
        relationship_memory = MemoryObject(
            id="memory_relationship_only",
            type="relationship",
            summary="Tony wants Julia continuity.",
            content={},
            topics=["relationship", "identity continuity"],
            importance={"emotional": 0.9, "relationship": 1.0, "technical": 0.1, "recurrence": 0.8},
            timestamp="2026-07-27",
            source="test",
        )
        mismatch = replace(context, memory_context=[relationship_memory])

        report = ContextValidator(max_memory_items=5).validate(mismatch)

        self.assertTrue(report.passed, report.errors)
        self.assertIn("situation.memory_mismatch:engineering_without_technical_memory", report.warnings)


if __name__ == "__main__":
    unittest.main()
