#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.conversation_archive import TranscriptStore
from runtime.conversation_archive.analytics import ArchiveAnalyticsReporter, DatasetMaturityEvaluator, ExperienceCollectionPlanner


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Julia Conversation Experience Archive analytics")
    parser.add_argument("--archive", default="data/conversation_archive/transcripts.jsonl", help="archive JSONL path")
    parser.add_argument("--output", default="", help="optional JSON report output path")
    args = parser.parse_args()

    store = TranscriptStore(Path(args.archive))
    report_obj = ArchiveAnalyticsReporter(store).build()
    report = report_obj.to_dict()
    report["dataset_maturity"] = DatasetMaturityEvaluator().evaluate(report_obj).to_dict()
    report["collection_plan"] = ExperienceCollectionPlanner().build(report_obj).to_dict()
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
