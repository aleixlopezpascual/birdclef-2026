#!/usr/bin/env python3
"""Validate submission.csv contract quickly before upload."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate BirdCLEF submission file structure.")
    parser.add_argument("--submission", default="submission.csv")
    parser.add_argument("--min-class-columns", type=int, default=200)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.submission)
    if not path.exists():
        raise FileNotFoundError(f"Submission file not found: {path}")

    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        if not cols or cols[0] != "row_id":
            raise ValueError("First column must be row_id")
        class_cols = cols[1:]
        if len(class_cols) < args.min_class_columns:
            raise ValueError(
                f"Expected at least {args.min_class_columns} class columns, got {len(class_cols)}"
            )

        seen = set()
        for i, row in enumerate(reader, start=1):
            rid = row.get("row_id", "")
            if not rid:
                raise ValueError(f"Missing row_id at data row {i}")
            if rid in seen:
                raise ValueError(f"Duplicate row_id detected: {rid}")
            seen.add(rid)
            for c in class_cols:
                v = row.get(c, "")
                if v == "":
                    raise ValueError(f"Empty value at row_id={rid}, col={c}")
                x = float(v)
                if x < 0.0 or x > 1.0:
                    raise ValueError(f"Out-of-range probability at row_id={rid}, col={c}: {x}")

    print(
        f"Submission contract OK: rows={len(seen)}, class_columns={len(class_cols)}, file={path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
