from __future__ import annotations

import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from chat_analyser.config import load_config  # noqa: E402
from chat_analyser.pipeline import ChatAnalysisPipeline  # noqa: E402


ASSETS_DIR = ROOT / "assets" / "figures"
BENCHMARK_DIR = ROOT / "outputs" / "portfolio_benchmark"


def render_network(graph: nx.DiGraph, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 7))
    positions = nx.spring_layout(graph, seed=42, weight="weight")
    node_sizes = [700 + graph.nodes[node].get("message_count", 1) * 55 for node in graph.nodes]
    node_colors = [graph.nodes[node].get("community", 0) for node in graph.nodes]
    edge_weights = [graph[source][target]["weight"] for source, target in graph.edges]
    max_weight = max(edge_weights) if edge_weights else 1
    edge_widths = [1.2 + (weight / max_weight) * 4 for weight in edge_weights]
    edge_labels = {(source, target): f"{graph[source][target]['weight']:.1f}" for source, target in graph.edges}

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
        ax=ax,
    )
    nx.draw_networkx_edge_labels(graph, positions, edge_labels=edge_labels, font_size=8, ax=ax)
    ax.set_title("Weighted Conversation Network")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def main() -> int:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    config = load_config(ROOT / "config" / "defaults.json")
    pipeline = ChatAnalysisPipeline(config)
    results = pipeline.run_from_file(ROOT / "data" / "sample" / "whatsapp_chat_sample.txt")

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(results.daily_timeline["only_date"], results.daily_timeline["message_count"], color="#ef476f", linewidth=2.5)
    ax.set_title("Daily Message Activity")
    ax.set_ylabel("Messages")
    fig.tight_layout()
    fig.savefig(ASSETS_DIR / "daily_message_activity.png", dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(results.common_words["word"].head(10), results.common_words["count"].head(10), color="#ff7f51")
    ax.set_title("Top Common Words")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(ASSETS_DIR / "top_common_words.png", dpi=220)
    plt.close(fig)

    if not results.sentiment_summary.empty:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(results.sentiment_summary["sentiment"].astype(str), results.sentiment_summary["messages"], color=["#d62828", "#fcbf49", "#2a9d8f"])
        ax.set_title("Sentiment Distribution")
        fig.tight_layout()
        fig.savefig(ASSETS_DIR / "sentiment_distribution.png", dpi=220)
        plt.close(fig)

    if results.graph.number_of_nodes() >= 2 and results.graph.number_of_edges() >= 1:
        render_network(results.graph, ASSETS_DIR / "conversation_network.png")

    for benchmark_plot in ["benchmark_accuracy.png", "benchmark_macro_f1.png"]:
        source_path = BENCHMARK_DIR / benchmark_plot
        if source_path.exists():
            shutil.copy2(source_path, ASSETS_DIR / benchmark_plot)

    print(f"Portfolio figures written to: {ASSETS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
