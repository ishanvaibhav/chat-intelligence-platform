from __future__ import annotations

from pathlib import Path

from chat_analyser.config import AnalysisConfig
from chat_analyser.pipeline import ChatAnalysisPipeline


def test_pipeline_runs_and_exports_csv_and_parquet(tmp_path):
    sample_path = Path(__file__).resolve().parents[1] / "data" / "sample" / "whatsapp_chat_sample.txt"
    config = AnalysisConfig()
    config.sentiment.enabled = False
    config.export.output_dir = str(tmp_path)
    pipeline = ChatAnalysisPipeline(config)

    results = pipeline.run_from_file(sample_path)
    written_paths = pipeline.export(results)

    assert results.stats["messages"] > 0
    assert results.graph.number_of_nodes() >= 2
    assert not results.link_domains.empty
    assert not results.media_summary.empty
    assert not results.graph_metrics.empty
    assert not results.behavior_profiles.empty
    assert any(path.suffix == ".csv" for path in written_paths)
    assert any(path.suffix == ".parquet" for path in written_paths)
    assert (tmp_path / "metadata.json").exists()
