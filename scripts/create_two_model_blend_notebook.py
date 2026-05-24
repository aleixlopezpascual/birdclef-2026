#!/usr/bin/env python3
"""Create a Kaggle notebook package that blends Raunak V6 and Meenal V1 submissions."""

from __future__ import annotations

import json
from pathlib import Path


OUTPUT_DIR = Path("experiments/kaggle_submission/two-model-blend-v1")


def notebook_source() -> str:
    return """import glob
import pandas as pd

OUT_PATH = "submission.csv"
RAUNAK_TOKENS = ["aleixlopez", "birdclef-2026-ported-raunak-v6-v1"]
MEENAL_TOKENS = ["aleixlopez", "birdclef-2026-meenal-v1"]


def _find_submission(required_tokens):
    candidates = glob.glob("/kaggle/input/notebooks/**/submission.csv", recursive=True)
    matches = []
    for path in candidates:
        normalized = path.lower().replace("\\\\", "/")
        if all(token in normalized for token in required_tokens):
            matches.append(path)
    if not matches:
        raise FileNotFoundError(f"Could not find submission.csv matching tokens={required_tokens}")
    return sorted(matches)[-1]


def _find_sample_submission():
    candidates = glob.glob("/kaggle/input/**/sample_submission.csv", recursive=True)
    if not candidates:
        raise FileNotFoundError("sample_submission.csv not found under /kaggle/input")
    return sorted(candidates)[0]


def _align_to_template(df, row_ids, class_cols):
    if "row_id" not in df.columns:
        raise ValueError("Source submission is missing row_id")
    missing_cols = [c for c in class_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Source submission missing class columns: {missing_cols[:5]}")
    aligned = df[["row_id"] + class_cols].drop_duplicates(subset=["row_id"]).set_index("row_id")
    aligned = aligned.reindex(row_ids)
    if aligned.isna().any().any():
        # Fill any missing rows with neutral probabilities to keep valid format.
        aligned = aligned.fillna(0.5)
    return aligned


raunak_path = _find_submission(RAUNAK_TOKENS)
meenal_path = _find_submission(MEENAL_TOKENS)
sample_path = _find_sample_submission()
print("Using Raunak submission:", raunak_path)
print("Using Meenal submission:", meenal_path)
print("Using sample submission template:", sample_path)

raunak = pd.read_csv(raunak_path)
meenal = pd.read_csv(meenal_path)
sample = pd.read_csv(sample_path)

if "row_id" not in sample.columns:
    raise ValueError("sample_submission.csv missing row_id")
class_cols = [c for c in sample.columns if c != "row_id"]
row_ids = sample["row_id"].tolist()

raunak_aligned = _align_to_template(raunak, row_ids, class_cols)
meenal_aligned = _align_to_template(meenal, row_ids, class_cols)

merged = sample[["row_id"]].copy()
for c in class_cols:
    rank_raunak = raunak_aligned[c].rank(method="average", pct=True)
    rank_meenal = meenal_aligned[c].rank(method="average", pct=True)
    merged[c] = 0.5 * rank_raunak + 0.5 * rank_meenal

# Final contract safety: exact column order and no NaNs.
merged = merged[["row_id"] + class_cols].fillna(0.5)
merged.to_csv(OUT_PATH, index=False, float_format="%.10f")
print(merged.shape)
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
        "id": "aleixlopez/birdclef-2026-two-model-blend-v1",
        "title": "BirdCLEF 2026 Two Model Blend V1",
        "code_file": "two_model_blend_v1.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": False,
        "enable_internet": False,
        "competition_sources": ["birdclef-2026"],
        "kernel_sources": [
            "aleixlopez/birdclef-2026-ported-raunak-v6-v1",
            "aleixlopez/birdclef-2026-meenal-v1",
        ],
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "two_model_blend_v1.ipynb").write_text(
        json.dumps(notebook_json(), indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "kernel-metadata.json").write_text(
        json.dumps(metadata_json(), indent=2), encoding="utf-8"
    )
    print(f"Wrote Kaggle package at: {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
