from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import pandas as pd

from .config import SentimentConfig
from .sentiment import compute_classification_metrics, config_for_model, predict_texts


@dataclass
class ModelEvaluationResult:
    model_name: str
    predictions: pd.DataFrame
    per_label_metrics: pd.DataFrame
    summary_metrics: pd.DataFrame
    confusion_matrix: pd.DataFrame


def load_labeled_dataset(path: str | Path) -> pd.DataFrame:
    dataset = pd.read_csv(path)
    required_columns = {"text", "label"}
    if not required_columns.issubset(dataset.columns):
        raise ValueError(f"Dataset must contain columns: {sorted(required_columns)}")
    dataset["label"] = dataset["label"].astype(str).str.title()
    return dataset


def evaluate_model(
    dataset: pd.DataFrame,
    model_name: str,
    base_config: SentimentConfig,
) -> ModelEvaluationResult:
    model_config = config_for_model(base_config, model_name)
    predictions = predict_texts(dataset["text"].astype(str).tolist(), model_config)
    prediction_df = dataset.copy()
    prediction_df["prediction"] = predictions
    prediction_df["correct"] = prediction_df["label"] == prediction_df["prediction"]

    per_label_df, summary_df, confusion_df = compute_classification_metrics(
        prediction_df["label"].tolist(),
        prediction_df["prediction"].tolist(),
    )
    per_label_df.insert(0, "model_name", model_name)
    summary_df.insert(0, "model_name", model_name)
    confusion_df.insert(0, "model_name", model_name)

    return ModelEvaluationResult(
        model_name=model_name,
        predictions=prediction_df,
        per_label_metrics=per_label_df,
        summary_metrics=summary_df,
        confusion_matrix=confusion_df,
    )


def compare_models(
    dataset: pd.DataFrame,
    model_names: list[str],
    base_config: SentimentConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, ModelEvaluationResult]]:
    results: dict[str, ModelEvaluationResult] = {}
    summary_frames: list[pd.DataFrame] = []
    per_label_frames: list[pd.DataFrame] = []

    for model_name in model_names:
        result = evaluate_model(dataset, model_name, base_config)
        results[model_name] = result
        summary_frames.append(result.summary_metrics)
        per_label_frames.append(result.per_label_metrics)

    summary_df = pd.concat(summary_frames, ignore_index=True)
    per_label_df = pd.concat(per_label_frames, ignore_index=True)
    accuracy_df = summary_df[summary_df["metric"] == "accuracy"].sort_values("value", ascending=False)
    return accuracy_df, per_label_df, results


def sanitize_model_name(model_name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", model_name)
