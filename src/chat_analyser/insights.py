from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from .analysis import DELETED_MESSAGE, MEDIA_MESSAGE, STOP_WORDS, URL_EXTRACTOR, text_messages
from .config import TopicConfig


MEDIA_PATTERNS = {
    "image": re.compile(r"\b(?:image omitted|photo omitted|jpg|jpeg|png)\b", re.IGNORECASE),
    "video": re.compile(r"\b(?:video omitted|mp4|mov|video)\b", re.IGNORECASE),
    "audio": re.compile(r"\b(?:audio omitted|voice message|opus|mp3|wav)\b", re.IGNORECASE),
    "document": re.compile(r"\b(?:document omitted|pdf|docx|pptx|xlsx|file)\b", re.IGNORECASE),
    "sticker": re.compile(r"\bsticker\b", re.IGNORECASE),
    "media": re.compile(r"<media omitted>", re.IGNORECASE),
}
ENTITY_PATTERNS = {
    "date": re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),
    "time": re.compile(r"\b\d{1,2}:\d{2}\s?(?:am|pm)?\b", re.IGNORECASE),
    "money": re.compile(r"(?:₹|\$|rs\.?)\s?\d+(?:,\d{3})*(?:\.\d+)?", re.IGNORECASE),
    "email": re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b"),
}
ACTION_PATTERNS = {
    "request": re.compile(r"\b(?:please|plz|can you|could you|kindly)\b", re.IGNORECASE),
    "deadline": re.compile(r"\b(?:today|tomorrow|tonight|asap|eod|morning|evening|deadline)\b", re.IGNORECASE),
    "decision": re.compile(r"\b(?:decide|agreed|final|approved|confirmed)\b", re.IGNORECASE),
    "issue": re.compile(r"\b(?:bug|issue|error|problem|slow|broken|delay|crash)\b", re.IGNORECASE),
}
CAPITALIZED_ENTITY_PATTERN = re.compile(r"\b[A-Z][a-z]{2,}\b")
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9']+")


@dataclass
class InsightBundle:
    media_summary: pd.DataFrame
    media_by_user: pd.DataFrame
    link_domains: pd.DataFrame
    entities: pd.DataFrame
    action_items: pd.DataFrame
    behavior_profiles: pd.DataFrame
    behavior_summary: pd.DataFrame
    topics: pd.DataFrame
    topic_messages: pd.DataFrame
    session_summaries: pd.DataFrame


def _infer_media_type(message: str) -> str | None:
    lowered = str(message).strip()
    if lowered == MEDIA_MESSAGE:
        return "media"

    for media_type, pattern in MEDIA_PATTERNS.items():
        if pattern.search(lowered):
            return media_type
    return None


def media_analytics(selected_user: str, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    filtered = df.copy() if selected_user == "Overall" else df[df["user"] == selected_user].copy()
    filtered["media_type"] = filtered["message"].map(_infer_media_type)
    media_df = filtered[filtered["media_type"].notna() & (filtered["user"] != "group_notification")].copy()

    if media_df.empty:
        return pd.DataFrame(columns=["media_type", "count"]), pd.DataFrame(columns=["user", "media_type", "count"])

    summary_df = media_df["media_type"].value_counts().rename_axis("media_type").reset_index(name="count")
    by_user_df = (
        media_df.groupby(["user", "media_type"])
        .size()
        .reset_index(name="count")
        .sort_values(["count", "user"], ascending=[False, True])
        .reset_index(drop=True)
    )
    return summary_df, by_user_df


def link_domain_analysis(selected_user: str, df: pd.DataFrame) -> pd.DataFrame:
    filtered = text_messages(selected_user, df)
    rows: list[dict[str, object]] = []
    for _, row in filtered.iterrows():
        message = str(row["message"])
        for url in URL_EXTRACTOR.find_urls(message):
            parsed = urlparse(url if "://" in url else f"https://{url}")
            domain = parsed.netloc or parsed.path.split("/")[0]
            domain = domain.lower().replace("www.", "")
            rows.append({"user": row["user"], "domain": domain, "url": url})

    if not rows:
        return pd.DataFrame(columns=["domain", "count", "users"])

    domain_df = pd.DataFrame(rows)
    return (
        domain_df.groupby("domain")
        .agg(count=("url", "size"), users=("user", "nunique"))
        .reset_index()
        .sort_values("count", ascending=False)
        .reset_index(drop=True)
    )


def entity_and_action_analysis(selected_user: str, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    filtered = text_messages(selected_user, df)
    entity_rows: list[dict[str, object]] = []
    action_rows: list[dict[str, object]] = []

    for _, row in filtered.iterrows():
        message = str(row["message"])
        found_entities: list[tuple[str, str]] = []
        for entity_type, pattern in ENTITY_PATTERNS.items():
            for match in pattern.findall(message):
                found_entities.append((entity_type, match))
        for match in CAPITALIZED_ENTITY_PATTERN.findall(message):
            if match.lower() not in STOP_WORDS and match not in {"This", "That", "When"}:
                found_entities.append(("named_entity", match))

        for entity_type, value in found_entities:
            entity_rows.append(
                {
                    "date": row["date"],
                    "user": row["user"],
                    "entity_type": entity_type,
                    "entity_value": value,
                    "message": message,
                }
            )

        matched_tags = [tag for tag, pattern in ACTION_PATTERNS.items() if pattern.search(message)]
        if matched_tags:
            action_rows.append(
                {
                    "date": row["date"],
                    "user": row["user"],
                    "tags": ", ".join(sorted(matched_tags)),
                    "message": message,
                }
            )

    entities_df = pd.DataFrame(entity_rows)
    actions_df = pd.DataFrame(action_rows)
    return entities_df, actions_df


def user_behavior_profiles(selected_user: str, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    filtered = text_messages("Overall", df).sort_values("date").reset_index(drop=True)
    if filtered.empty:
        empty_df = pd.DataFrame()
        return empty_df, empty_df

    filtered["gap_minutes"] = filtered["date"].diff().dt.total_seconds().div(60)
    filtered["is_conversation_start"] = filtered["gap_minutes"].fillna(9999) > 45
    filtered["reply_gap_to_previous"] = filtered["gap_minutes"].where(
        filtered["user"] != filtered["user"].shift(1)
    )
    filtered["word_count"] = filtered["message"].map(lambda value: len(TOKEN_PATTERN.findall(str(value))))
    filtered["links_shared"] = filtered["message"].map(lambda value: len(URL_EXTRACTOR.find_urls(str(value))))
    filtered["questions_asked"] = filtered["message"].astype(str).str.count(r"\?")

    profile_df = (
        filtered.groupby("user")
        .agg(
            messages=("message", "size"),
            avg_words=("word_count", "mean"),
            conversation_starts=("is_conversation_start", "sum"),
            avg_reply_minutes=("reply_gap_to_previous", "mean"),
            links_shared=("links_shared", "sum"),
            questions_asked=("questions_asked", "sum"),
        )
        .reset_index()
    )
    profile_df["avg_words"] = profile_df["avg_words"].round(2)
    profile_df["avg_reply_minutes"] = profile_df["avg_reply_minutes"].fillna(0).round(2)

    most_talkative = profile_df.sort_values("messages", ascending=False).head(1)
    fastest_replier = profile_df[profile_df["avg_reply_minutes"] > 0].sort_values("avg_reply_minutes").head(1)
    question_asker = profile_df.sort_values("questions_asked", ascending=False).head(1)
    starter = profile_df.sort_values("conversation_starts", ascending=False).head(1)
    summary_rows = []
    if not most_talkative.empty:
        summary_rows.append({"metric": "Most talkative", "user": most_talkative.iloc[0]["user"], "value": int(most_talkative.iloc[0]["messages"])})
    if not fastest_replier.empty:
        summary_rows.append({"metric": "Fastest replier", "user": fastest_replier.iloc[0]["user"], "value": float(fastest_replier.iloc[0]["avg_reply_minutes"])})
    if not question_asker.empty:
        summary_rows.append({"metric": "Most questions", "user": question_asker.iloc[0]["user"], "value": int(question_asker.iloc[0]["questions_asked"])})
    if not starter.empty:
        summary_rows.append({"metric": "Conversation starter", "user": starter.iloc[0]["user"], "value": int(starter.iloc[0]["conversation_starts"])})
    summary_df = pd.DataFrame(summary_rows)

    if selected_user != "Overall":
        profile_df = profile_df[profile_df["user"] == selected_user].reset_index(drop=True)
        summary_df = summary_df[summary_df["user"] == selected_user].reset_index(drop=True)

    return profile_df, summary_df


def topic_modeling(selected_user: str, df: pd.DataFrame, config: TopicConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    filtered = text_messages(selected_user, df).copy()
    if not config.enabled or filtered.shape[0] < config.min_messages:
        return pd.DataFrame(columns=["topic_id", "topic_terms", "message_count"]), pd.DataFrame()

    filtered["clean_message"] = filtered["message"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    vectorizer = TfidfVectorizer(stop_words=list(STOP_WORDS), ngram_range=(1, 2), min_df=1)
    matrix = vectorizer.fit_transform(filtered["clean_message"])
    n_topics = max(2, min(config.n_topics, filtered.shape[0]))
    if matrix.shape[1] == 0:
        return pd.DataFrame(columns=["topic_id", "topic_terms", "message_count"]), pd.DataFrame()

    model = KMeans(n_clusters=n_topics, random_state=42, n_init=10)
    labels = model.fit_predict(matrix)
    filtered["topic_id"] = labels

    feature_names = vectorizer.get_feature_names_out()
    topic_rows: list[dict[str, object]] = []
    for topic_id in range(n_topics):
        center = model.cluster_centers_[topic_id]
        top_indices = center.argsort()[::-1][: config.top_terms_per_topic]
        topic_terms = ", ".join(feature_names[index] for index in top_indices)
        message_count = int((filtered["topic_id"] == topic_id).sum())
        topic_rows.append({"topic_id": topic_id, "topic_terms": topic_terms, "message_count": message_count})

    topic_df = pd.DataFrame(topic_rows).sort_values("message_count", ascending=False).reset_index(drop=True)
    topic_messages_df = filtered[["date", "user", "message", "topic_id"]].copy()
    return topic_df, topic_messages_df


def session_summaries(selected_user: str, df: pd.DataFrame, session_gap_minutes: int = 45) -> pd.DataFrame:
    filtered = text_messages(selected_user, df).sort_values("date").reset_index(drop=True)
    if filtered.empty:
        return pd.DataFrame(columns=["conversation_id", "summary", "participants", "messages"])

    filtered["gap_minutes"] = filtered["date"].diff().dt.total_seconds().div(60).fillna(0)
    filtered["conversation_id"] = (filtered["gap_minutes"] > session_gap_minutes).cumsum()
    rows: list[dict[str, object]] = []

    for conversation_id, group in filtered.groupby("conversation_id", sort=False):
        participants = ", ".join(sorted(group["user"].unique()))
        candidate_messages = group["message"].astype(str).tolist()
        scored_messages = sorted(
            candidate_messages,
            key=lambda value: (
                value.count("?") * 2
                + sum(1 for tag, pattern in ACTION_PATTERNS.items() if pattern.search(value))
                + math.log(len(value.split()) + 1)
            ),
            reverse=True,
        )
        highlights = scored_messages[:2] if len(scored_messages) >= 2 else scored_messages
        summary = " | ".join(highlights)
        rows.append(
            {
                "conversation_id": int(conversation_id),
                "start_time": group["date"].min(),
                "end_time": group["date"].max(),
                "participants": participants,
                "messages": int(group.shape[0]),
                "summary": summary,
            }
        )

    summary_df = pd.DataFrame(rows)
    return summary_df


def build_insights(selected_user: str, df: pd.DataFrame, topic_config: TopicConfig) -> InsightBundle:
    media_summary, media_by_user = media_analytics(selected_user, df)
    link_domains = link_domain_analysis(selected_user, df)
    entities, action_items = entity_and_action_analysis(selected_user, df)
    behavior_profiles, behavior_summary = user_behavior_profiles(selected_user, df)
    topics, topic_messages = topic_modeling(selected_user, df, topic_config)
    session_summary_df = session_summaries(selected_user, df)
    return InsightBundle(
        media_summary=media_summary,
        media_by_user=media_by_user,
        link_domains=link_domains,
        entities=entities,
        action_items=action_items,
        behavior_profiles=behavior_profiles,
        behavior_summary=behavior_summary,
        topics=topics,
        topic_messages=topic_messages,
        session_summaries=session_summary_df,
    )
