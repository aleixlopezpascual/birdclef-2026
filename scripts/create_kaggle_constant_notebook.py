#!/usr/bin/env python3
"""Create a Kaggle code-competition notebook package for constant baseline."""

from __future__ import annotations

import json
from pathlib import Path


OUTPUT_DIR = Path("experiments/kaggle_submission/constant-baseline-v1")


def notebook_source() -> str:
    return """import glob
import os
import pandas as pd

OUT_PATH = "submission.csv"
CONST_PROB = 0.02

taxonomy_candidates = glob.glob("/kaggle/input/**/taxonomy.csv", recursive=True)
if not taxonomy_candidates:
    raise FileNotFoundError("taxonomy.csv not found under /kaggle/input")
TAXONOMY_PATH = sorted(taxonomy_candidates)[0]

taxonomy = pd.read_csv(TAXONOMY_PATH)
class_cols = taxonomy["primary_label"].tolist()

# Code competitions may not expose hidden test files during a plain run.
# Prefer sample_submission row_id as the robust source of required rows.
sample_candidates = glob.glob("/kaggle/input/**/sample_submission.csv", recursive=True)
if sample_candidates:
    SAMPLE_PATH = sorted(sample_candidates)[0]
    rows = pd.read_csv(SAMPLE_PATH)["row_id"].tolist()
else:
    soundscape_dirs = glob.glob("/kaggle/input/**/test_soundscapes", recursive=True)
    if not soundscape_dirs:
        raise FileNotFoundError("Neither sample_submission.csv nor test_soundscapes was found.")
    TEST_GLOB = os.path.join(sorted(soundscape_dirs)[0], "*.ogg")
    test_files = sorted(glob.glob(TEST_GLOB))
    if not test_files:
        raise FileNotFoundError(f"No test soundscape files matched {TEST_GLOB}")
    rows = []
    for path in test_files:
        stem = os.path.splitext(os.path.basename(path))[0]
        for end_sec in range(5, 61, 5):
            rows.append(f"{stem}_{end_sec}")

submission = pd.DataFrame({"row_id": rows, **{c: CONST_PROB for c in class_cols}})

submission.to_csv(OUT_PATH, index=False)
print(submission.shape)
print(f"Wrote {OUT_PATH}")
"""


def notebook_json() -> dict:
    return {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [line + "\n" for line in notebook_source().splitlines()],
            }
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def metadata_json() -> dict:
    return {
        "id": "aleixlopez/birdclef-2026-constant-baseline-v1",
        "title": "BirdCLEF 2026 Constant Baseline V1",
        "code_file": "constant_baseline_v1.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": False,
        "enable_internet": False,
        "competition_sources": ["birdclef-2026"],
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "constant_baseline_v1.ipynb").write_text(
        json.dumps(notebook_json(), indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "kernel-metadata.json").write_text(
        json.dumps(metadata_json(), indent=2), encoding="utf-8"
    )
    print(f"Wrote Kaggle package at: {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
