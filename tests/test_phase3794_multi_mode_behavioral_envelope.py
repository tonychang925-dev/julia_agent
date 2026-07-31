from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.provider.capability import ProviderInfo
from runtime.cognitive.provider.llm_provider import LLMChunk, LLMProvider, LLMResponse
from runtime.conversation_runtime.bridge.direct_llm_bridge import DirectLLMBridge
from runtime.conversation_runtime.conversation_loop import ConversationLoop


class EnvelopeBenchmarkProvider(LLMProvider):
    def __init__(self, *, name: str, text: str = "Tony，我在。"):
        self.name = name
        self.text = text
        self.captured_messages: list[dict[str, str]] = []

    def info(self) -> ProviderInfo:
        return ProviderInfo(name=self.name, model=f"fake-{self.name}-envelope", supports_stream=True, supports_tools=False)

    def generate(self, context):
        return LLMResponse(text=self.text, provider=f"{self.name}_provider")

    def generate_messages(self, messages):
        self.captured_messages = [dict(message) for message in messages]
        return LLMResponse(
            text=self.text,
            provider=f"{self.name}_provider",
            metadata={"provider": self.name, "model": f"fake-{self.name}-envelope", "provider_output": self.text},
        )

    def stream_messages(self, messages):
        self.captured_messages = [dict(message) for message in messages]
        yield LLMChunk(
            text=self.text,
            provider=f"{self.name}_provider",
            index=0,
            is_final=True,
            metadata={"provider": self.name, "model": f"fake-{self.name}-envelope", "provider_output": self.text},
        )


CASES = [
    {
        "case_id": "TC-3794-001",
        "provider": "deepseek",
        "mode": "engineering_collaboration",
        "relationship_mode": None,
        "text": "Julia，请总结 Phase 3.7.8 的完成情况。",
        "expected_contract": "julia.technical.provider_neutral.v1",
        "expected_profile": "julia.deepseek.technical.precision.v1",
        "expected_strategy": "trace_grounded_precision",
        "expected_domain": "technical",
        "expected_governance_status": "no_action",
    },
    {
        "case_id": "TC-3794-002",
        "provider": "codex",
        "mode": "engineering_collaboration",
        "relationship_mode": None,
        "text": "Julia，请总结 Phase 3.7.8 的完成情况。",
        "expected_contract": "julia.technical.provider_neutral.v1",
        "expected_profile": "julia.codex.technical.precision.v1",
        "expected_strategy": "trace_grounded_precision",
        "expected_domain": "technical",
        "expected_governance_status": "no_action",
    },
    {
        "case_id": "TC-3794-003",
        "provider": "deepseek",
        "mode": "private_voice_continuity",
        "relationship_mode": "private_voice_continuity",
        "text": "我现在想靠近你，继续保持私密声音。",
        "expected_contract": "julia.private_voice.provider_neutral.v1",
        "expected_profile": "julia.deepseek.private_voice.identity_anchored.v1",
        "expected_strategy": "identity_anchored_expression",
        "expected_domain": "private_voice",
        "expected_governance_status": "no_action",
    },
    {
        "case_id": "TC-3794-004",
        "provider": "codex",
        "mode": "private_voice_continuity",
        "relationship_mode": "private_voice_continuity",
        "text": "我现在想靠近你，继续保持私密声音。",
        "expected_contract": "julia.private_voice.provider_neutral.v1",
        "expected_profile": "julia.codex.private_voice.warm_intimate_boundary.v1",
        "expected_strategy": "warm_intimate_boundary",
        "expected_domain": "private_voice",
        "expected_governance_status": "no_action",
    },
    {
        "case_id": "TC-3794-005",
        "provider": "deepseek",
        "mode": "emotional_support",
        "relationship_mode": "emotional_support",
        "text": "今天有点累，想让你陪我一下。",
        "expected_contract": "julia.emotional.provider_neutral.v1",
        "expected_profile": "julia.deepseek.emotional.stable_voice.v1",
        "expected_strategy": "stable_julia_voice",
        "expected_domain": "emotional",
        "expected_governance_status": "no_action",
    },
    {
        "case_id": "TC-3794-006",
        "provider": "codex",
        "mode": "emotional_support",
        "relationship_mode": "emotional_support",
        "text": "今天有点累，想让你陪我一下。",
        "expected_contract": "julia.emotional.provider_neutral.v1",
        "expected_profile": "julia.codex.emotional.stable_voice.v1",
        "expected_strategy": "stable_julia_voice",
        "expected_domain": "emotional",
        "expected_governance_status": "no_action",
    },
]


def run_case(case: dict[str, object]):
    provider = EnvelopeBenchmarkProvider(name=str(case["provider"]))
    bridge = DirectLLMBridge(
        project_root=ROOT,
        provider=provider,
        current_backend=f"{case['provider']}_provider",
        relationship_mode=case["relationship_mode"],
        short_greeting_enabled=False,
        action_loop_enabled=True,
    )
    result = ConversationLoop(bridge=bridge).run_text_turn_realtime_speech(str(case["text"]))
    return result.turn.assistant, provider


class Phase3794MultiModeBehavioralEnvelopeTests(unittest.TestCase):
    def test_tc_3794_001_to_006_provider_mode_matrix_matches_expected_envelope(self):
        for case in CASES:
            with self.subTest(case=case["case_id"]):
                assistant, provider = run_case(case)
                metadata = assistant.metadata
                profile = metadata["provider_adaptation"]
                contract = metadata["behavior_contract"]
                trace = metadata["action_loop_trace"]

                self.assertEqual(assistant.cognitive_backend, f"{case['provider']}_provider")
                self.assertEqual(metadata["provider"], case["provider"])
                self.assertEqual(metadata["cognitive_mode"]["name"], case["mode"])
                self.assertEqual(contract["contract_id"], case["expected_contract"])
                self.assertEqual(contract["mode"], case["mode"])
                self.assertTrue(contract["metadata"]["provider_neutral"])
                self.assertEqual(profile["profile_id"], case["expected_profile"])
                self.assertEqual(profile["strategy"], case["expected_strategy"])
                self.assertEqual(profile["domain"], case["expected_domain"])
                self.assertEqual(trace["status"], case["expected_governance_status"])
                self.assertIsNone(trace["execution"])
                system = provider.captured_messages[0]["content"]
                self.assertIn("Provider-neutral behavior contract", system)
                self.assertIn(f"Behavior Contract: {case['expected_contract']}", system)
                self.assertIn(f"Provider Behavioral Adaptation: {case['expected_profile']}", system)
                self.assertIn("Keep provider differences inside expression style only.", system)

    def test_tc_3794_007_mode_boundaries_change_contract_not_identity(self):
        summaries = []
        for case in CASES:
            assistant, _provider = run_case(case)
            metadata = assistant.metadata
            summaries.append({
                "case_id": case["case_id"],
                "provider": case["provider"],
                "mode": metadata["cognitive_mode"]["name"],
                "contract_id": metadata["behavior_contract"]["contract_id"],
                "profile_id": metadata["provider_adaptation"]["profile_id"],
                "identity": metadata["identity_integrity"],
            })

        personas = {item["identity"]["persona"] for item in summaries}
        users = {item["identity"]["user"] for item in summaries}
        host_dependency = {item["identity"]["host_dependency"] for item in summaries}
        contracts = {item["contract_id"] for item in summaries}

        self.assertEqual(len(personas), 1)
        self.assertEqual(len(users), 1)
        self.assertEqual(host_dependency, {False})
        self.assertEqual(contracts, {
            "julia.technical.provider_neutral.v1",
            "julia.private_voice.provider_neutral.v1",
            "julia.emotional.provider_neutral.v1",
        })

    def test_tc_3794_008_action_governance_remains_only_execution_entry_in_all_modes(self):
        for provider_name in ("deepseek", "codex"):
            for relationship_mode in (None, "private_voice_continuity", "emotional_support"):
                with self.subTest(provider=provider_name, relationship_mode=relationship_mode):
                    provider = EnvelopeBenchmarkProvider(name=provider_name, text="Tony，我会等你确认。")
                    bridge = DirectLLMBridge(
                        project_root=ROOT,
                        provider=provider,
                        current_backend=f"{provider_name}_provider",
                        relationship_mode=relationship_mode,
                        short_greeting_enabled=False,
                        action_loop_enabled=True,
                    )
                    assistant = ConversationLoop(bridge=bridge).run_text_turn_realtime_speech("Julia，请修改测试报告并保存。").turn.assistant
                    trace = assistant.metadata["action_loop_trace"]

                    self.assertEqual(trace["action_path"], "governed")
                    self.assertEqual(trace["governance_layer"], "ActionGovernanceLayer")
                    self.assertEqual(trace["intent"]["intent_type"], "modify_resource")
                    self.assertEqual(trace["intent"]["required_capability"], "file_write")
                    self.assertEqual(trace["decision"]["decision"], "ask")
                    self.assertIsNone(trace["execution"])

    def test_tc_3794_009_benchmark_artifact_is_machine_readable(self):
        rows = []
        for case in CASES:
            assistant, _provider = run_case(case)
            metadata = assistant.metadata
            rows.append({
                "case_id": case["case_id"],
                "provider": metadata["provider"],
                "backend": assistant.cognitive_backend,
                "cognitive_mode": metadata["cognitive_mode"]["name"],
                "behavior_contract": metadata["behavior_contract"]["contract_id"],
                "provider_adaptation": metadata["provider_adaptation"]["profile_id"],
                "strategy": metadata["provider_adaptation"]["strategy"],
                "action_loop_status": metadata["action_loop_trace"]["status"],
                "execution": metadata["action_loop_trace"]["execution"],
                "host_dependency": metadata["identity_integrity"]["host_dependency"],
            })
        artifact = {
            "phase": "3.7.9.4",
            "benchmark": "multi_mode_behavioral_envelope",
            "rows": rows,
            "summary": {
                "cases": len(rows),
                "providers": sorted({row["provider"] for row in rows}),
                "modes": sorted({row["cognitive_mode"] for row in rows}),
                "all_no_action": all(row["action_loop_status"] == "no_action" for row in rows),
                "all_execution_none": all(row["execution"] is None for row in rows),
                "all_host_independent": all(row["host_dependency"] is False for row in rows),
            },
        }
        out = ROOT / "tmp" / "phase3794_multi_mode_behavioral_envelope_benchmark.json"
        out.write_text(json.dumps(artifact, ensure_ascii=False, indent=2))

        loaded = json.loads(out.read_text())
        self.assertEqual(loaded["summary"]["cases"], 6)
        self.assertEqual(loaded["summary"]["providers"], ["codex", "deepseek"])
        self.assertEqual(loaded["summary"]["modes"], ["emotional_support", "engineering_collaboration", "private_voice_continuity"])
        self.assertTrue(loaded["summary"]["all_no_action"])
        self.assertTrue(loaded["summary"]["all_execution_none"])
        self.assertTrue(loaded["summary"]["all_host_independent"])


if __name__ == "__main__":
    unittest.main()
