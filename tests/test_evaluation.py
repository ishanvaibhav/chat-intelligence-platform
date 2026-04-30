from __future__ import annotations

from chat_analyser.sentiment import compute_classification_metrics


def test_compute_classification_metrics_returns_accuracy_and_macro_scores():
    metrics_df, summary_df, confusion_df = compute_classification_metrics(
        ["Positive", "Negative", "Neutral", "Positive"],
        ["Positive", "Negative", "Positive", "Positive"],
    )

    accuracy = summary_df.loc[summary_df["metric"] == "accuracy", "value"].iloc[0]
    assert accuracy == 0.75
    assert set(metrics_df["label"]) == {"Negative", "Neutral", "Positive"}
    assert "actual" in confusion_df.columns
