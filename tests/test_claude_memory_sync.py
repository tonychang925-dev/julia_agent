import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from runtime.memory_loader import MemoryLoader
from scripts.sync_claude_memory import sync


class ClaudeMemorySyncTests(unittest.TestCase):
    def test_sync_claude_memory_copies_files_and_writes_manifest(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            target = root / "target"
            manifest = root / "manifest.json"
            source.mkdir()
            (source / "julia_character.md").write_text("Julia character", encoding="utf-8")
            (source / "user_role.md").write_text("Tony", encoding="utf-8")

            result = sync(source, target, manifest)

            self.assertTrue((target / "julia_character.md").exists())
            self.assertTrue((target / "user_role.md").exists())
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(data["mode"], "mirror_only_not_raw_prompt_injection")
            self.assertEqual(len(result["files"]), 2)

    def test_memory_loader_prefers_local_claude_diary_mirror(self):
        with TemporaryDirectory() as td:
            memory_dir = Path(td) / "memory"
            mirror = memory_dir / "claude_diary"
            mirror.mkdir(parents=True)
            (mirror / "julia_character.md").write_text("LOCAL JULIA", encoding="utf-8")

            diary = MemoryLoader(memory_dir).load_claude_diary()

            self.assertEqual(diary["julia_character.md"], "LOCAL JULIA")


if __name__ == "__main__":
    unittest.main()
