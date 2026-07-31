from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.context_compiler import ContextCompiler, ContextPolicy, RuntimeEnvelope
from runtime.context_assembly import ContextAssemblyEngine
from runtime.context_os.cache import ContextCacheInvalidator, ContextCacheKey, ContextSnapshotCache


def envelope(session_id="conv_phase3753", turn_id=1):
    return RuntimeEnvelope(
        session_id=session_id,
        turn_id=turn_id,
        provider="deepseek",
        backend="deepseek-chat",
        timestamp="2026-07-29T00:00:00Z",
        latency_target_ms=1500,
    )


def context(text="继续设计 Context Cache", session_id="conv_phase3753"):
    return ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=2)).compile(
        envelope(session_id=session_id),
        text,
    ).julia_context


class Phase3753ContextCacheTests(unittest.TestCase):
    def test_tc_3753_001_stable_assembly_cache_miss_then_hit(self):
        engine = ContextAssemblyEngine(ROOT)
        julia_context = context("继续设计 Context Cache", session_id="cache_s1")

        first = engine.assemble("继续设计 Context Cache", session_id="cache_s1", julia_context=julia_context)
        second = engine.assemble("继续设计 Context Cache", session_id="cache_s1", julia_context=julia_context)

        self.assertEqual(first.metadata["cache"]["status"], "miss")
        self.assertEqual(second.metadata["cache"]["status"], "hit")
        self.assertIn("core_identity_pack", second.metadata["cache"]["cached_sections"])
        self.assertIn("relationship_anchor_pack", second.metadata["cache"]["cached_sections"])

    def test_tc_3753_002_current_user_input_is_not_part_of_stable_cache_key(self):
        julia_context = context("继续设计 Context Cache", session_id="cache_s2")
        key_a = ContextCacheKey.from_julia_context(
            session_id="cache_s2",
            julia_context=julia_context,
            component="context_assembly_stable_sections.v1",
            task_state_version="excluded_from_stable_cache",
            memory_version="excluded_from_stable_cache",
        )
        # Same JuliaContext, different runtime user text at assembly time must not alter the stable key.
        key_b = ContextCacheKey.from_julia_context(
            session_id="cache_s2",
            julia_context=julia_context,
            component="context_assembly_stable_sections.v1",
            task_state_version="excluded_from_stable_cache",
            memory_version="excluded_from_stable_cache",
        )

        self.assertEqual(key_a.digest, key_b.digest)
        self.assertNotIn("继续设计 Context Cache", str(key_a.to_dict()))
        self.assertEqual(key_a.memory_version, "excluded_from_stable_cache")
        self.assertEqual(key_a.task_state_version, "excluded_from_stable_cache")

    def test_tc_3753_003_semantic_evidence_and_routes_are_not_cached(self):
        engine = ContextAssemblyEngine(ROOT)
        julia_context = context("Phase 3.7.5 Context Cache", session_id="cache_s3")

        first = engine.assemble("Phase 3.7.5 Context Cache", session_id="cache_s3", julia_context=julia_context)
        second = engine.assemble("今天有点累，想让 Julia 陪我一下", session_id="cache_s3", julia_context=julia_context)

        self.assertEqual(second.metadata["cache"]["status"], "hit")
        self.assertIn("semantic_evidence", second.metadata["cache"]["excluded_from_cache"])
        self.assertIn("memory_route_decisions", second.metadata["cache"]["excluded_from_cache"])
        self.assertNotEqual(
            first.metadata["resolver"]["semantic_evidence"].get("scope_decision"),
            second.metadata["resolver"]["semantic_evidence"].get("scope_decision"),
        )

    def test_tc_3753_004_context_mode_change_creates_new_cache_key(self):
        engineering = context("继续设计 Context Cache", session_id="cache_s4")
        emotional = context("今天有点累，想让 Julia 陪我一下", session_id="cache_s4")
        key_engineering = ContextCacheKey.from_julia_context(
            session_id="cache_s4",
            julia_context=engineering,
            component="context_assembly_stable_sections.v1",
            task_state_version="excluded_from_stable_cache",
            memory_version="excluded_from_stable_cache",
        )
        key_emotional = ContextCacheKey.from_julia_context(
            session_id="cache_s4",
            julia_context=emotional,
            component="context_assembly_stable_sections.v1",
            task_state_version="excluded_from_stable_cache",
            memory_version="excluded_from_stable_cache",
        )

        self.assertNotEqual(key_engineering.context_mode, key_emotional.context_mode)
        self.assertNotEqual(key_engineering.digest, key_emotional.digest)

    def test_tc_3753_005_manual_invalidation_clears_cache(self):
        cache = ContextSnapshotCache[str]()
        julia_context = context("继续设计 Context Cache", session_id="cache_s5")
        key = ContextCacheKey.from_julia_context(
            session_id="cache_s5",
            julia_context=julia_context,
            component="unit_test",
            task_state_version="excluded_from_stable_cache",
            memory_version="excluded_from_stable_cache",
        )
        cache.set(key, "cached")
        decision = ContextCacheInvalidator().decide(previous_version="v1", current_version="v2", reason="persona_version_changed")
        result = ContextCacheInvalidator().apply(cache, decision)

        self.assertTrue(decision.invalidate)
        self.assertEqual(result["invalidated"], 1)
        self.assertIsNone(cache.get(key))

    def test_tc_3753_006_cache_metadata_serializes_for_trace(self):
        engine = ContextAssemblyEngine(ROOT)
        julia_context = context("继续设计 Context Cache", session_id="cache_s6")

        assembled = engine.assemble("继续设计 Context Cache", session_id="cache_s6", julia_context=julia_context)
        cache_meta = assembled.metadata["cache"]

        self.assertTrue(cache_meta["enabled"])
        self.assertIn(cache_meta["status"], {"miss", "hit"})
        self.assertIn("key_digest", cache_meta)
        self.assertIn("stats", cache_meta)
        self.assertIn("provider_output", cache_meta["excluded_from_cache"])


if __name__ == "__main__":
    unittest.main()
