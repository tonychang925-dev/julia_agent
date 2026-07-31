from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.voice_validation import JuliaBirthTestReport, VoiceE2EScenario, VoiceTraceValidator


def trace(*, mode="engineering_collaboration", current_arc="technical_progress", ttfv=1800, memory_text="Julia Runtime independence Cognitive Ownership"):
    return {
        "reasoning": {
            "backend": "deepseek_provider",
            "metadata": {
                "phase35_pipeline": True,
                "bridge": "direct_llm",
                "provider_info": {"name": "deepseek", "model": "deepseek-chat"},
                "context_quality": {"passed": True, "metrics": {"memory_count": 3}},
                "cognitive_mode": {"name": mode, "confidence": 0.9, "evidence": ["test"], "reason": "test"},
                "conversation_continuity": {
                    "current_arc": current_arc,
                    "active_topics": ["Julia Runtime", "Voice Runtime"],
                    "open_loops": [],
                    "session_summary": "Tony and Julia are validating Julia Runtime voice loop.",
                },
                "memory_summary": memory_text,
            },
        },
        "response": {"text": "在呀 Tony，我在。"},
        "audio": {"tts": "elevenlabs_streaming", "ok": True},
        "bridge": "direct_llm",
        "latency": {
            "latency": {
                "speech_to_text_ms": 120,
                "context_compile_ms": 12,
                "bridge_first_chunk_ms": 1000,
                "tts_start_ms": 350,
                "time_to_first_voice_ms": ttfv,
                "total_response_ms": 2400,
            }
        },
    }


class Phase36VoiceCognitiveLoopValidationTests(unittest.TestCase):
    def test_tc_phase366_001_identity_voice_trace(self):
        # TC-PHASE366-001
        scenario = VoiceE2EScenario("E2E-001", "Julia，你是谁？")
        result = VoiceTraceValidator().validate(scenario, trace())

        self.assertTrue(result.passed, result.errors)
        self.assertTrue(result.checks["host_independence"])
        self.assertTrue(result.checks["provider"])
        self.assertTrue(result.checks["tts"])

    def test_tc_phase366_002_memory_recall_trace(self):
        # TC-PHASE366-002
        scenario = VoiceE2EScenario(
            "E2E-002",
            "你记得我们为什么做 Julia Runtime 吗？",
            expected_memory_topics=["Julia Runtime", "Cognitive Ownership"],
        )
        result = VoiceTraceValidator().validate(scenario, trace())

        self.assertTrue(result.passed, result.errors)
        self.assertTrue(result.checks["memory"])

    def test_tc_phase366_003_conversation_continuity_trace(self):
        # TC-PHASE366-003
        scenario = VoiceE2EScenario("E2E-003", "那下一步怎么办？")
        result = VoiceTraceValidator().validate(scenario, trace(current_arc="technical_progress"))

        self.assertTrue(result.passed, result.errors)
        self.assertEqual(result.metrics["current_arc"], "technical_progress")

    def test_tc_phase366_004_cognitive_mode_trace(self):
        # TC-PHASE366-004
        engineering = VoiceTraceValidator().validate(
            VoiceE2EScenario("E2E-004A", "帮我分析 ContextCompiler", expected_mode="engineering_collaboration"),
            trace(mode="engineering_collaboration"),
        )
        emotional = VoiceTraceValidator().validate(
            VoiceE2EScenario("E2E-004B", "今天有点累", expected_mode="emotional_support"),
            trace(mode="emotional_support", current_arc="emotional_check_in"),
        )

        self.assertTrue(engineering.passed, engineering.errors)
        self.assertTrue(emotional.passed, emotional.errors)

    def test_tc_phase366_005_voice_latency_trace(self):
        # TC-PHASE366-005
        ok = VoiceTraceValidator().validate(VoiceE2EScenario("E2E-005", "Julia，在吗？", latency_target_ms=2500), trace(ttfv=1800))
        slow = VoiceTraceValidator().validate(VoiceE2EScenario("E2E-005", "Julia，在吗？", latency_target_ms=2500), trace(ttfv=3800))

        self.assertTrue(ok.passed, ok.errors)
        self.assertFalse(slow.passed)
        self.assertIn("latency_check_failed", slow.errors)

    def test_tc_phase366_006_birth_test_report_markdown(self):
        # TC-PHASE366-006
        result = VoiceTraceValidator().validate(VoiceE2EScenario("E2E-001", "Julia，在吗？"), trace())
        report = JuliaBirthTestReport("Julia Birth Test v1", [result])
        markdown = report.to_markdown()

        self.assertTrue(report.passed)
        self.assertIn("Julia Birth Test v1", markdown)
        self.assertIn("Overall: PASS", markdown)


if __name__ == "__main__":
    unittest.main()
