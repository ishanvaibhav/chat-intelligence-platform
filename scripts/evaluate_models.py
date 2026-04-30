from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from chat_analyser.config import load_config  # noqa: E402
from chat_analyser.evaluation import compare_models, load_labeled_dataset, sanitize_model_name  # noqa: E402


DEFAULT_MODELS = [
    "rohanrajpal/bert-base-multilingual-codemixed-cased-sentiment",
    "lxyuan/distilbert-base-multilingual-cased-sentiments-student",
    "tabularisai/multilingual-sentiment-analysis",
]


def _build_metrics_table(results: dict) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for model_name, result in results.items():
        summary_lookup = {
            row["metric"]: row["value"]
            for _, row in result.summary_metrics.iterrows()
        }
        rows.append(
            {
                "model_name": model_name,
                "accuracy": summary_lookup.get("accuracy", 0.0),
                "macro_precision": summary_lookup.get("macro_precision", 0.0),
                "macro_recall": summary_lookup.get("macro_recall", 0.0),
                "macro_f1": summary_lookup.get("macro_f1", 0.0),
            }
        )
    return pd.DataFrame(rows).sort_values(["macro_f1", "accuracy"], ascending=False).reset_index(drop=True)


def _save_bar_plot(df: pd.DataFrame, metric: str, output_path: Path, title: str, color: str) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(df["model_name"], df[metric], color=color)
    ax.set_ylim(0, 1)
    ax.set_ylabel(metric.replace("_", " ").title())
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def _write_markdown_report(
    dataset: pd.DataFrame,
    metrics_df: pd.DataFrame,
    output_dir: Path,
    models: list[str],
) -> Path:
    table_headers = ["model_name", "accuracy", "macro_precision", "macro_recall", "macro_f1"]
    table_lines = [
        "| " + " | ".join(table_headers) + " |",
        "| " + " | ".join(["---"] * len(table_headers)) + " |",
    ]
    for _, row in metrics_df.iterrows():
        table_lines.append(
            "| "
            + " | ".join(str(row[column]) for column in table_headers)
            + " |"
        )

    best_row = metrics_df.iloc[0]
    report_lines = [
        "# Sentiment Benchmark Report",
        "",
        f"- Dataset rows: {len(dataset)}",
        f"- Labels: {', '.join(sorted(dataset['label'].unique()))}",
        f"- Models benchmarked: {len(models)}",
        f"- Selected model: `{best_row['model_name']}`",
        f"- Selection rule: highest macro F1, then highest accuracy",
        "",
        "## Summary Metrics",
        "",
        *table_lines,
        "",
        "## Why This Model Was Chosen",
        "",
        f"`{best_row['model_name']}` achieved the strongest macro F1 on the mixed Hinglish/English validation set, which is the most balanced metric for three-class sentiment tasks. It was therefore kept as the recommended default for portfolio and analysis workflows.",
        "",
        "## Reproducibility",
        "",
        f"- Dataset path: `{ROOT / 'data' / 'sample' / 'sentiment_validation.csv'}`",
        f"- Config path: `{ROOT / 'config' / 'defaults.json'}`",
        f"- Generated artifacts directory: `{output_dir}`",
    ]
    report_path = output_dir / "benchmark_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    return report_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate one or more sentiment models on a labeled dataset.")
    parser.add_argument(
        "--dataset",
        default=str(ROOT / "data" / "sample" / "sentiment_validation.csv"),
        help="CSV file with text,label columns",
    )
    parser.add_argument("--config", default=str(ROOT / "config" / "defaults.json"), help="Path to JSON config")
    parser.add_argument(
        "--model",
        action="append",
        dest="models",
        default=None,
        help="Model name to evaluate; pass multiple times for comparison",
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "outputs" / "model_evaluation"),
        help="Directory for evaluation outputs",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = load_config(args.config)
    dataset = load_labeled_dataset(args.dataset)
    models = args.models or DEFAULT_MODELS
    accuracy_df, per_label_df, results = compare_models(dataset, models, config.sentiment)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    accuracy_df.to_csv(output_dir / "model_accuracy.csv", index=False)
    per_label_df.to_csv(output_dir / "model_per_label_metrics.csv", index=False)
    metrics_df = _build_metrics_table(results)
    metrics_df.to_csv(output_dir / "model_summary_metrics.csv", index=False)

    for model_name, result in results.items():
        safe_name = sanitize_model_name(model_name)
        result.predictions.to_csv(output_dir / f"{safe_name}_predictions.csv", index=False)
        result.confusion_matrix.to_csv(output_dir / f"{safe_name}_confusion_matrix.csv", index=False)

    _save_bar_plot(metrics_df, "accuracy", output_dir / "benchmark_accuracy.png", "Model Accuracy Comparison", "#1d3557")
    _save_bar_plot(metrics_df, "macro_f1", output_dir / "benchmark_macro_f1.png", "Model Macro F1 Comparison", "#2a9d8f")
    report_path = _write_markdown_report(dataset, metrics_df, output_dir, models)

    best_row = metrics_df.iloc[0]
    selection_path = output_dir / "selected_model.json"
    selection_path.write_text(
        json.dumps(
            {
                "selected_model": best_row["model_name"],
                "accuracy": best_row["accuracy"],
                "macro_f1": best_row["macro_f1"],
                "dataset_rows": len(dataset),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Best model: {best_row['model_name']}")
    print(f"Accuracy: {best_row['accuracy']}")
    print(f"Macro F1: {best_row['macro_f1']}")
    print(f"Benchmark report: {report_path}")
    print(f"Outputs written to: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
