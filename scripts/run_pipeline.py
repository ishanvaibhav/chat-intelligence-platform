from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from chat_analyser.pipeline import ChatAnalysisPipeline  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the WhatsApp chat analysis pipeline and export outputs.")
    parser.add_argument("--chat-file", required=True, help="Path to the exported WhatsApp .txt file")
    parser.add_argument("--config", default=str(ROOT / "config" / "defaults.json"), help="Path to JSON config")
    parser.add_argument("--selected-user", default="Overall", help="User name to analyze")
    parser.add_argument("--output-dir", default=None, help="Directory for CSV/Parquet exports")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    pipeline = ChatAnalysisPipeline.from_config_path(args.config)
    results = pipeline.run_from_file(args.chat_file, selected_user=args.selected_user)
    written_paths = pipeline.export(results, output_dir=args.output_dir)

    print(f"Source: {results.source_name}")
    print(f"Selected user: {results.selected_user}")
    print(f"Messages: {results.stats['messages']}")
    print(f"Words: {results.stats['words']}")
    print(f"Links: {results.stats['links']}")
    print(f"Exports written: {len(written_paths)}")
    for path in written_paths[:10]:
        print(f" - {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
