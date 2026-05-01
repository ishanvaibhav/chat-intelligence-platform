from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Any


@dataclass
class SentimentConfig:
    enabled: bool = True
    model_name: str = "tabularisai/multilingual-sentiment-analysis"
    batch_size: int = 16
    max_length: int = 128
    framework: str = "pt"
    label_map: dict[str, str] = field(
        default_factory=lambda: {
            "LABEL_0": "Negative",
            "LABEL_1": "Neutral",
            "LABEL_2": "Positive",
            "0": "Negative",
            "1": "Neutral",
            "2": "Positive",
        }
    )


@dataclass
class GraphConfig:
    enabled: bool = True
    session_gap_minutes: int = 45
    reply_window_minutes: int = 15
    context_window: int = 5
    mention_weight: float = 2.8
    reply_base_weight: float = 1.2
    reply_decay_weight: float = 2.2
    reply_decay_divisor: float = 4.0
    cluster_weight: float = 0.7
    cluster_decay_divisor: float = 12.0


@dataclass
class ExportConfig:
    include_csv: bool = True
    include_parquet: bool = True
    output_dir: str = "outputs/latest_run"


@dataclass
class TopicConfig:
    enabled: bool = True
    n_topics: int = 4
    top_terms_per_topic: int = 6
    min_messages: int = 6


@dataclass
class TrackingConfig:
    enabled: bool = True
    log_dir: str = "outputs/experiment_tracking"


@dataclass
class AnalysisConfig:
    sentiment: SentimentConfig = field(default_factory=SentimentConfig)
    graph: GraphConfig = field(default_factory=GraphConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    topic: TopicConfig = field(default_factory=TopicConfig)
    tracking: TrackingConfig = field(default_factory=TrackingConfig)


def _merge_into_dataclass(instance: Any, overrides: dict[str, Any]) -> Any:
    for key, value in overrides.items():
        if not hasattr(instance, key):
            continue

        current_value = getattr(instance, key)
        if is_dataclass(current_value) and isinstance(value, dict):
            _merge_into_dataclass(current_value, value)
        else:
            setattr(instance, key, value)
    return instance


def load_config(path: str | Path | None = None) -> AnalysisConfig:
    config = AnalysisConfig()
    if path is None:
        return config

    raw_path = Path(path)
    if not raw_path.exists():
        raise FileNotFoundError(f"Config file not found: {raw_path}")

    data = json.loads(raw_path.read_text(encoding="utf-8"))
    return _merge_into_dataclass(config, data)


def save_config(config: AnalysisConfig, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")
    return output_path


def config_to_dict(config: AnalysisConfig) -> dict[str, Any]:
    return asdict(config)
