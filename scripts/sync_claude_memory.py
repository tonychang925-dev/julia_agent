#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_SOURCE = Path.home() / ".claude-dev" / "projects" / "-Users-admin" / "memory"
DEFAULT_TARGET = Path(__file__).resolve().parents[1] / "memory" / "claude_diary"
DEFAULT_MANIFEST = Path(__file__).resolve().parents[1] / "memory" / "source_manifest.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sync(source: Path, target: Path, manifest_path: Path) -> dict:
    if not source.exists():
        raise FileNotFoundError(f"source memory dir not found: {source}")
    target.mkdir(parents=True, exist_ok=True)
    files = []
    for src in sorted(source.glob("*")):
        if not src.is_file() or src.name.startswith("."):
            continue
        dst = target / src.name
        shutil.copy2(src, dst)
        files.append(
            {
                "name": src.name,
                "source": str(src),
                "target": str(dst),
                "bytes": dst.stat().st_size,
                "sha256": sha256(dst),
            }
        )
    manifest = {
        "schema_version": "claude_memory_sync.v1",
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "source_dir": str(source),
        "target_dir": str(target),
        "mode": "mirror_only_not_raw_prompt_injection",
        "files": files,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Claude diary memory into Julia Runtime local memory mirror")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE), help="Claude memory source directory")
    parser.add_argument("--target", default=str(DEFAULT_TARGET), help="Julia local diary mirror directory")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="sync manifest path")
    args = parser.parse_args()
    manifest = sync(Path(args.source), Path(args.target), Path(args.manifest))
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
