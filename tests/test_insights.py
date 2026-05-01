from __future__ import annotations

from pathlib import Path

from chat_analyser.config import TopicConfig
from chat_analyser.insights import build_insights
from chat_analyser.preprocessing import preprocess_chat


def test_insights_bundle_contains_domains_topics_and_actions():
    sample_path = Path(__file__).resolve().parents[1] / "data" / "sample" / "whatsapp_chat_sample.txt"
    df = preprocess_chat(sample_path.read_text(encoding="utf-8"))
    bundle = build_insights("Overall", df, TopicConfig())

    assert not bundle.link_domains.empty
    assert not bundle.media_summary.empty
    assert not bundle.topics.empty
    assert not bundle.session_summaries.empty
