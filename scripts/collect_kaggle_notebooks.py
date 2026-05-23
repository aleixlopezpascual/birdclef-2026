#!/usr/bin/env python3
"""Collect top Kaggle notebooks for a competition and download sources."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download top-scored and most-voted Kaggle notebooks."
    )
    parser.add_argument("--competition", default="birdclef-2026")
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument(
        "--output-dir", default="data/external/kaggle-notebooks", help="Destination folder"
    )
    parser.add_argument("--kaggle-bin", default="kaggle")
    return parser.parse_args()


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONWARNINGS"] = "ignore"
    return subprocess.run(cmd, check=False, text=True, capture_output=True, env=env)


def normalize_row(row: Dict[str, str]) -> Dict[str, str]:
    return {k.strip().lower(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}


def first_present(data: Dict[str, str], keys: List[str]) -> str:
    for key in keys:
        if key in data and data[key]:
            return str(data[key])
    return ""


def fetch_bucket(
    kaggle_bin: str, competition: str, sort_by: str, page_size: int
) -> List[Dict[str, str]]:
    cmd = [
        kaggle_bin,
        "kernels",
        "list",
        "--competition",
        competition,
        "--sort-by",
        sort_by,
        "--page-size",
        str(page_size),
        "--page",
        "1",
        "--csv",
    ]
    proc = run_cmd(cmd)
    if proc.returncode != 0:
        output = "\n".join([(proc.stderr or "").strip(), (proc.stdout or "").strip()]).strip()
        output_lower = output.lower()
        if "401" in output or "unauthorized" in output_lower:
            raise RuntimeError(
                "Kaggle API authentication failed (401 Unauthorized). "
                "Refresh ~/.kaggle/kaggle.json or set KAGGLE_USERNAME/KAGGLE_KEY."
            )
        raise RuntimeError(output or "Failed to list kernels")

    reader = csv.DictReader(proc.stdout.splitlines())
    return [normalize_row(row) for row in reader]


def safe_ref(ref: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", ref)


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    if args.top_n <= 0:
        raise ValueError("--top-n must be > 0")

    output_dir = Path(args.output_dir)
    metadata_dir = output_dir / "metadata"
    notebooks_dir = output_dir / "notebooks"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    notebooks_dir.mkdir(parents=True, exist_ok=True)

    page_size = min(max(args.top_n, 1), 200)
    fetched_at = datetime.now(timezone.utc).isoformat()

    buckets = OrderedDict(
        [
            ("top_score", "scoreDescending"),
            ("top_votes", "voteCount"),
        ]
    )

    all_rows: List[Dict[str, object]] = []
    unique_refs: OrderedDict[str, Dict[str, object]] = OrderedDict()

    for bucket_name, sort_by in buckets.items():
        rows = fetch_bucket(args.kaggle_bin, args.competition, sort_by, page_size)[: args.top_n]
        bucket_rows: List[Dict[str, object]] = []
        for rank, row in enumerate(rows, start=1):
            ref = first_present(row, ["ref", "kernelref", "id"])
            if not ref:
                continue
            entry = {
                "bucket": bucket_name,
                "bucket_rank": rank,
                "sort_by": sort_by,
                "ref": ref,
                "title": first_present(row, ["title", "kerneltitle", "kernelname"]),
                "author": first_present(row, ["author", "ownername", "owner"]),
                "votes": first_present(row, ["totalvotes", "votes", "votecount"]),
                "score": first_present(row, ["score", "bestscore", "publicscore"]),
                "last_run_time": first_present(row, ["lastruntime", "daterun", "lastruntime"]),
                "fetched_at_utc": fetched_at,
            }
            bucket_rows.append(entry)
            all_rows.append(entry)

            if ref not in unique_refs:
                unique_refs[ref] = {
                    "ref": ref,
                    "title": entry["title"],
                    "author": entry["author"],
                    "votes": entry["votes"],
                    "score": entry["score"],
                    "last_run_time": entry["last_run_time"],
                    "buckets": [bucket_name],
                    "bucket_ranks": [f"{bucket_name}:{rank}"],
                    "fetched_at_utc": fetched_at,
                }
            else:
                unique_refs[ref]["buckets"].append(bucket_name)
                unique_refs[ref]["bucket_ranks"].append(f"{bucket_name}:{rank}")

        write_csv(metadata_dir / f"{bucket_name}.csv", bucket_rows)

    downloaded: List[Dict[str, object]] = []
    for ref, item in unique_refs.items():
        local_dir = notebooks_dir / safe_ref(ref)
        local_dir.mkdir(parents=True, exist_ok=True)
        cmd = [args.kaggle_bin, "kernels", "pull", ref, "--path", str(local_dir), "--metadata"]
        proc = run_cmd(cmd)
        downloaded.append(
            {
                "ref": ref,
                "local_dir": str(local_dir),
                "downloaded": proc.returncode == 0,
                "stderr": (proc.stderr or "").strip(),
                "stdout": (proc.stdout or "").strip(),
            }
        )

    unique_rows: List[Dict[str, object]] = []
    for ref, item in unique_refs.items():
        unique_rows.append(
            {
                **item,
                "buckets": ";".join(item["buckets"]),
                "bucket_ranks": ";".join(item["bucket_ranks"]),
            }
        )

    write_csv(metadata_dir / "combined_index.csv", unique_rows)
    write_csv(metadata_dir / "all_bucket_rows.csv", all_rows)
    write_csv(metadata_dir / "download_status.csv", downloaded)

    summary = {
        "competition": args.competition,
        "top_n_per_bucket": args.top_n,
        "fetched_at_utc": fetched_at,
        "bucket_counts": {k: args.top_n for k in buckets.keys()},
        "rows_collected": len(all_rows),
        "unique_notebooks": len(unique_rows),
        "download_success_count": sum(1 for d in downloaded if d["downloaded"]),
        "download_failure_count": sum(1 for d in downloaded if not d["downloaded"]),
    }
    (metadata_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )

    failures = [d for d in downloaded if not d["downloaded"]]
    if failures:
        print(
            "Notebook listing succeeded, but some downloads failed. "
            "Check metadata/download_status.csv for details.",
            file=sys.stderr,
        )
        return 2

    print(
        f"Collected {len(all_rows)} rows across buckets, "
        f"{len(unique_rows)} unique notebooks downloaded."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # Explicitly surface failures to caller.
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
