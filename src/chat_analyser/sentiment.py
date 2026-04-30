from __future__ import annotations

from dataclasses import replace
from functools import lru_cache

import pandas as pd

from .analysis import text_messages
from .config import SentimentConfig


SENTIMENT_ORDER = ["Negative", "Neutral", "Positive"]
SENTIMENT_SCORE_MAP = {"Negative": -1, "Neutral": 0, "Positive": 1}


def clean_message_text(message: str) -> str:
    return " ".join(str(message).replace("\n", " ").split())


@lru_cache(maxsize=8)
def load_sentiment_pipeline(model_name: str, framework: str):
    from transformers import pipeline

    return pipeline(
        "text-classification",
        model=model_name,
        tokenizer=model_name,
        framework=framework,
    )


def normalize_label(raw_label: str, label_map: dict[str, str] | None = None) -> str:
    candidate = str(raw_label).strip()
    if label_map:
        candidate = label_map.get(candidate, candidate)

    lowered = candidate.lower()
    if "negative" in lowered or lowered in {"label_0", "0", "neg"}:
        return "Negative"
    if "neutral" in lowered or lowered in {"label_1", "1", "neu"}:
        return "Neutral"
    if "positive" in lowered or lowered in {"label_2", "2", "pos"}:
        return "Positive"
    return candidate.title()


def prepare_sentiment_messages(selected_user: str, df: pd.DataFrame) -> pd.DataFrame:
    filtered = text_messages(selected_user, df)
    filtered["clean_message"] = filtered["message"].map(clean_message_text)
    return filtered[filtered["clean_message"].str.len() > 0].reset_index(drop=True)


def predict_sentiment(
    selected_user: str,
    df: pd.DataFrame,
    config: SentimentConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    filtered = prepare_sentiment_messages(selected_user, df)
    if filtered.empty or not config.enabled:
        empty_df = pd.DataFrame()
        return empty_df, empty_df, empty_df

    classifier = load_sentiment_pipeline(config.model_name, config.framework)
    predictions = classifier(
        filtered["clean_message"].tolist(),
        truncation=True,
        max_length=config.max_length,
        batch_size=config.batch_size,
    )

    filtered["sentiment"] = [
        normalize_label(prediction["label"], config.label_map)
        for prediction in predictions
    ]
    filtered["score"] = [round(float(prediction["score"]), 4) for prediction in predictions]
    filtered["sentiment_score"] = filtered["sentiment"].map(SENTIMENT_SCORE_MAP).fillna(0)

    summary_df = (
        filtered.groupby("sentiment")
        .agg(
            messages=("sentiment", "size"),
            avg_confidence=("score", "mean"),
        )
        .reset_index()
    )
    summary_df["avg_confidence"] = summary_df["avg_confidence"].round(3)
    summary_df["share_percent"] = (
        (summary_df["messages"] / summary_df["messages"].sum()) * 100
    ).round(2)
    summary_df["sentiment"] = pd.Categorical(
        summary_df["sentiment"],
        categories=SENTIMENT_ORDER,
        ordered=True,
    )
    summary_df = summary_df.sort_values("sentiment").reset_index(drop=True)

    timeline_df = (
        filtered.groupby("only_date")
        .agg(
            avg_sentiment=("sentiment_score", "mean"),
            messages=("sentiment_score", "size"),
        )
        .reset_index()
    )
    timeline_df["avg_sentiment"] = timeline_df["avg_sentiment"].round(3)

    return filtered, summary_df, timeline_df


def sentiment_by_user(predictions_df: pd.DataFrame) -> pd.DataFrame:
    if predictions_df.empty:
        return pd.DataFrame()

    pivot = (
        predictions_df.pivot_table(
            index="user",
            columns="sentiment",
            values="message",
            aggfunc="count",
            fill_value=0,
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )
    for column in SENTIMENT_ORDER:
        if column not in pivot.columns:
            pivot[column] = 0
    pivot["Total"] = pivot[SENTIMENT_ORDER].sum(axis=1)
    return pivot.sort_values("Total", ascending=False).reset_index(drop=True)


def predict_texts(texts: list[str], config: SentimentConfig) -> list[str]:
    classifier = load_sentiment_pipeline(config.model_name, config.framework)
    predictions = classifier(
        texts,
        truncation=True,
        max_length=config.max_length,
        batch_size=config.batch_size,
    )
    return [normalize_label(prediction["label"], config.label_map) for prediction in predictions]


def compute_classification_metrics(
    y_true: list[str],
    y_pred: list[str],
    labels: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    labels = labels or SENTIMENT_ORDER
    rows: list[dict[str, float | str]] = []

    for label in labels:
        tp = sum(1 for actual, predicted in zip(y_true, y_pred) if actual == label and predicted == label)
        fp = sum(1 for actual, predicted in zip(y_true, y_pred) if actual != label and predicted == label)
        fn = sum(1 for actual, predicted in zip(y_true, y_pred) if actual == label and predicted != label)
        support = sum(1 for actual in y_true if actual == label)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        rows.append(
            {
                "label": label,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "support": support,
            }
        )

    metrics_df = pd.DataFrame(rows)
    accuracy = sum(1 for actual, predicted in zip(y_true, y_pred) if actual == predicted) / len(y_true)
    summary_df = pd.DataFrame(
        [
            {"metric": "accuracy", "value": round(accuracy, 4)},
            {"metric": "macro_precision", "value": round(metrics_df["precision"].mean(), 4)},
            {"metric": "macro_recall", "value": round(metrics_df["recall"].mean(), 4)},
            {"metric": "macro_f1", "value": round(metrics_df["f1"].mean(), 4)},
        ]
    )
    confusion_df = (
        pd.crosstab(
            pd.Series(y_true, name="actual"),
            pd.Series(y_pred, name="predicted"),
            dropna=False,
        )
        .reindex(index=labels, columns=labels, fill_value=0)
        .reset_index()
    )
    return metrics_df, summary_df, confusion_df


def config_for_model(base_config: SentimentConfig, model_name: str) -> SentimentConfig:
    return replace(base_config, model_name=model_name)
