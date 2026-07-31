from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.action import ActionPlanner
from runtime.cognitive.context_compiler import ContextCompiler, ContextPolicy, RuntimeEnvelope
from runtime.conversation_state import ContinuityManager


def envelope() -> RuntimeEnvelope:
    return RuntimeEnvelope(
        session_id="fix_e2e_alpha",
        turn_id=1,
        provider="fixture",
        backend="fixture",
        timestamp="2026-07-29T00:00:00Z",
        latency_target_ms=1500,
    )


def julia_context(text: str):
    return ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=2)).compile(
        envelope(),
        text,
        conversation_context={},
        user_intent={"mode": "engineering_collaboration"},
    ).julia_context


class E2EAlphaInputAndRoutingFixesTests(unittest.TestCase):
    def test_e2e_alpha_008_declarative_next_step_remember_does_not_trigger_action(self):
        # Regression: “下一步要做 E2E，请记住” was misrouted to create_plan.
        text = "Julia，我们刚才冻结了 Phase 3.7.4，下一步要做 E2E Integration Alpha。请记住：重点是单轮受治理 E2E；不写长期 Memory；ask/reject 必须阻断；需要验证完整 trace。"

        action_intent = ActionPlanner().plan(julia_context(text))

        self.assertIsNone(action_intent)

    def test_e2e_alpha_009_continuity_keeps_named_e2e_topics_and_constraints(self):
        text = "Julia，我们刚才冻结了 Phase 3.7.4，下一步要做 E2E Integration Alpha。请记住：重点是单轮受治理 E2E；不写长期 Memory；ask/reject 必须阻断；需要验证完整 trace。"

        state = ContinuityManager().build_context(current_user_input=text, cognitive_mode="engineering_collaboration")

        self.assertIn("Phase 3.7.4", state.active_topics)
        self.assertIn("E2E Integration Alpha", state.active_topics)
        self.assertIn("Single-Step Governed E2E", state.active_topics)
        loop = next(item for item in state.open_loops if item["topic"] == "E2E Integration Alpha")
        self.assertIn("no long-term memory persistence", loop["constraints"])
        self.assertIn("ask and reject must not execute", loop["constraints"])
        self.assertIn("full trace required", loop["constraints"])

    def test_e2e_alpha_010_text_file_preserves_complete_turn(self):
        text = "Julia，第一行。\n第二行：重点是单轮受治理 E2E。"
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f:
            f.write(text)
            path = f.name
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "runtime.conversation_runtime.cli",
                    "--text-input",
                    "--text-input-turns",
                    "1",
                    "--backend",
                    "direct-echo",
                    "--text-file",
                    path,
                    "--conversation-tts-mode",
                    "dry_run",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
        finally:
            Path(path).unlink(missing_ok=True)

        self.assertIn("[TEXT_FILE]", completed.stdout)
        self.assertIn("第二行：重点是单轮受治理 E2E。", completed.stdout)

    def test_e2e_alpha_011_multiline_send_preserves_complete_turn(self):
        stdin = "/multi\nJulia，第一行。\n第二行：重点是单轮受治理 E2E。\n/send\n"

        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "runtime.conversation_runtime.cli",
                "--text-input",
                "--text-input-turns",
                "1",
                "--backend",
                "direct-echo",
                "--conversation-tts-mode",
                "dry_run",
            ],
            cwd=ROOT,
            input=stdin,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        self.assertIn("[TEXT_MULTI]", completed.stdout)
        self.assertIn("第二行：重点是单轮受治理 E2E。", completed.stdout)


if __name__ == "__main__":
    unittest.main()
