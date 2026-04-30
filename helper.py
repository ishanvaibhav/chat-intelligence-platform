from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from chat_analyser.analysis import (  # noqa: E402
    DELETED_MESSAGE,
    MEDIA_MESSAGE,
    activity_heatmap,
    emoji_counts,
    fetch_stats,
    month_activity_map,
    monthly_timeline,
    most_busy_users,
    most_common_words,
    week_activity_map,
    daily_timeline,
)
from chat_analyser.config import AnalysisConfig  # noqa: E402
from chat_analyser.network import build_conversation_network as _build_conversation_network  # noqa: E402
from chat_analyser.sentiment import (  # noqa: E402
    load_sentiment_pipeline,
    predict_sentiment,
    sentiment_by_user as sentiment_by_user_from_predictions,
)


def create_wordcloud_data(selected_user, df, top_n=20):
    return most_common_words(selected_user, df, top_n=top_n)


def emoji_helper(selected_user, df):
    return emoji_counts(selected_user, df)


def analyze_sentiment(selected_user, df, config=None):
    sentiment_config = config or AnalysisConfig().sentiment
    return predict_sentiment(selected_user, df, sentiment_config)


def sentiment_by_user(df, config=None):
    predictions_df, _, _ = analyze_sentiment("Overall", df, config=config)
    return sentiment_by_user_from_predictions(predictions_df)


def build_conversation_network(selected_user, df, config=None):
    graph_config = config or AnalysisConfig().graph
    result = _build_conversation_network(selected_user, df, graph_config)
    return result.graph, result.edges, result.nodes, result.sessions
