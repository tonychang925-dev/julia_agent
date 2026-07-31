import unittest
from pathlib import Path

from runtime.memory import MemoryRuntime

ROOT = Path(__file__).resolve().parents[1]


class IntimacyModeMemoryRetrievalTests(unittest.TestCase):
    def test_l1_l4_intimacy_mode_memory_is_in_julia_owned_store(self):
        runtime = MemoryRuntime(ROOT)

        memories = runtime.retrieve("亲密模式 L1 L2 L3 L4 是什么", limit=8)

        ids = [memory.id for memory in memories]
        self.assertIn("memory_semantic_intimacy_mode_l1_l4_boundary_definition", ids)
        target = next(memory for memory in memories if memory.id == "memory_semantic_intimacy_mode_l1_l4_boundary_definition")
        self.assertIn("L1-L4", target.summary)
        self.assertIn("intimacy mode", target.topics)


if __name__ == "__main__":
    unittest.main()
