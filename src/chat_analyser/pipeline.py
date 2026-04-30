from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd

from .analysis import (
    activity_heatmap,
    daily_timeline,
    emoji_counts,
    fetch_stats,
    month_activity_map,
    monthly_timeline,
    most_busy_users,
    most_common_words,
    series_to_frame,
    week_activity_map,
)
from .config import AnalysisConfig, load_config
from .exporters import export_frames, export_metadata
from .network import ConversationNetworkResult, build_conversation_network
from .preprocessing import load_chat_file, preprocess_chat
from .sentiment import predict_sentiment, sentiment_by_user


@dataclass
class AnalysisResults:
    selected_user: str
    source_name: str
    config: AnalysisConfig
    messages: pd.DataFrame
    stats: dict[str, int]
    busy_users: pd.DataFrame
    monthly_timeline: pd.DataFrame
    daily_timeline: pd.DataFrame
    week_activity: pd.Series
    month_activity: pd.Series
    heatmap: pd.DataFrame
    common_words: pd.DataFrame
    emoji_counts: pd.DataFrame
    sentiment_messages: pd.DataFrame
    sentiment_summary: pd.DataFrame
    sentiment_timeline: pd.DataFrame
    sentiment_by_user: pd.DataFrame
    graph: nx.DiGraph
    graph_edges: pd.DataFrame
    graph_nodes: pd.DataFrame
    conversation_sessions: pd.DataFrame

    def dataframe_exports(self) -> dict[str, pd.DataFrame]:
        return {
            "messages": self.messages,
            "stats": pd.DataFrame([self.stats]),
            "busy_users": self.busy_users,
            "monthly_timeline": self.monthly_timeline,
            "daily_timeline": self.daily_timeline,
            "week_activity": series_to_frame(self.week_activity, "day_name", "message_count"),
            "month_activity": series_to_frame(self.month_activity, "month", "message_count"),
            "heatmap": self.heatmap.reset_index(),
            "common_words": self.common_words,
            "emoji_counts": self.emoji_counts,
            "sentiment_messages": self.sentiment_messages,
            "sentiment_summary": self.sentiment_summary,
            "sentiment_timeline": self.sentiment_timeline,
            "sentiment_by_user": self.sentiment_by_user,
            "graph_edges": self.graph_edges,
            "graph_nodes": self.graph_nodes,
            "conversation_sessions": self.conversation_sessions,
        }

    def metadata(self) -> dict[str, Any]:
        return {
            "selected_user": self.selected_user,
            "source_name": self.source_name,
            "stats": self.stats,
            "sentiment_enabled": self.config.sentiment.enabled,
            "graph_enabled": self.config.graph.enabled,
            "graph_nodes": int(self.graph.number_of_nodes()),
            "graph_edges": int(self.graph.number_of_edges()),
        }


class ChatAnalysisPipeline:
    def __init__(self, config: AnalysisConfig | None = None) -> None:
        self.config = config or AnalysisConfig()

    @classmethod
    def from_config_path(cls, path: str | Path | None) -> "ChatAnalysisPipeline":
        return cls(load_config(path))

    def run(self, chat_text: str, selected_user: str = "Overall", source_name: str = "uploaded_chat") -> AnalysisResults:
        messages = preprocess_chat(chat_text)
        if messages.empty:
            raise ValueError("No chat messages could be parsed from the provided input.")

        message_count, word_count, media_count, link_count = fetch_stats(selected_user, messages)
        busy_users_series, busy_users_df = most_busy_users(messages)
        sentiment_messages_df, sentiment_summary_df, sentiment_timeline_df = predict_sentiment(
            selected_user,
            messages,
            self.config.sentiment,
        )
        graph_result: ConversationNetworkResult = build_conversation_network(
            selected_user,
            messages,
            self.config.graph,
        )

        if selected_user == "Overall":
            busy_users_export = busy_users_df.copy()
            if not busy_users_export.empty:
                counts = busy_users_series.reindex(busy_users_export["user"]).fillna(0).astype(int).values
                busy_users_export.insert(0, "message_count", counts)
        else:
            busy_users_export = pd.DataFrame(columns=["message_count", "user", "percent"])

        return AnalysisResults(
            selected_user=selected_user,
            source_name=source_name,
            config=self.config,
            messages=messages,
            stats={
                "messages": message_count,
                "words": word_count,
                "media_messages": media_count,
                "links": link_count,
            },
            busy_users=busy_users_export,
            monthly_timeline=monthly_timeline(selected_user, messages),
            daily_timeline=daily_timeline(selected_user, messages),
            week_activity=week_activity_map(selected_user, messages),
            month_activity=month_activity_map(selected_user, messages),
            heatmap=activity_heatmap(selected_user, messages),
            common_words=most_common_words(selected_user, messages),
            emoji_counts=emoji_counts(selected_user, messages),
            sentiment_messages=sentiment_messages_df,
            sentiment_summary=sentiment_summary_df,
            sentiment_timeline=sentiment_timeline_df,
            sentiment_by_user=sentiment_by_user(sentiment_messages_df) if selected_user == "Overall" else pd.DataFrame(),
            graph=graph_result.graph,
            graph_edges=graph_result.edges,
            graph_nodes=graph_result.nodes,
            conversation_sessions=graph_result.sessions,
        )

    def run_from_file(self, chat_path: str | Path, selected_user: str = "Overall") -> AnalysisResults:
        chat_file = Path(chat_path)
        return self.run(load_chat_file(chat_file), selected_user=selected_user, source_name=chat_file.name)

    def export(self, results: AnalysisResults, output_dir: str | Path | None = None) -> list[Path]:
        target_dir = Path(output_dir or self.config.export.output_dir)
        written_paths = export_frames(results.dataframe_exports(), target_dir, self.config.export)
        written_paths.append(export_metadata(results.metadata(), target_dir))
        return written_paths
