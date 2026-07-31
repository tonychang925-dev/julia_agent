from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.capability import (
    CapabilityInvocationRuntime,
    CapabilityRequest,
    CapabilityRouter,
    ClaudeCodeTool,
)
from runtime.capability.permission import CapabilityPermissionGuard
from runtime.cognitive.context_builder import ContextBuilder


class Phase34CapabilityInvocationTests(unittest.TestCase):
    def test_tc_phase34_005_brain_hands_separation_routes_tool_via_capability_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            request_path = Path(tmp) / "claude_request.json"
            router = CapabilityRouter()
            router.register(ClaudeCodeTool(request_path=request_path))
            runtime = CapabilityInvocationRuntime.default(router)
            context = ContextBuilder(ROOT).build(
                "帮我看看 context builder 有没有问题",
                session_id="conv_tool_001",
                current_backend="deepseek_provider",
                conversation={"session_id": "conv_tool_001", "turn_id": 7, "history": []},
            )

            result = runtime.run(context)

            self.assertIsNotNone(result.request)
            self.assertEqual(result.request.capability, "claude_code_tool")
            self.assertEqual(result.request.context.actor, "julia_runtime")
            self.assertTrue(result.permission.allowed)
            self.assertTrue(result.tool_result.ok)
            payload = json.loads(request_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["type"], "capability_request")
            self.assertEqual(payload["context"]["intent"], "帮我看看 context builder 有没有问题")

    def test_tc_phase34_006_capability_discovery_lists_claude_code_tool(self):
        router = CapabilityRouter()
        router.register(ClaudeCodeTool())

        infos = [info.name for info in router.list_capabilities()]

        self.assertEqual(infos, ["claude_code_tool"])

    def test_tc_phase34_007_permission_blocks_destructive_tool_request(self):
        request = CapabilityRequest(
            capability="claude_code_tool",
            action="handoff",
            input={"task": "删除 runtime/cognitive/context_builder.py"},
        )

        decision = CapabilityPermissionGuard().decide(request)

        self.assertFalse(decision.allowed)
        self.assertTrue(decision.confirm_required)
        self.assertIn("requires_confirmation", decision.reason)

    def test_tc_phase34_008_tool_result_reflection_is_generated(self):
        with tempfile.TemporaryDirectory() as tmp:
            router = CapabilityRouter()
            router.register(ClaudeCodeTool(request_path=Path(tmp) / "request.json"))
            runtime = CapabilityInvocationRuntime.default(router)
            context = ContextBuilder(ROOT).build(
                "帮我检查代码",
                session_id="conv_reflect_001",
                current_backend="deepseek_provider",
                conversation={"session_id": "conv_reflect_001", "turn_id": 2, "history": []},
            )

            result = runtime.run(context)
            reflection = result.reflection.to_dict()

            self.assertEqual(reflection["event"], "tool_execution_result")
            self.assertEqual(reflection["capability"], "claude_code_tool")
            self.assertTrue(reflection["ok"])
            self.assertIn("tool_result", reflection["metadata"])

    def test_tc_phase34_009_no_tool_intent_returns_empty_invocation(self):
        router = CapabilityRouter()
        router.register(ClaudeCodeTool())
        runtime = CapabilityInvocationRuntime.default(router)
        context = ContextBuilder(ROOT).build("Julia，你是谁？", session_id="conv_no_tool")

        result = runtime.run(context)

        self.assertIsNone(result.request)
        self.assertIsNone(result.tool_result)
        self.assertIsNone(result.reflection)


if __name__ == "__main__":
    unittest.main()
