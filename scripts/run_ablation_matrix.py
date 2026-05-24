#!/usr/bin/env python3
"""Expand advanced ablation matrix and register runs in tracking files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


ABLATION_CONFIG = Path("experiments/configs/ablations/advanced_matrix.json")
EXPERIMENT_REGISTRY = Path("experiments/tracking/experiment_registry.csv")
LEADERBOARD_TRACKING = Path("experiments/tracking/leaderboard_tracking.csv")
OUTPUT_DIR = Path("experiments/ablations")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Register advanced ablation runs.")
    parser.add_argument("--base-experiment-id", required=True)
    parser.add_argument("--seed", default="2026")
    parser.add_argument("--fold-scheme", default="grouped-5fold")
    parser.add_argument("--train-data-version", default="unknown")
    parser.add_argument("--inference-backend", default="onnx")
    parser.add_argument("--dry-run", action="store_true", help="Do not append tracking rows")
    return parser.parse_args()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_csv(path: Path, row: Dict[str, str]) -> None:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow({k: row.get(k, "") for k in fieldnames})


def cfg_hash(ablation: str, variant: str, base_experiment_id: str) -> str:
    return hashlib.sha1(f"{base_experiment_id}:{ablation}:{variant}".encode("utf-8")).hexdigest()[:12]


def main() -> int:
    args = parse_args()
    config = json.loads(ABLATION_CONFIG.read_text(encoding="utf-8"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    planned: List[Dict[str, str]] = []
    ts = now_utc()
    for ab in config.get("ablations", []):
        name = ab["name"]
        for variant in ab.get("variants", []):
            exp_id = f"{args.base_experiment_id}__{name}__{variant}"
            row = {
                "experiment_id": exp_id,
                "timestamp_utc": ts,
                "config_hash": cfg_hash(name, variant, args.base_experiment_id),
                "seed": args.seed,
                "fold_scheme": args.fold_scheme,
                "train_data_version": args.train_data_version,
                "inference_backend": args.inference_backend,
                "artifacts_path": f"experiments/ablations/{exp_id}",
                "status": "planned",
                "ablation": name,
                "variant": variant,
                "base_experiment_id": args.base_experiment_id,
            }
            planned.append(row)

            if not args.dry_run:
                append_csv(
                    EXPERIMENT_REGISTRY,
                    {
                        "experiment_id": exp_id,
                        "timestamp_utc": ts,
                        "config_hash": row["config_hash"],
                        "seed": args.seed,
                        "fold_scheme": args.fold_scheme,
                        "train_data_version": args.train_data_version,
                        "inference_backend": args.inference_backend,
                        "artifacts_path": row["artifacts_path"],
                        "status": "planned",
                    },
                )
                append_csv(
                    LEADERBOARD_TRACKING,
                    {
                        "experiment_id": exp_id,
                        "timestamp_utc": ts,
                        "config_hash": row["config_hash"],
                        "cv_score": "",
                        "lb_score": "",
                        "delta_cv": "",
                        "delta_lb": "",
                        "runtime_seconds": "",
                        "model_family": "portfolio",
                        "fusion_method": "rank_power_weighted_fusion",
                        "threshold_method": "global_plus_per_class_override",
                        "notes": f"ablation={name};variant={variant};base={args.base_experiment_id}",
                    },
                )

    out = OUTPUT_DIR / "planned_runs.json"
    out.write_text(json.dumps({"created_at_utc": ts, "runs": planned}, indent=2), encoding="utf-8")
    print(f"Wrote ablation plan: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
