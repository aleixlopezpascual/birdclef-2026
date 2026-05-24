#!/usr/bin/env python3
"""Run runtime-hardening checks and persist experiment tracking artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import resource
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


LEADERBOARD_TRACKING = Path("experiments/tracking/leaderboard_tracking.csv")
EXPERIMENT_REGISTRY = Path("experiments/tracking/experiment_registry.csv")
RUNTIME_DIR = Path("experiments/runtime")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run runtime hardening checks for a submission.")
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--submission", required=True)
    parser.add_argument("--min-class-columns", type=int, default=234)
    parser.add_argument("--inference-cmd", default="", help="Optional command to generate submission")
    parser.add_argument("--repeat", type=int, default=2, help="Determinism repeats")
    parser.add_argument("--inference-backend", default="onnx")
    parser.add_argument("--config-hash", default="pending")
    parser.add_argument("--seed", default="2026")
    parser.add_argument("--fold-scheme", default="grouped-5fold")
    parser.add_argument("--train-data-version", default="unknown")
    parser.add_argument("--model-family", default="portfolio")
    parser.add_argument("--fusion-method", default="rank_power_weighted_fusion")
    parser.add_argument("--threshold-method", default="global_plus_per_class_override")
    return parser.parse_args()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def validate_submission(path: Path, min_class_columns: int) -> Dict[str, int]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        if not fieldnames or fieldnames[0] != "row_id":
            raise ValueError("submission must start with row_id column")
        class_cols = fieldnames[1:]
        if len(class_cols) < min_class_columns:
            raise ValueError(
                f"expected at least {min_class_columns} class columns, got {len(class_cols)}"
            )
        seen = set()
        for i, row in enumerate(reader, start=1):
            rid = row.get("row_id", "")
            if not rid:
                raise ValueError(f"missing row_id at row {i}")
            if rid in seen:
                raise ValueError(f"duplicate row_id: {rid}")
            seen.add(rid)
            for c in class_cols:
                v = row.get(c, "")
                if v == "":
                    raise ValueError(f"empty probability at row_id={rid}, class={c}")
                x = float(v)
                if x < 0.0 or x > 1.0:
                    raise ValueError(f"probability out of range at row_id={rid}, class={c}")
    return {"rows": len(seen), "class_columns": len(class_cols)}


def append_csv(path: Path, row: Dict[str, str]) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Tracking file missing: {path}")
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow({k: row.get(k, "") for k in fieldnames})


def run_command(cmd: str) -> Dict[str, float]:
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    start = datetime.now(timezone.utc)
    completed = subprocess.run(cmd, shell=True, check=True, text=True, capture_output=True)
    end = datetime.now(timezone.utc)
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
        "duration_seconds": (end - start).total_seconds(),
        "max_rss_kb_delta": max(0.0, after.ru_maxrss - before.ru_maxrss),
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }


def main() -> int:
    args = parse_args()
    submission = Path(args.submission)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    out_dir = RUNTIME_DIR / args.experiment_id
    out_dir.mkdir(parents=True, exist_ok=True)

    run_results: List[Dict[str, float | str]] = []
    checksums: List[str] = []
    validation_info = None

    for _ in range(args.repeat):
        execution = {}
        if args.inference_cmd:
            execution = run_command(args.inference_cmd)
        if not submission.exists():
            raise FileNotFoundError(f"submission not found after run: {submission}")
        validation_info = validate_submission(submission, args.min_class_columns)
        checksums.append(sha256(submission))
        run_results.append(execution)

    deterministic = len(set(checksums)) == 1
    runtime_seconds = max((float(r.get("duration_seconds", 0.0)) for r in run_results), default=0.0)
    max_rss_kb = max((float(r.get("max_rss_kb_delta", 0.0)) for r in run_results), default=0.0)

    report = {
        "experiment_id": args.experiment_id,
        "created_at_utc": now_utc(),
        "submission_path": str(submission),
        "inference_cmd": args.inference_cmd,
        "repeat": args.repeat,
        "deterministic": deterministic,
        "checksums": checksums,
        "runtime_seconds_max": runtime_seconds,
        "max_rss_kb_delta_max": max_rss_kb,
        "validation": validation_info,
        "runs": run_results,
    }
    (out_dir / "runtime_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    append_csv(
        EXPERIMENT_REGISTRY,
        {
            "experiment_id": args.experiment_id,
            "timestamp_utc": now_utc(),
            "config_hash": args.config_hash,
            "seed": args.seed,
            "fold_scheme": args.fold_scheme,
            "train_data_version": args.train_data_version,
            "inference_backend": args.inference_backend,
            "artifacts_path": str(out_dir),
            "status": "runtime_hardened" if deterministic else "runtime_nondeterministic",
        },
    )

    append_csv(
        LEADERBOARD_TRACKING,
        {
            "experiment_id": args.experiment_id,
            "timestamp_utc": now_utc(),
            "config_hash": args.config_hash,
            "cv_score": "",
            "lb_score": "",
            "delta_cv": "",
            "delta_lb": "",
            "runtime_seconds": f"{runtime_seconds:.4f}",
            "model_family": args.model_family,
            "fusion_method": args.fusion_method,
            "threshold_method": args.threshold_method,
            "notes": "runtime_hardening_pass" if deterministic else "runtime_hardening_failed_determinism",
        },
    )

    print(f"Wrote runtime report: {out_dir / 'runtime_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
