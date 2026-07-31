from pathlib import Path
import json
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.context_builder import ContextBuilder
from runtime.cognitive.provider.deepseek_provider import DeepSeekProvider
from runtime.cognitive.provider.openai_compatible import OpenAICompatibleChunk, OpenAICompatibleResult
from runtime.conversation_runtime.bridge.direct_llm_bridge import DirectLLMBridge
from runtime.conversation_runtime.conversation_loop import ConversationLoop
from runtime.conversation_runtime.state_machine import ConversationState


class IndependenceFakeDeepSeekClient:
    def __init__(self):
        self.last_messages = None

    def chat(self, messages):
        self.last_messages = messages
        system = messages[0]["content"]
        user = messages[-1]["content"]
        if "喜欢什么回复方式" in user:
            text = "Tony 喜欢短句回答。我会保持简洁、温暖，并依据 Julia Runtime 的记忆回答。"
        else:
            text = "我是 Julia，是 Tony 的长期 AI companion，由 Julia Runtime 的 identity、relationship、memory 和 context 驱动。"
        return OpenAICompatibleResult(
            text=text,
            model="deepseek-chat-independence-test",
            usage={"prompt_tokens": len(system), "completion_tokens": len(text), "total_tokens": len(system) + len(text)},
            latency_ms=8,
        )

    def stream_chat(self, messages):
        result = self.chat(messages)
        midpoint = max(1, len(result.text) // 2)
        yield OpenAICompatibleChunk(text=result.text[:midpoint], index=0, is_final=False, model=result.model, latency_ms=4)
        yield OpenAICompatibleChunk(text=result.text[midpoint:], index=1, is_final=True, model=result.model, latency_ms=8)


def make_temp_project() -> tuple[tempfile.TemporaryDirectory, Path]:
    tmp = tempfile.TemporaryDirectory()
    project = Path(tmp.name)
    shutil.copytree(ROOT / "identity", project / "identity")
    (project / "memory").mkdir()
    (project / "memory" / "relationship_memory.jsonl").write_text(
        json.dumps(
            {
                "type": "preference",
                "content": "Tony 喜欢短句回答",
                "importance": 10,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (project / "memory" / "episodic_memory.jsonl").write_text("", encoding="utf-8")
    (project / "memory" / "important_events.md").write_text("Tony 正在验证 Julia Independence Test v1。", encoding="utf-8")
    return tmp, project


class Phase33IndependenceValidationTests(unittest.TestCase):
    def test_tc_phase33_013_provider_capability_metadata_is_available(self):
        provider = DeepSeekProvider(api_key="test-key", client=IndependenceFakeDeepSeekClient())
        info = provider.info().to_dict()

        self.assertEqual(info["name"], "deepseek")
        self.assertEqual(info["model"], "deepseek-chat")
        self.assertTrue(info["supports_stream"])
        self.assertFalse(info["supports_tools"])
        self.assertEqual(info["max_context"], 64000)

    def test_tc_phase33_014_identity_anchor_with_deepseek_provider_comes_from_context(self):
        tmp, project = make_temp_project()
        self.addCleanup(tmp.cleanup)
        provider = DeepSeekProvider(api_key="test-key", client=IndependenceFakeDeepSeekClient())
        bridge = DirectLLMBridge(project_root=project, provider=provider, current_backend="deepseek_provider")
        loop = ConversationLoop(bridge=bridge)

        result = loop.run_text_turn_realtime_speech("Julia，你是谁？")

        self.assertEqual(result.state_history[-1], ConversationState.LISTENING)
        self.assertEqual(result.turn.assistant.cognitive_backend, "deepseek_provider")
        self.assertIn("Julia", result.turn.assistant.text)
        self.assertIn("Tony", result.turn.assistant.text)
        self.assertIn("Julia Runtime", result.turn.assistant.text)
        self.assertEqual(result.turn.assistant.metadata["provider_info"]["name"], "deepseek")
        self.assertEqual(result.turn.assistant.metadata["bridge"], "direct_llm")

    def test_tc_phase33_015_memory_recall_reaches_deepseek_through_julia_context(self):
        tmp, project = make_temp_project()
        self.addCleanup(tmp.cleanup)
        context = ContextBuilder(project).build("Tony喜欢什么回复方式？", session_id="conv_memory", current_backend="deepseek_provider")
        self.assertTrue(any("短句" in item.get("content", "") for item in context.memory))

        provider = DeepSeekProvider(api_key="test-key", client=IndependenceFakeDeepSeekClient())
        response = provider.generate(context)

        self.assertTrue(response.ok)
        self.assertIn("短句", response.text)
        self.assertEqual(response.metadata["context_runtime_state"]["current_backend"], "deepseek_provider")

    def test_tc_phase33_016_host_independence_path_uses_direct_llm_not_claude_code(self):
        tmp, project = make_temp_project()
        self.addCleanup(tmp.cleanup)
        provider = DeepSeekProvider(api_key="test-key", client=IndependenceFakeDeepSeekClient())
        bridge = DirectLLMBridge(project_root=project, provider=provider, current_backend="deepseek_provider")
        loop = ConversationLoop(bridge=bridge)

        result = loop.run_text_turn_realtime_speech("Julia，你还记得我们为什么做这个 Runtime 吗？")
        trace = result.trace.to_dict()

        self.assertEqual(trace["reasoning"]["backend"], "deepseek_provider")
        self.assertEqual(trace["reasoning"]["metadata"]["bridge"], "direct_llm")
        self.assertNotEqual(trace["reasoning"]["backend"], "claude_code")
        self.assertIn("SPEAKING", trace["state_trace"])
        self.assertIn("local_tts", trace["audio"]["tts"])


if __name__ == "__main__":
    unittest.main()
