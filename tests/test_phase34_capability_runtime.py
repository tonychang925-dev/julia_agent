from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.capability import CapabilityRequest, CapabilityRouter, ClaudeCodeTool


class Phase34CapabilityRuntimeTests(unittest.TestCase):
    def test_tc_phase34_001_router_registers_claude_code_as_capability_not_brain(self):
        router = CapabilityRouter()
        tool = ClaudeCodeTool()
        router.register(tool)

        infos = router.list_capabilities()
        self.assertEqual(len(infos), 1)
        self.assertEqual(infos[0].name, "claude_code_tool")
        self.assertFalse(infos[0].metadata["brain"])
        self.assertIn("handoff", infos[0].actions)

    def test_tc_phase34_002_claude_code_tool_writes_capability_handoff_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            request_path = Path(tmp) / "request.json"
            tool = ClaudeCodeTool(request_path=request_path)
            request = CapabilityRequest(
                capability="claude_code_tool",
                action="handoff",
                input={"task": "inspect context builder", "path": "runtime/cognitive/context_builder.py"},
                session_id="conv_cap_001",
                turn_id=3,
                correlation_id="conv_cap_001_turn_003",
            )

            result = tool.invoke(request)

            self.assertTrue(result.ok)
            self.assertEqual(result.tool, "claude_code_tool")
            payload = json.loads(request_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["type"], "capability_request")
            self.assertEqual(payload["provider"], "claude_code_tool")
            self.assertEqual(payload["input"]["task"], "inspect context builder")
            self.assertEqual(payload["session_id"], "conv_cap_001")

    def test_tc_phase34_003_router_invokes_registered_tool_and_reports_missing_tool(self):
        with tempfile.TemporaryDirectory() as tmp:
            router = CapabilityRouter()
            router.register(ClaudeCodeTool(request_path=Path(tmp) / "request.json"))
            ok = router.invoke(CapabilityRequest(capability="claude_code_tool", action="handoff", input={"task": "noop"}))
            missing = router.invoke(CapabilityRequest(capability="browser_tool", action="open", input={"url": "https://example.com"}))

            self.assertTrue(ok.ok)
            self.assertFalse(missing.ok)
            self.assertIn("not registered", missing.error)

    def test_tc_phase34_004_claude_code_tool_reads_response_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            response_path = Path(tmp) / "response.json"
            response_path.write_text(json.dumps({"status": "success", "output": "checked"}), encoding="utf-8")
            tool = ClaudeCodeTool(response_path=response_path)

            result = tool.invoke(CapabilityRequest(capability="claude_code_tool", action="read_response", input={}))

            self.assertTrue(result.ok)
            self.assertEqual(result.output, "checked")
            self.assertEqual(result.metadata["raw"]["status"], "success")


if __name__ == "__main__":
    unittest.main()
