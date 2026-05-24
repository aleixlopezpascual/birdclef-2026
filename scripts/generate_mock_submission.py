#!/usr/bin/env python3
"""Generate a synthetic submission file for pipeline smoke tests."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a mock submission.csv for smoke tests.")
    parser.add_argument("--output", default="experiments/runtime/mock/submission.csv")
    parser.add_argument("--rows", type=int, default=12)
    parser.add_argument("--classes", type=int, default=234)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    class_cols = [f"class_{i:03d}" for i in range(args.classes)]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["row_id", *class_cols])
        for i in range(args.rows):
            row_id = f"MOCK_SOUND_{i:04d}_5"
            probs = [f"{(i + j) % 100 / 100:.4f}" for j in range(args.classes)]
            writer.writerow([row_id, *probs])
    print(f"Wrote mock submission: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
