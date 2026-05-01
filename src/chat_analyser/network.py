from __future__ import annotations

import math
import re
from dataclasses import dataclass

import networkx as nx
import pandas as pd

from .analysis import DELETED_MESSAGE, MEDIA_MESSAGE
from .config import GraphConfig


@dataclass
class ConversationNetworkResult:
    graph: nx.DiGraph
    edges: pd.DataFrame
    nodes: pd.DataFrame
    sessions: pd.DataFrame
    metrics: pd.DataFrame
    user_network_roles: pd.DataFrame


def _build_alias_map(users: list[str]) -> dict[str, set[str]]:
    alias_map: dict[str, set[str]] = {}
    for user in users:
        cleaned = re.sub(r"[^a-z0-9\s]", " ", user.lower())
        aliases = {part for part in cleaned.split() if len(part) >= 3}
        normalized_name = re.sub(r"\s+", " ", cleaned).strip()
        if normalized_name:
            aliases.add(normalized_name)
        alias_map[user] = aliases
    return alias_map


def _extract_mentions(message: str, current_user: str, alias_map: dict[str, set[str]]) -> set[str]:
    lowered = re.sub(r"[^a-z0-9@\s]", " ", message.lower())
    normalized = re.sub(r"\s+", " ", lowered).strip()
    tokens = set(normalized.split())
    matches: set[str] = set()

    for user, aliases in alias_map.items():
        if user == current_user:
            continue
        for alias in aliases:
            if not alias:
                continue
            if f"@{alias}" in normalized or alias in tokens or f" {alias} " in f" {normalized} ":
                matches.add(user)
                break
    return matches


def build_conversation_network(
    selected_user: str,
    df: pd.DataFrame,
    config: GraphConfig,
) -> ConversationNetworkResult:
    if not config.enabled:
        empty = pd.DataFrame()
        return ConversationNetworkResult(nx.DiGraph(), empty, empty, empty, empty, empty)

    filtered = df[
        (df["user"] != "group_notification")
        & (df["message"] != MEDIA_MESSAGE)
        & (df["message"] != DELETED_MESSAGE)
    ].copy()
    filtered = filtered.sort_values("date").reset_index(drop=True)

    if filtered.empty or filtered["user"].nunique() < 2:
        empty = pd.DataFrame()
        return ConversationNetworkResult(nx.DiGraph(), empty, empty, empty, empty, empty)

    filtered["gap_minutes"] = filtered["date"].diff().dt.total_seconds().div(60).fillna(0)
    filtered["conversation_id"] = (filtered["gap_minutes"] > config.session_gap_minutes).cumsum()
    alias_map = _build_alias_map(filtered["user"].unique().tolist())
    edge_store: dict[tuple[str, str], dict[str, object]] = {}

    def add_edge(
        source: str,
        target: str,
        weight: float,
        reason: str,
        gap_minutes: float | None,
        conversation_id: int,
    ) -> None:
        if source == target:
            return

        edge = edge_store.setdefault(
            (source, target),
            {
                "source": source,
                "target": target,
                "weight": 0.0,
                "reply_gap_score": 0.0,
                "mention_score": 0.0,
                "cluster_score": 0.0,
                "interactions": 0,
                "conversation_ids": set(),
                "gap_values": [],
            },
        )
        edge["weight"] += weight
        edge["interactions"] += 1
        edge["conversation_ids"].add(conversation_id)
        if reason == "reply_gap":
            edge["reply_gap_score"] += weight
        elif reason == "mention":
            edge["mention_score"] += weight
        elif reason == "cluster":
            edge["cluster_score"] += weight
        if gap_minutes is not None:
            edge["gap_values"].append(gap_minutes)

    for conversation_id, conversation_df in filtered.groupby("conversation_id", sort=False):
        records = conversation_df.to_dict("records")
        for index, row in enumerate(records):
            current_user = str(row["user"])
            current_message = str(row["message"])
            recent_records = records[max(0, index - config.context_window) : index]

            if recent_records:
                last_other_message = next(
                    (item for item in reversed(recent_records) if item["user"] != current_user),
                    None,
                )
                if last_other_message is not None:
                    gap = max(
                        (row["date"] - last_other_message["date"]).total_seconds() / 60,
                        0.1,
                    )
                    if gap <= config.reply_window_minutes:
                        reply_weight = config.reply_base_weight + config.reply_decay_weight * math.exp(
                            -gap / config.reply_decay_divisor
                        )
                        add_edge(
                            current_user,
                            str(last_other_message["user"]),
                            reply_weight,
                            "reply_gap",
                            gap,
                            conversation_id,
                        )

            for distance, previous_row in enumerate(reversed(recent_records), start=1):
                previous_user = str(previous_row["user"])
                if previous_user == current_user:
                    continue

                gap = max(
                    (row["date"] - previous_row["date"]).total_seconds() / 60,
                    0.1,
                )
                if gap > config.session_gap_minutes:
                    continue

                cluster_weight = config.cluster_weight * math.exp(-gap / config.cluster_decay_divisor) / distance
                add_edge(
                    current_user,
                    previous_user,
                    cluster_weight,
                    "cluster",
                    gap,
                    conversation_id,
                )

            for mentioned_user in _extract_mentions(current_message, current_user, alias_map):
                add_edge(
                    current_user,
                    mentioned_user,
                    config.mention_weight,
                    "mention",
                    None,
                    conversation_id,
                )

    graph = nx.DiGraph()
    message_counts = filtered["user"].value_counts().to_dict()
    for user, count in message_counts.items():
        graph.add_node(user, message_count=int(count))

    edge_rows: list[dict[str, object]] = []
    for edge in edge_store.values():
        weight = round(float(edge["weight"]), 2)
        reply_gap_score = round(float(edge["reply_gap_score"]), 2)
        mention_score = round(float(edge["mention_score"]), 2)
        cluster_score = round(float(edge["cluster_score"]), 2)
        conversation_count = len(edge["conversation_ids"])
        avg_gap_minutes = (
            round(sum(edge["gap_values"]) / len(edge["gap_values"]), 2)
            if edge["gap_values"]
            else None
        )
        graph.add_edge(
            str(edge["source"]),
            str(edge["target"]),
            weight=weight,
            reply_gap_score=reply_gap_score,
            mention_score=mention_score,
            cluster_score=cluster_score,
            interactions=int(edge["interactions"]),
            conversation_count=int(conversation_count),
        )
        edge_rows.append(
            {
                "source": edge["source"],
                "target": edge["target"],
                "weight": weight,
                "reply_gap_score": reply_gap_score,
                "mention_score": mention_score,
                "cluster_score": cluster_score,
                "interactions": int(edge["interactions"]),
                "conversation_count": int(conversation_count),
                "avg_gap_minutes": avg_gap_minutes,
            }
        )

    communities = []
    if graph.number_of_edges() > 0:
        communities = list(nx.community.greedy_modularity_communities(graph.to_undirected(), weight="weight"))

    community_lookup = {
        node: community_index + 1
        for community_index, community in enumerate(communities)
        for node in community
    }
    for node in graph.nodes:
        graph.nodes[node]["community"] = community_lookup.get(node, 0)

    edge_df = pd.DataFrame(edge_rows)
    if not edge_df.empty:
        edge_df = edge_df.sort_values("weight", ascending=False).reset_index(drop=True)

    node_df = pd.DataFrame(
        [
            {
                "user": node,
                "message_count": graph.nodes[node]["message_count"],
                "community": graph.nodes[node]["community"],
            }
            for node in graph.nodes
        ]
    )
    if not node_df.empty:
        node_df = node_df.sort_values("message_count", ascending=False).reset_index(drop=True)

    session_df = (
        filtered.groupby("conversation_id")
        .agg(
            start_time=("date", "min"),
            end_time=("date", "max"),
            messages=("message", "size"),
            participants=("user", "nunique"),
        )
        .reset_index()
    )
    session_df["duration_minutes"] = (
        session_df["end_time"] - session_df["start_time"]
    ).dt.total_seconds().div(60).round(1)

    metrics_df = pd.DataFrame()
    roles_df = pd.DataFrame()
    if graph.number_of_nodes() >= 1:
        weighted_graph = graph.to_undirected()
        density = nx.density(weighted_graph)
        reciprocity = nx.reciprocity(graph)
        clustering = nx.average_clustering(weighted_graph, weight="weight") if weighted_graph.number_of_edges() else 0.0
        metrics_df = pd.DataFrame(
            [
                {"metric": "participants", "value": float(graph.number_of_nodes())},
                {"metric": "edges", "value": float(graph.number_of_edges())},
                {"metric": "density", "value": round(float(density), 4)},
                {"metric": "reciprocity", "value": round(float(reciprocity or 0.0), 4)},
                {"metric": "avg_clustering", "value": round(float(clustering), 4)},
            ]
        )

        indegree = dict(graph.in_degree(weight="weight"))
        outdegree = dict(graph.out_degree(weight="weight"))
        betweenness = nx.betweenness_centrality(graph, weight="weight", normalized=True) if graph.number_of_edges() else {}
        pagerank = nx.pagerank(graph, weight="weight") if graph.number_of_edges() else {node: 0.0 for node in graph.nodes}
        roles_df = pd.DataFrame(
            [
                {
                    "user": node,
                    "weighted_in_degree": round(float(indegree.get(node, 0.0)), 3),
                    "weighted_out_degree": round(float(outdegree.get(node, 0.0)), 3),
                    "betweenness": round(float(betweenness.get(node, 0.0)), 4),
                    "pagerank": round(float(pagerank.get(node, 0.0)), 4),
                }
                for node in graph.nodes
            ]
        ).sort_values(["pagerank", "betweenness"], ascending=False).reset_index(drop=True)

    if selected_user != "Overall":
        focus_nodes = {selected_user}
        if graph.has_node(selected_user):
            focus_nodes.update(graph.predecessors(selected_user))
            focus_nodes.update(graph.successors(selected_user))
        graph = graph.subgraph(focus_nodes).copy()
        if not edge_df.empty:
            edge_df = edge_df[
                edge_df["source"].isin(focus_nodes) & edge_df["target"].isin(focus_nodes)
            ].reset_index(drop=True)
        if not node_df.empty:
            node_df = node_df[node_df["user"].isin(focus_nodes)].reset_index(drop=True)
        if not session_df.empty:
            relevant_sessions = filtered[filtered["user"].isin(focus_nodes)]["conversation_id"].unique()
            session_df = session_df[session_df["conversation_id"].isin(relevant_sessions)].reset_index(drop=True)
        if not roles_df.empty:
            roles_df = roles_df[roles_df["user"].isin(focus_nodes)].reset_index(drop=True)

    return ConversationNetworkResult(
        graph=graph,
        edges=edge_df,
        nodes=node_df,
        sessions=session_df,
        metrics=metrics_df,
        user_network_roles=roles_df,
    )
