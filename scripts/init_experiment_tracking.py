#!/usr/bin/env python3
"""Initialize experiment and leaderboard tracking files."""

from __future__ import annotations

import csv
from pathlib import Path


TRACKING_DIR = Path("experiments/tracking")
FILES = {
    "leaderboard_tracking.csv": [
        "experiment_id",
        "timestamp_utc",
        "config_hash",
        "cv_score",
        "lb_score",
        "delta_cv",
        "delta_lb",
        "runtime_seconds",
        "model_family",
        "fusion_method",
        "threshold_method",
        "notes",
    ],
    "experiment_registry.csv": [
        "experiment_id",
        "timestamp_utc",
        "config_hash",
        "seed",
        "fold_scheme",
        "train_data_version",
        "inference_backend",
        "artifacts_path",
        "status",
    ],
}


def ensure_csv(path: Path, header: list[str]) -> None:
    if path.exists():
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)


def main() -> int:
    TRACKING_DIR.mkdir(parents=True, exist_ok=True)
    for name, header in FILES.items():
        ensure_csv(TRACKING_DIR / name, header)
    print(f"Initialized tracking files in {TRACKING_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
