from pathlib import Path
from types import SimpleNamespace
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.conversation_runtime.cli import make_bridge
from runtime.conversation_runtime.bridge.direct_llm_bridge import DirectLLMBridge
from runtime.conversation_runtime.conversation_loop import ConversationLoop


def args(**overrides):
    data = {
        "backend": "deepseek",
        "deepseek_model": "deepseek-chat",
        "disable_short_greeting": False,
        "disable_local_vocal_gesture": False,
        "relationship_mode": None,
        "disable_voice_latency_optimization": False,
        "voice_max_tokens": 320,
        "enable_action_loop": False,
        "handoff_input": "/tmp/in",
        "handoff_response": "/tmp/out",
        "handoff_request_json": "/tmp/req.json",
        "handoff_response_json": "/tmp/res.json",
        "handoff_stream_jsonl": "/tmp/stream.jsonl",
        "handoff_timeout": 0.0,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


class Phase377ControlledActionLoopActivationTests(unittest.TestCase):
    def test_tc_phase377_001_cli_help_exposes_enable_action_loop_flag(self):
        # TC-PHASE377-001
        completed = subprocess.run(
            [sys.executable, "-m", "runtime.conversation_runtime.cli", "--help"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        self.assertIn("--enable-action-loop", completed.stdout)

    def test_tc_phase377_002_make_bridge_keeps_action_loop_disabled_by_default(self):
        # TC-PHASE377-002
        bridge = make_bridge(args(enable_action_loop=False))

        self.assertIsInstance(bridge, DirectLLMBridge)
        self.assertFalse(bridge.action_loop_enabled)
        self.assertIsNone(bridge.action_loop)

    def test_tc_phase377_003_make_bridge_enables_deepseek_action_loop_when_flag_set(self):
        # TC-PHASE377-003
        bridge = make_bridge(args(enable_action_loop=True))

        self.assertTrue(bridge.action_loop_enabled)
        self.assertIsNotNone(bridge.action_loop)

    def test_tc_phase377_004_direct_echo_factory_accepts_action_loop_activation(self):
        # TC-PHASE377-004
        bridge = make_bridge(args(backend="direct-echo", enable_action_loop=True))

        self.assertIsInstance(bridge, DirectLLMBridge)
        self.assertTrue(bridge.action_loop_enabled)
        self.assertIsNotNone(bridge.action_loop)

    def test_tc_phase377_005_enabled_cli_bridge_emits_action_loop_trace_without_provider_metadata(self):
        # TC-PHASE377-005
        bridge = make_bridge(args(enable_action_loop=True, disable_short_greeting=True))
        # Avoid real network: replace provider with deterministic message provider from Phase 3.7.6 test.
        from tests.test_phase376_action_loop_trace_integration import FakeMessageProvider

        bridge.provider = FakeMessageProvider()
        loop = ConversationLoop(bridge=bridge)
        result = loop.run_text_turn_realtime_speech("帮我检查 Julia Runtime 架构。")
        trace = result.turn.assistant.metadata["action_loop_trace"]

        self.assertTrue(trace["enabled"])
        self.assertIn(trace["status"], {"failed_with_reflection", "completed_with_reflection"})
        serialized = str(trace).lower()
        for forbidden in ["provider", "backend", "deepseek", "model", "latency", "tts", "stt", "session_id", "turn_id"]:
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
