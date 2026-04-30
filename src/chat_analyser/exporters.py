from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .config import ExportConfig


def export_frames(
    frames: dict[str, pd.DataFrame],
    output_dir: str | Path,
    config: ExportConfig,
) -> list[Path]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    written_paths: list[Path] = []

    for name, frame in frames.items():
        if frame is None or (frame.empty and len(frame.columns) == 0):
            continue

        if config.include_csv:
            csv_path = target_dir / f"{name}.csv"
            frame.to_csv(csv_path, index=False)
            written_paths.append(csv_path)

        if config.include_parquet:
            parquet_path = target_dir / f"{name}.parquet"
            frame.to_parquet(parquet_path, index=False)
            written_paths.append(parquet_path)

    return written_paths


def export_metadata(metadata: dict[str, Any], output_dir: str | Path) -> Path:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = target_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
    return metadata_path
