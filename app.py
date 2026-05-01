from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import plotly.graph_objects as go
import seaborn as sns
import streamlit as st


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
DEFAULT_CONFIG_PATH = ROOT / "config" / "defaults.json"
SAMPLE_CHAT_PATH = ROOT / "data" / "sample" / "whatsapp_chat_sample.txt"
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


def render_interactive_graph(graph: nx.DiGraph):
    if graph.number_of_edges() == 0:
        st.info("Not enough interactions to build the relationship graph.")
        return

    positions = nx.spring_layout(graph, seed=42, weight="weight")
    edge_x: list[float] = []
    edge_y: list[float] = []
    edge_text: list[str] = []

    for source, target, payload in graph.edges(data=True):
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_text.append(f"{source} → {target}<br>weight={payload['weight']:.2f}")

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line={"width": 1.8, "color": "#7f8c8d"},
        hoverinfo="none",
        mode="lines",
    )

    node_x: list[float] = []
    node_y: list[float] = []
    node_text: list[str] = []
    node_size: list[float] = []
    node_color: list[float] = []
    for node, payload in graph.nodes(data=True):
        x, y = positions[node]
        node_x.append(x)
        node_y.append(y)
        node_size.append(16 + payload.get("message_count", 1) * 2)
        node_color.append(payload.get("community", 0))
        node_text.append(
            "<br>".join(
                [
                    f"user={node}",
                    f"messages={payload.get('message_count', 0)}",
                    f"community={payload.get('community', 0)}",
                ]
            )
        )

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=list(graph.nodes),
        textposition="top center",
        hovertext=node_text,
        hoverinfo="text",
        marker={
            "showscale": True,
            "colorscale": "Tealgrn",
            "color": node_color,
            "size": node_size,
            "line": {"width": 1, "color": "#ffffff"},
            "colorbar": {"title": "Community"},
        },
    )

    figure = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title="Interactive Conversation Network",
            showlegend=False,
            hovermode="closest",
            margin={"b": 20, "l": 20, "r": 20, "t": 45},
            xaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
            yaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
        ),
    )
    st.plotly_chart(figure, use_container_width=True)


def load_sidebar_config():
    config = load_config(DEFAULT_CONFIG_PATH)
    st.sidebar.header("Analysis Controls")
    config.sentiment.enabled = st.sidebar.checkbox("Enable Sentiment", value=config.sentiment.enabled)
    config.sentiment.model_name = st.sidebar.text_input("Sentiment Model", value=config.sentiment.model_name)
    config.sentiment.batch_size = st.sidebar.number_input("Sentiment Batch Size", min_value=1, max_value=64, value=config.sentiment.batch_size)
    config.sentiment.max_length = st.sidebar.number_input("Sentiment Max Length", min_value=16, max_value=512, value=config.sentiment.max_length)

    st.sidebar.divider()
    st.sidebar.subheader("Graph Parameters")
    config.graph.enabled = st.sidebar.checkbox("Enable Conversation Graph", value=config.graph.enabled)
    config.graph.session_gap_minutes = st.sidebar.number_input("Session Gap (minutes)", min_value=5, max_value=180, value=config.graph.session_gap_minutes)
    config.graph.reply_window_minutes = st.sidebar.number_input("Reply Window (minutes)", min_value=1, max_value=60, value=config.graph.reply_window_minutes)
    config.graph.context_window = st.sidebar.number_input("Context Window (messages)", min_value=1, max_value=20, value=config.graph.context_window)

    st.sidebar.divider()
    st.sidebar.subheader("Topic Modeling")
    config.topic.enabled = st.sidebar.checkbox("Enable Topic Modeling", value=config.topic.enabled)
    config.topic.n_topics = st.sidebar.number_input("Number of Topics", min_value=2, max_value=10, value=config.topic.n_topics)

    st.sidebar.divider()
    st.sidebar.subheader("Experiment Tracking")
    config.tracking.enabled = st.sidebar.checkbox("Log Experiment Runs", value=config.tracking.enabled)
    config.tracking.log_dir = st.sidebar.text_input("Tracking Log Directory", value=config.tracking.log_dir)

    st.sidebar.divider()
    st.sidebar.subheader("Exports")
    export_outputs = st.sidebar.checkbox("Export CSV/Parquet Outputs", value=False)
    export_dir = st.sidebar.text_input("Output Directory", value=config.export.output_dir)
    config.export.output_dir = export_dir
    return config, export_outputs


def load_chat_source(uploaded_file):
    if uploaded_file is not None:
        st.session_state["sample_chat_enabled"] = False
        raw_data = uploaded_file.getvalue().decode("utf-8", errors="ignore")
        return raw_data, uploaded_file.name

    if st.session_state.get("sample_chat_enabled", False):
        return SAMPLE_CHAT_PATH.read_text(encoding="utf-8", errors="ignore"), SAMPLE_CHAT_PATH.name

    return None, None


def render_empty_state():
    st.info("Upload a WhatsApp export or load the bundled sample chat to explore the full analysis pipeline.")
    col1, col2 = st.columns([1.5, 1])
    with col1:
        st.markdown("### What this app can do")
        st.markdown(
            "\n".join(
                [
                    "- Deep-learning sentiment analysis",
                    "- Topic discovery and session summaries",
                    "- Media, link-domain, entity, and action-item analytics",
                    "- Interactive conversation network with centrality metrics",
                    "- Exportable CSV and Parquet outputs for downstream analysis",
                ]
            )
        )
        if st.button("Load Sample Chat", type="primary"):
            st.session_state["sample_chat_enabled"] = True
            st.rerun()
    with col2:
        st.markdown("### Included Demo Chat")
        st.markdown(
            "\n".join(
                [
                    f"- File: `{SAMPLE_CHAT_PATH.name}`",
                    "- Messages: `30`",
                    "- Participants: `4`",
                    "- Includes positive, neutral, and negative conversations",
                ]
            )
        )


st.title("WhatsApp Chat Analyser")
st.caption("Upload a WhatsApp exported chat text file to explore activity, graph relationships, ML sentiment, topics, and conversation intelligence.")

uploaded_file = st.sidebar.file_uploader("Choose a WhatsApp chat export", type=["txt"])
st.sidebar.caption("No file handy? Use the bundled sample chat.")
if st.sidebar.button("Use Sample Chat", use_container_width=True):
    st.session_state["sample_chat_enabled"] = True
    st.rerun()

config, export_outputs = load_sidebar_config()
raw_data, source_name = load_chat_source(uploaded_file)

if raw_data is None:
    render_empty_state()
    st.stop()

preview_df = preprocess_chat(raw_data)
if preview_df.empty:
    st.error("No chat messages could be parsed from this file. Please upload a valid WhatsApp export.")
    st.stop()

users = sorted(user for user in preview_df["user"].unique() if user != "group_notification")
selected_user = st.sidebar.selectbox("Show analysis for", ["Overall", *users])
run_analysis = st.sidebar.button("Show Analysis", use_container_width=True)

preview_col1, preview_col2, preview_col3, preview_col4 = st.columns(4)
preview_col1.metric("Source", source_name)
preview_col2.metric("Preview Messages", int(preview_df.shape[0]))
preview_col3.metric("Participants", int(preview_df[preview_df["user"] != "group_notification"]["user"].nunique()))
preview_col4.metric("Date Range", f"{preview_df['only_date'].min()} to {preview_df['only_date'].max()}")
st.caption("Adjust the sidebar controls, then click `Show Analysis` to run the full pipeline.")

if run_analysis:
    pipeline = ChatAnalysisPipeline(config)
    with st.spinner("Running the data pipeline..."):
        results = pipeline.run(raw_data, selected_user=selected_user, source_name=source_name)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Messages", results.stats["messages"])
    col2.metric("Words", results.stats["words"])
    col3.metric("Media", results.stats["media_messages"])
    col4.metric("Links", results.stats["links"])

    if export_outputs:
        written_paths = pipeline.export(results)
        st.success(f"Exported {len(written_paths)} analysis files to `{config.export.output_dir}`.")
    if results.experiment_log_path:
        st.caption(f"Experiment log updated: `{results.experiment_log_path}`")

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

    st.subheader("Topic Modeling")
    if results.topics.empty:
        st.info("Not enough clean text was available to build stable topics for this selection.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(results.topics, use_container_width=True, hide_index=True)
        with col2:
            st.dataframe(results.topic_messages.head(12), use_container_width=True, hide_index=True)

    st.subheader("Most Common Words")
    if results.common_words.empty:
        st.info("No meaningful words found for this selection.")
    else:
        fig, ax = plt.subplots()
        ax.barh(results.common_words["word"], results.common_words["count"], color="#ff7f51")
        ax.invert_yaxis()
        st.pyplot(fig)

    st.subheader("Media and Link Analytics")
    col1, col2 = st.columns(2)
    with col1:
        if results.media_summary.empty:
            st.info("No media messages detected in this selection.")
        else:
            st.dataframe(results.media_summary, use_container_width=True, hide_index=True)
            st.dataframe(results.media_by_user.head(10), use_container_width=True, hide_index=True)
    with col2:
        if results.link_domains.empty:
            st.info("No shared links detected in this selection.")
        else:
            st.dataframe(results.link_domains.head(10), use_container_width=True, hide_index=True)

    st.subheader("Entities and Action Items")
    col1, col2 = st.columns(2)
    with col1:
        if results.entities.empty:
            st.info("No lightweight entities detected.")
        else:
            st.dataframe(results.entities.head(15), use_container_width=True, hide_index=True)
    with col2:
        if results.action_items.empty:
            st.info("No action-oriented messages detected.")
        else:
            st.dataframe(results.action_items.head(15), use_container_width=True, hide_index=True)

    st.subheader("User Behavior Profiles")
    col1, col2 = st.columns(2)
    with col1:
        if results.behavior_profiles.empty:
            st.info("No user behavior profile could be computed.")
        else:
            st.dataframe(results.behavior_profiles, use_container_width=True, hide_index=True)
    with col2:
        if results.behavior_summary.empty:
            st.info("No behavior summary available.")
        else:
            st.dataframe(results.behavior_summary, use_container_width=True, hide_index=True)

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

    st.subheader("Conversation Summaries")
    if results.session_summaries.empty:
        st.info("No session summaries available.")
    else:
        st.dataframe(results.session_summaries.head(20), use_container_width=True, hide_index=True)

    st.subheader("Advanced Conversation Network")
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

        render_interactive_graph(results.graph)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Network Metrics**")
            st.dataframe(results.graph_metrics, use_container_width=True, hide_index=True)
            st.markdown("**Top Relationship Edges**")
            st.dataframe(results.graph_edges.head(15), use_container_width=True, hide_index=True)
        with col2:
            st.markdown("**Node Communities**")
            st.dataframe(results.graph_nodes, use_container_width=True, hide_index=True)
            st.markdown("**Network Roles**")
            st.dataframe(results.network_roles, use_container_width=True, hide_index=True)

        st.markdown("**Conversation Sessions**")
        st.dataframe(results.conversation_sessions.head(20), use_container_width=True, hide_index=True)
