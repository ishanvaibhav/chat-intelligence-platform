from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import AnalysisConfig


def log_experiment(
    config: AnalysisConfig,
    source_name: str,
    selected_user: str,
    metadata: dict[str, Any],
) -> Path | None:
    if not config.tracking.enabled:
        return None

    log_dir = Path(config.tracking.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "run_log.jsonl"
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source_name": source_name,
        "selected_user": selected_user,
        "config": asdict(config),
        "metadata": metadata,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, default=str) + "\n")
    return log_path
