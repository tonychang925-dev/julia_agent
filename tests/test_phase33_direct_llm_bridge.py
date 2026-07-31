from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.conversation_runtime.bridge.direct_llm_bridge import DirectLLMBridge
from runtime.conversation_runtime.conversation_loop import ConversationLoop
from runtime.conversation_runtime.state_machine import ConversationState


class Phase33DirectLLMBridgeTests(unittest.TestCase):
    def test_tc_phase33_005_direct_llm_bridge_uses_julia_context_without_host_agent(self):
        loop = ConversationLoop(bridge=DirectLLMBridge.echo(ROOT))
        result = loop.run_text_turn("Julia，你是谁？")

        self.assertEqual(
            result.state_history,
            [
                ConversationState.IDLE,
                ConversationState.LISTENING,
                ConversationState.USER_SPEAKING,
                ConversationState.FINALIZING,
                ConversationState.THINKING,
                ConversationState.RESPONDING,
                ConversationState.SPEAKING,
                ConversationState.LISTENING,
            ],
        )
        self.assertEqual(result.turn.assistant.cognitive_backend, "echo_provider")
        self.assertIn("我是Julia", result.turn.assistant.text)
        self.assertIn("Tony", result.turn.assistant.text)
        self.assertEqual(result.turn.assistant.metadata["bridge"], "direct_llm")
        self.assertEqual(result.turn.assistant.metadata["context_runtime_state"]["current_backend"], "echo_provider")

    def test_tc_phase33_006_direct_llm_bridge_streams_provider_chunks_into_realtime_speech(self):
        loop = ConversationLoop(bridge=DirectLLMBridge.echo(ROOT))
        result = loop.run_text_turn_realtime_speech("Julia，你还记得我吗？")

        self.assertEqual(result.state_history[-1], ConversationState.LISTENING)
        self.assertEqual(result.turn.assistant.cognitive_backend, "echo_provider")
        self.assertIn("记得", result.turn.assistant.text)
        self.assertIn("[TTS_SENTENCE:0:local_tts]", "\n".join(result.event_log))
        self.assertIsNotNone(result.trace)
        self.assertEqual(result.trace.to_dict()["reasoning"]["backend"], "echo_provider")


from runtime.cognitive.provider.capability import ProviderInfo
from runtime.cognitive.provider.llm_provider import LLMChunk, LLMProvider, LLMResponse


class Phase35MessageFakeProvider(LLMProvider):
    def __init__(self):
        self.messages_seen = []

    def info(self) -> ProviderInfo:
        return ProviderInfo(name="fake", model="fake-phase35", supports_stream=True)

    def generate(self, context):
        return LLMResponse(text="legacy path", provider="fake")

    def generate_messages(self, messages):
        self.messages_seen.append(messages)
        return LLMResponse(text="[呻吟]嗯……Tony……我会慢一点，多陪你说一会儿。", provider="fake", metadata={"provider": "fake"})

    def stream_messages(self, messages):
        self.messages_seen.append(messages)
        text = "[呻吟]嗯……Tony……我会慢一点，多陪你说一会儿。"
        yield LLMChunk(text=text, provider="fake", index=0, is_final=False, metadata={"provider": "fake"})
        yield LLMChunk(text="", provider="fake", index=1, is_final=True, metadata={"provider": "fake"})


class Phase35DirectLLMBridgeIntegrationTests(unittest.TestCase):
    def test_tc_phase35_010_deepseek_style_bridge_uses_phase35_pipeline_not_vocal_one_line_policy(self):
        provider = Phase35MessageFakeProvider()
        bridge = DirectLLMBridge(project_root=ROOT, provider=provider, current_backend="fake_phase35")
        loop = ConversationLoop(bridge=bridge)

        result = loop.run_text_turn_realtime_speech("呻吟一下久一点。")
        prompt_text = provider.messages_seen[0][0]["content"]

        self.assertIn("phase35_pipeline", result.turn.assistant.metadata)
        self.assertTrue(result.turn.assistant.metadata["phase35_pipeline"])
        self.assertNotIn("vocal_gesture_generation", result.turn.assistant.metadata)
        self.assertNotIn("Use 1 short line only", prompt_text)
        self.assertIn("Recent conversation", prompt_text)
        self.assertIn("Relationship continuity", prompt_text)


    def test_tc_phase35_013_bridge_relationship_mode_projects_private_voice_without_keyword_matching(self):
        provider = Phase35MessageFakeProvider()
        bridge = DirectLLMBridge(
            project_root=ROOT,
            provider=provider,
            current_backend="fake_phase35",
            relationship_mode="private_voice_continuity",
        )
        loop = ConversationLoop(bridge=bridge)

        loop.run_text_turn_realtime_speech("普通一句话。")
        prompt_text = provider.messages_seen[0][0]["content"]

        self.assertIn("private voice continuity", prompt_text)
        self.assertNotIn("software_architecture", prompt_text)
        self.assertNotIn("Julia Cognitive Environment", prompt_text)

    def test_tc_phase35_011_phase35_bridge_passes_recent_turns_to_renderer(self):
        provider = Phase35MessageFakeProvider()
        bridge = DirectLLMBridge(project_root=ROOT, provider=provider, current_backend="fake_phase35")
        loop = ConversationLoop(bridge=bridge)

        loop.run_text_turn_realtime_speech("呻吟一下久一点。")
        result = loop.run_text_turn_realtime_speech("太短了，要久一点。")
        second_prompt = provider.messages_seen[1][0]["content"]

        self.assertEqual(result.turn.assistant.metadata["rendering"]["recent_turns_count"], 1)
        self.assertIn("Tony: 呻吟一下久一点。", second_prompt)
        self.assertIn("Julia: [呻吟]嗯", second_prompt)


if __name__ == "__main__":
    unittest.main()



class Phase35OneTagFakeProvider(LLMProvider):
    def info(self) -> ProviderInfo:
        return ProviderInfo(name="fake", model="fake-one-tag", supports_stream=True)

    def generate(self, context):
        return LLMResponse(text="legacy path", provider="fake")

    def stream_messages(self, messages):
        text = "[呻吟] 好…Tony，来吧。用力抱紧我，我感受到了你的急切和渴望。让我完全属于你，这一刻…"
        yield LLMChunk(text=text, provider="fake", index=0, is_final=False, metadata={"provider": "fake"})
        yield LLMChunk(text="", provider="fake", index=1, is_final=True, metadata={"provider": "fake"})

    def generate_messages(self, messages):
        return LLMResponse(text="[呻吟] 好。继续。", provider="fake", metadata={"provider": "fake"})


class Phase35VoiceTagContinuityTests(unittest.TestCase):
    def test_tc_phase35_012_realtime_tts_carries_voice_tag_to_following_sentences(self):
        bridge = DirectLLMBridge(project_root=ROOT, provider=Phase35OneTagFakeProvider(), current_backend="fake_phase35")
        loop = ConversationLoop(bridge=bridge)

        result = loop.run_text_turn_realtime_speech("我想要连续语音。")
        spoken = result.turn.assistant.metadata["spoken_sentences"]

        self.assertGreaterEqual(len(spoken), 3)
        self.assertTrue(all(str(sentence).startswith("[呻吟]") for sentence in spoken))
        self.assertEqual(
            result.turn.assistant.text,
            "[呻吟] 好…Tony，来吧。用力抱紧我，我感受到了你的急切和渴望。让我完全属于你，这一刻…",
        )


if __name__ == "__main__":
    unittest.main()
