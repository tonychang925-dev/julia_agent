from pathlib import Path
import json
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memory.consolidation import BehaviorMemoryUpdater, PreferenceExtractor
from runtime.cognitive.context_builder import ContextBuilder
from runtime.event_graph import AgentEventGraph
from runtime.reflection import ReflectionAnalyzer


def make_project() -> tuple[tempfile.TemporaryDirectory, Path]:
    tmp = tempfile.TemporaryDirectory()
    project = Path(tmp.name)
    shutil.copytree(ROOT / "identity", project / "identity")
    (project / "memory").mkdir()
    (project / "memory" / "relationship_memory.jsonl").write_text("", encoding="utf-8")
    (project / "memory" / "episodic_memory.jsonl").write_text("", encoding="utf-8")
    (project / "memory" / "important_events.md").write_text("", encoding="utf-8")
    return tmp, project


class Phase35ReflectiveMemoryTests(unittest.TestCase):
    def test_tc_phase35_001_reflection_extracts_preference_insight(self):
        insights = ReflectionAnalyzer().analyze_text("Tony喜欢先看架构再看代码细节，也喜欢短句。")
        contents = [insight.content for insight in insights]

        self.assertIn("Tony 喜欢先看架构设计，再看代码细节", contents)
        self.assertIn("Tony 喜欢短句、简洁回答", contents)

    def test_tc_phase35_002_preference_memory_updates_future_context(self):
        tmp, project = make_project()
        self.addCleanup(tmp.cleanup)
        reflections = "Tony喜欢先看架构再看代码细节。"
        insights = PreferenceExtractor().extract(reflections)
        written = BehaviorMemoryUpdater(project / "memory").append_preferences(insights)

        context = ContextBuilder(project).build("帮我设计新模块", session_id="conv_future")

        self.assertEqual(len(written), 1)
        self.assertTrue(any("先看架构" in item.get("content", "") for item in context.memory))
        self.assertEqual(context.emotional_context["interaction_style"], "architecture_first")
        self.assertEqual(context.emotional_context["response_order"], "architecture_then_code_detail")

    def test_tc_phase35_003_agent_event_graph_links_voice_to_memory_update(self):
        graph = AgentEventGraph()
        voice = graph.chain("voice_command", {"text": "帮我看看 context builder"}, correlation_id="conv_1_turn_1")
        decision = graph.chain("decision_event", {"need_tool": True}, parent=voice)
        request = graph.chain("capability_request", {"capability": "claude_code_tool"}, parent=decision)
        tool_result = graph.chain("tool_result", {"ok": True, "output": "analysis complete"}, parent=request)
        reflection = graph.chain("reflection", {"summary": "Tony喜欢先看架构再看代码细节"}, parent=tool_result)
        memory_update = graph.chain("memory_update", {"type": "preference"}, parent=reflection)

        events = graph.to_list()
        self.assertEqual(len(events), 6)
        self.assertEqual(memory_update.parent_id, reflection.event_id)
        self.assertEqual(reflection.parent_id, tool_result.event_id)
        self.assertEqual(events[0]["correlation_id"], "conv_1_turn_1")
        self.assertEqual(events[-1]["correlation_id"], "conv_1_turn_1")

    def test_tc_phase35_004_behavior_update_deduplicates_preference_memory(self):
        tmp, project = make_project()
        self.addCleanup(tmp.cleanup)
        insights = PreferenceExtractor().extract("Tony喜欢先看架构再看代码细节。")
        updater = BehaviorMemoryUpdater(project / "memory")
        first = updater.append_preferences(insights)
        second = updater.append_preferences(insights)
        lines = (project / "memory" / "relationship_memory.jsonl").read_text(encoding="utf-8").splitlines()

        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])
        self.assertEqual(len(lines), 1)
        self.assertIn("先看架构", json.loads(lines[0])["content"])


if __name__ == "__main__":
    unittest.main()
