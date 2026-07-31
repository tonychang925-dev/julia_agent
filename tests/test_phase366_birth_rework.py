from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.context_compiler import ContextCompiler, ContextPolicy, RuntimeEnvelope
from stt.speech_lab_stt import SpeechLabSTT, SpeechLabSTTConfig


def envelope(turn_id: int = 1) -> RuntimeEnvelope:
    return RuntimeEnvelope(
        session_id="conv_birth_rework",
        turn_id=turn_id,
        provider="deepseek",
        backend="deepseek-chat",
        timestamp="2026-07-27T00:00:00Z",
        latency_target_ms=1500,
    )


class Phase366BirthReworkTests(unittest.TestCase):
    def test_tc_phase3662_001_emotional_intent_overrides_recent_engineering_mode(self):
        compiler = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=3))
        previous = compiler.compile(envelope(1), "帮我分析 ContextCompiler。")
        recent_turn = {"user": "帮我分析 ContextCompiler。", "assistant": "我们看架构。", "cognitive_mode": previous.julia_context.cognitive_mode.mode.name}

        current = compiler.compile(
            envelope(2),
            "今天有点累。",
            conversation_context={"recent_turns": [recent_turn]},
        )

        self.assertEqual(current.julia_context.cognitive_mode.mode.name, "emotional_support")
        self.assertIn("explicit_emotional_expression", current.julia_context.cognitive_mode.evidence)

    def test_tc_phase3662_002_relationship_intent_overrides_recent_engineering_mode(self):
        compiler = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=3))
        recent_turn = {"user": "帮我分析 ContextCompiler。", "assistant": "我们看架构。", "cognitive_mode": "engineering_collaboration"}

        current = compiler.compile(
            envelope(2),
            "你知道情人。",
            conversation_context={"recent_turns": [recent_turn]},
        )

        self.assertEqual(current.julia_context.cognitive_mode.mode.name, "private_voice_continuity")
        self.assertIn("explicit_relationship_continuation", current.julia_context.cognitive_mode.evidence)

    def test_tc_phase3662_003_recent_turn_id_is_allowed_inside_conversation_state_validation(self):
        from runtime.cognitive.context_validation import ContextValidator

        compiler = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=3))
        context = compiler.compile(
            envelope(2),
            "那下一步怎么办？",
            conversation_context={"recent_turns": [{"turn_id": 1, "user": "前一句", "assistant": "前一答", "cognitive_mode": "engineering_collaboration"}]},
        ).julia_context

        report = ContextValidator().validate(context)
        self.assertNotIn("runtime_contamination:context.conversation_context.recent_turns[0].turn_id", report.errors)

    def test_tc_phase3662_004_stt_repairs_birth_v2_identity_mishears(self):
        stt = SpeechLabSTT(SpeechLabSTTConfig(speech_lab_root=Path("/Users/admin/Desktop/speech_lab")))

        self.assertEqual(stt._normalize_text("教练今天有点累。"), "Julia今天有点累。")
        self.assertEqual(stt._normalize_text("助力了助力呀你认识从。"), "Julia你认识Tony。")


if __name__ == "__main__":
    unittest.main()
