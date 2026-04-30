from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import emoji
import pandas as pd
from urlextract import URLExtract


MEDIA_MESSAGE = "<Media omitted>"
DELETED_MESSAGE = "This message was deleted"
URL_EXTRACTOR = URLExtract()
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9']+")
STOP_WORDS_PATH = Path(__file__).resolve().parents[2] / "stop_hinglish.txt"


def _load_stop_words() -> set[str]:
    if not STOP_WORDS_PATH.exists():
        return set()
    return {
        word.strip().lower()
        for word in STOP_WORDS_PATH.read_text(encoding="utf-8").splitlines()
        if word.strip()
    }


STOP_WORDS = _load_stop_words()


def filter_messages(selected_user: str, df: pd.DataFrame) -> pd.DataFrame:
    if selected_user == "Overall":
        return df.copy()
    return df[df["user"] == selected_user].copy()


def text_messages(selected_user: str, df: pd.DataFrame) -> pd.DataFrame:
    filtered = filter_messages(selected_user, df)
    return filtered[
        (filtered["user"] != "group_notification")
        & (filtered["message"] != MEDIA_MESSAGE)
        & (filtered["message"] != DELETED_MESSAGE)
    ].copy()


def fetch_stats(selected_user: str, df: pd.DataFrame) -> tuple[int, int, int, int]:
    filtered = filter_messages(selected_user, df)
    num_messages = filtered.shape[0]
    words = sum(len(TOKEN_PATTERN.findall(str(message))) for message in filtered["message"])
    num_media_messages = int((filtered["message"] == MEDIA_MESSAGE).sum())
    links = sum(len(URL_EXTRACTOR.find_urls(str(message))) for message in filtered["message"])
    return num_messages, words, num_media_messages, links


def most_busy_users(df: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    user_df = df[df["user"] != "group_notification"]
    top_users = user_df["user"].value_counts().head()
    percent_df = (
        (user_df["user"].value_counts(normalize=True) * 100)
        .round(2)
        .rename_axis("user")
        .reset_index(name="percent")
    )
    return top_users, percent_df


def word_frequency(selected_user: str, df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    filtered = text_messages(selected_user, df)
    tokens: list[str] = []
    for message in filtered["message"]:
        for token in TOKEN_PATTERN.findall(str(message).lower()):
            if token not in STOP_WORDS and len(token) > 1:
                tokens.append(token)
    counts = Counter(tokens).most_common(top_n)
    return pd.DataFrame(counts, columns=["word", "count"])


def most_common_words(selected_user: str, df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    return word_frequency(selected_user, df, top_n=top_n)


def monthly_timeline(selected_user: str, df: pd.DataFrame) -> pd.DataFrame:
    filtered = filter_messages(selected_user, df)
    timeline = (
        filtered.groupby(["year", "month_num", "month"])
        .size()
        .reset_index(name="message_count")
        .sort_values(["year", "month_num"])
    )
    timeline["time"] = timeline["month"] + "-" + timeline["year"].astype(str)
    return timeline


def daily_timeline(selected_user: str, df: pd.DataFrame) -> pd.DataFrame:
    filtered = filter_messages(selected_user, df)
    return filtered.groupby("only_date").size().reset_index(name="message_count")


def week_activity_map(selected_user: str, df: pd.DataFrame) -> pd.Series:
    filtered = filter_messages(selected_user, df)
    return filtered["day_name"].value_counts().reindex(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        fill_value=0,
    )


def month_activity_map(selected_user: str, df: pd.DataFrame) -> pd.Series:
    filtered = filter_messages(selected_user, df)
    months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    return filtered["month"].value_counts().reindex(months, fill_value=0)


def activity_heatmap(selected_user: str, df: pd.DataFrame) -> pd.DataFrame:
    filtered = filter_messages(selected_user, df)
    ordered_days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    period_order = [f"{hour:02d}-{((hour + 1) % 24):02d}" for hour in range(24)]
    heatmap = filtered.pivot_table(
        index="day_name",
        columns="period",
        values="message",
        aggfunc="count",
        fill_value=0,
    )
    return heatmap.reindex(index=ordered_days, columns=period_order, fill_value=0)


def emoji_counts(selected_user: str, df: pd.DataFrame) -> pd.DataFrame:
    filtered = filter_messages(selected_user, df)
    found_emojis: list[str] = []
    for message in filtered["message"]:
        found_emojis.extend(char for char in str(message) if emoji.is_emoji(char))
    return pd.DataFrame(Counter(found_emojis).most_common(), columns=["emoji", "count"])


def series_to_frame(series: pd.Series, index_name: str, value_name: str) -> pd.DataFrame:
    return series.rename_axis(index_name).reset_index(name=value_name)
