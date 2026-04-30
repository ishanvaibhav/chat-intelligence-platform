from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sns
import streamlit as st


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
DEFAULT_CONFIG_PATH = ROOT / "config" / "defaults.json"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from chat_analyser.config import load_config  # noqa: E402
from chat_analyser.pipeline import ChatAnalysisPipeline  # noqa: E402
from chat_analyser.preprocessing import preprocess_chat  # noqa: E402


st.set_page_config(
    page_title="WhatsApp Chat Analyser",
    page_icon=":speech_balloon:",
    layout="wide",
)
sns.set_theme(style="whitegrid")


def render_bar_chart(series, title, color):
    fig, ax = plt.subplots()
    ax.bar(series.index.astype(str), series.values, color=color)
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=45)
    st.pyplot(fig)


def render_relationship_graph(graph: nx.DiGraph):
    figure, axis = plt.subplots(figsize=(10, 7))
    if graph.number_of_edges() == 0:
        axis.text(0.5, 0.5, "Not enough interactions to build a graph.", ha="center", va="center")
        axis.axis("off")
        return figure

    positions = nx.spring_layout(graph, seed=42, weight="weight")
    node_sizes = [600 + graph.nodes[node].get("message_count", 1) * 40 for node in graph.nodes]
    node_colors = [graph.nodes[node].get("community", 0) for node in graph.nodes]
    edge_weights = [graph[source][target]["weight"] for source, target in graph.edges]
    max_weight = max(edge_weights) if edge_weights else 1
    edge_widths = [1.2 + (weight / max_weight) * 4 for weight in edge_weights]
    edge_labels = {
        (source, target): f"{graph[source][target]['weight']:.1f}"
        for source, target in graph.edges
    }

    nx.draw(
        graph,
        positions,
        with_labels=True,
        node_size=node_sizes,
        node_color=node_colors,
        cmap=plt.cm.Set3,
        width=edge_widths,
        arrows=True,
        arrowstyle="-|>",
        arrowsize=16,
        edge_color="#6c757d",
        font_size=10,
        ax=axis,
    )
    nx.draw_networkx_edge_labels(graph, positions, edge_labels=edge_labels, font_size=8, ax=axis)
    axis.set_title("Weighted Conversation Network")
    axis.axis("off")
    return figure


def load_sidebar_config():
    config = load_config(DEFAULT_CONFIG_PATH)
    st.sidebar.header("Analysis Controls")
    config.sentiment.enabled = st.sidebar.checkbox("Enable Sentiment", value=config.sentiment.enabled)
    config.sentiment.model_name = st.sidebar.text_input("Sentiment Model", value=config.sentiment.model_name)
    config.sentiment.batch_size = st.sidebar.number_input(
        "Sentiment Batch Size",
        min_value=1,
        max_value=64,
        value=config.sentiment.batch_size,
    )
    config.sentiment.max_length = st.sidebar.number_input(
        "Sentiment Max Length",
        min_value=16,
        max_value=512,
        value=config.sentiment.max_length,
    )

    st.sidebar.divider()
    st.sidebar.subheader("Graph Parameters")
    config.graph.enabled = st.sidebar.checkbox("Enable Conversation Graph", value=config.graph.enabled)
    config.graph.session_gap_minutes = st.sidebar.number_input(
        "Session Gap (minutes)",
        min_value=5,
        max_value=180,
        value=config.graph.session_gap_minutes,
    )
    config.graph.reply_window_minutes = st.sidebar.number_input(
        "Reply Window (minutes)",
        min_value=1,
        max_value=60,
        value=config.graph.reply_window_minutes,
    )
    config.graph.context_window = st.sidebar.number_input(
        "Context Window (messages)",
        min_value=1,
        max_value=20,
        value=config.graph.context_window,
    )

    st.sidebar.divider()
    st.sidebar.subheader("Exports")
    export_outputs = st.sidebar.checkbox("Export CSV/Parquet Outputs", value=False)
    export_dir = st.sidebar.text_input("Output Directory", value=config.export.output_dir)
    config.export.output_dir = export_dir
    return config, export_outputs


st.title("WhatsApp Chat Analyser")
st.caption("Upload a WhatsApp exported chat text file to explore activity, graph relationships, and ML sentiment.")

uploaded_file = st.sidebar.file_uploader("Choose a WhatsApp chat export", type=["txt"])
config, export_outputs = load_sidebar_config()

if uploaded_file is None:
    st.info("Upload a `.txt` WhatsApp chat export from the sidebar to begin.")
    st.stop()

raw_data = uploaded_file.getvalue().decode("utf-8", errors="ignore")
preview_df = preprocess_chat(raw_data)
if preview_df.empty:
    st.error("No chat messages could be parsed from this file. Please upload a valid WhatsApp export.")
    st.stop()

users = sorted(user for user in preview_df["user"].unique() if user != "group_notification")
selected_user = st.sidebar.selectbox("Show analysis for", ["Overall", *users])

if st.sidebar.button("Show Analysis", use_container_width=True):
    pipeline = ChatAnalysisPipeline(config)
    with st.spinner("Running the data pipeline..."):
        results = pipeline.run(raw_data, selected_user=selected_user, source_name=uploaded_file.name)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Messages", results.stats["messages"])
    col2.metric("Words", results.stats["words"])
    col3.metric("Media", results.stats["media_messages"])
    col4.metric("Links", results.stats["links"])

    if export_outputs:
        written_paths = pipeline.export(results)
        st.success(f"Exported {len(written_paths)} analysis files to `{config.export.output_dir}`.")

    if selected_user == "Overall" and not results.busy_users.empty:
        st.subheader("Most Busy Users")
        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots()
            ax.bar(results.busy_users["user"], results.busy_users["message_count"], color="#118ab2")
            ax.set_title("Top Participants")
            ax.tick_params(axis="x", rotation=45)
            st.pyplot(fig)
        with col2:
            st.dataframe(results.busy_users, use_container_width=True, hide_index=True)

    st.subheader("Monthly Timeline")
    fig, ax = plt.subplots()
    ax.plot(results.monthly_timeline["time"], results.monthly_timeline["message_count"], color="#ef476f", linewidth=2)
    ax.tick_params(axis="x", rotation=45)
    ax.set_ylabel("Messages")
    st.pyplot(fig)

    st.subheader("Daily Timeline")
    fig, ax = plt.subplots()
    ax.plot(results.daily_timeline["only_date"], results.daily_timeline["message_count"], color="#06d6a0", linewidth=2)
    ax.set_ylabel("Messages")
    ax.tick_params(axis="x", rotation=45)
    st.pyplot(fig)

    st.subheader("Activity Map")
    col1, col2 = st.columns(2)
    with col1:
        render_bar_chart(results.week_activity, "Weekly Activity", "#073b4c")
    with col2:
        render_bar_chart(results.month_activity, "Monthly Activity", "#ffd166")

    st.subheader("Busy Hours Heatmap")
    fig, ax = plt.subplots(figsize=(14, 4))
    sns.heatmap(results.heatmap, ax=ax, cmap="YlGnBu")
    st.pyplot(fig)

    st.subheader("Most Common Words")
    if results.common_words.empty:
        st.info("No meaningful words found for this selection.")
    else:
        fig, ax = plt.subplots()
        ax.barh(results.common_words["word"], results.common_words["count"], color="#ff7f51")
        ax.invert_yaxis()
        st.pyplot(fig)

    st.subheader("Emoji Analysis")
    if results.emoji_counts.empty:
        st.info("No emojis found for this selection.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots()
            ax.pie(
                results.emoji_counts.head()["count"],
                labels=results.emoji_counts.head()["emoji"],
                autopct="%0.1f%%",
                startangle=90,
            )
            st.pyplot(fig)
        with col2:
            st.dataframe(results.emoji_counts.head(10), use_container_width=True, hide_index=True)

    st.subheader("Deep Learning Sentiment")
    if not config.sentiment.enabled:
        st.info("Sentiment analysis is disabled in the sidebar config.")
    elif results.sentiment_messages.empty:
        st.info("No text messages were available for sentiment analysis.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots()
            ax.bar(
                results.sentiment_summary["sentiment"].astype(str),
                results.sentiment_summary["messages"],
                color=["#d62828", "#fcbf49", "#2a9d8f"],
            )
            ax.set_title("Sentiment Distribution")
            st.pyplot(fig)
        with col2:
            st.dataframe(results.sentiment_summary, use_container_width=True, hide_index=True)

        fig, ax = plt.subplots()
        ax.plot(
            results.sentiment_timeline["only_date"],
            results.sentiment_timeline["avg_sentiment"],
            color="#264653",
            linewidth=2,
        )
        ax.axhline(0, linestyle="--", color="#6c757d", linewidth=1)
        ax.set_ylabel("Average Mood Score")
        ax.set_title("Sentiment Timeline")
        ax.tick_params(axis="x", rotation=45)
        st.pyplot(fig)

        if selected_user == "Overall" and not results.sentiment_by_user.empty:
            st.markdown("**Sentiment By User**")
            st.dataframe(results.sentiment_by_user, use_container_width=True, hide_index=True)

        st.markdown("**High-Confidence Sentiment Samples**")
        st.dataframe(
            results.sentiment_messages[["date", "user", "message", "sentiment", "score"]]
            .sort_values("score", ascending=False)
            .head(12),
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Real Conversation Network")
    if not config.graph.enabled:
        st.info("Conversation graph is disabled in the sidebar config.")
    elif results.graph.number_of_nodes() < 2 or results.graph_edges.empty:
        st.info("Not enough multi-user interaction was found to build the relationship graph.")
    else:
        metric1, metric2, metric3, metric4 = st.columns(4)
        metric1.metric("Participants", results.graph.number_of_nodes())
        metric2.metric("Weighted Links", results.graph.number_of_edges())
        metric3.metric("Conversation Clusters", int(results.conversation_sessions["conversation_id"].nunique()))
        metric4.metric("Strongest Link", f"{results.graph_edges.iloc[0]['weight']:.2f}")

        st.pyplot(render_relationship_graph(results.graph))

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Top Relationship Edges**")
            st.dataframe(results.graph_edges.head(15), use_container_width=True, hide_index=True)
        with col2:
            st.markdown("**Node Communities**")
            st.dataframe(results.graph_nodes, use_container_width=True, hide_index=True)

        st.markdown("**Conversation Sessions**")
        st.dataframe(results.conversation_sessions.head(20), use_container_width=True, hide_index=True)
