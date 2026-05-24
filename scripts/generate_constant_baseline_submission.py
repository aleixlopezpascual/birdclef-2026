#!/usr/bin/env python3
"""Generate a simple constant-probability baseline submission."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate constant BirdCLEF submission.")
    parser.add_argument(
        "--sample-submission",
        default="data/competition/raw/sample_submission.csv",
        help="Path to sample_submission.csv",
    )
    parser.add_argument("--output", default="submission.csv")
    parser.add_argument("--prob", type=float, default=0.02)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.prob < 0.0 or args.prob > 1.0:
        raise ValueError("--prob must be in [0, 1]")

    src = Path(args.sample_submission)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    with src.open(encoding="utf-8", newline="") as f_in, out.open(
        "w", encoding="utf-8", newline=""
    ) as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = reader.fieldnames or []
        if not fieldnames or fieldnames[0] != "row_id":
            raise ValueError("sample submission must have row_id as first column")
        class_cols = fieldnames[1:]

        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            out_row = {"row_id": row["row_id"]}
            for c in class_cols:
                out_row[c] = f"{args.prob:.6f}"
            writer.writerow(out_row)

    print(f"Wrote baseline submission: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
