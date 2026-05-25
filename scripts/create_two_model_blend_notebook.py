#!/usr/bin/env python3
"""Create a Kaggle notebook package that blends Raunak V6 and Meenal V1 submissions."""

from __future__ import annotations

import json
from pathlib import Path


OUTPUT_DIR = Path("experiments/kaggle_submission/two-model-blend-v1")


def notebook_source() -> str:
    return """import csv
import glob
import pandas as pd

OUT_PATH = "submission.csv"
RAUNAK_TOKENS = ["aleixlopez", "birdclef-2026-ported-raunak-v6-v1"]
MEENAL_TOKENS = ["aleixlopez", "birdclef-2026-meenal-v1"]
MIN_EXPECTED_ROWS = 1000


def _csv_shape(path):
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return 0, 0, False
        has_row_id = "row_id" in header
        rows = 1 + sum(1 for _ in reader)
        cols = len(header)
    return rows, cols, has_row_id


def _find_submission(required_tokens):
    candidates = glob.glob("/kaggle/input/notebooks/**/*.csv", recursive=True)
    scored = []
    for path in candidates:
        normalized = path.lower().replace("\\\\", "/")
        if all(token in normalized for token in required_tokens):
            rows, cols, has_row_id = _csv_shape(path)
            if has_row_id and cols >= 200 and rows >= 50:
                scored.append((rows, cols, path))
    if not scored:
        raise FileNotFoundError(f"Could not find submission.csv matching tokens={required_tokens}")
    scored.sort(key=lambda x: (x[0], x[1], x[2]))
    rows, cols, best = scored[-1]
    print(f"Selected source {best} (rows={rows}, cols={cols})")
    return best


def _find_sample_submission():
    candidates = glob.glob("/kaggle/input/**/sample_submission.csv", recursive=True)
    if not candidates:
        raise FileNotFoundError("sample_submission.csv not found under /kaggle/input")
    return sorted(candidates)[0]


def _align_to_template(df, row_ids, class_cols, source_name):
    if "row_id" not in df.columns:
        raise ValueError(f"{source_name}: source submission is missing row_id")
    missing_cols = [c for c in class_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"{source_name}: source submission missing class columns: {missing_cols[:5]}")
    source = df[["row_id"] + class_cols].copy()
    source["row_id"] = source["row_id"].astype(str).str.strip()
    source = source.drop_duplicates(subset=["row_id"]).set_index("row_id")
    template_index = pd.Index(row_ids)
    missing_rows = int((~template_index.isin(source.index)).sum())
    print(f"{source_name}: missing row_ids vs sample = {missing_rows}")
    if missing_rows:
        raise ValueError(
            f"{source_name}: source predictions do not cover submission template "
            f"({missing_rows} missing row_ids). Blending cached notebook outputs is unsafe for this run."
        )
    aligned = source.reindex(row_ids)
    if aligned.isna().any().any():
        raise ValueError(f"{source_name}: NaNs found after alignment")
    return aligned


raunak_path = _find_submission(RAUNAK_TOKENS)
meenal_path = _find_submission(MEENAL_TOKENS)
sample_path = _find_sample_submission()
print("Using Raunak submission:", raunak_path)
print("Using Meenal submission:", meenal_path)
print("Using sample template:", sample_path)

raunak = pd.read_csv(raunak_path)
meenal = pd.read_csv(meenal_path)
sample = pd.read_csv(sample_path)
if "row_id" not in sample.columns:
    raise ValueError("sample_submission.csv missing row_id")
sample["row_id"] = sample["row_id"].astype(str).str.strip()
class_cols = [c for c in sample.columns if c != "row_id"]
row_ids = sample["row_id"].tolist()
print("Template row count from sample:", len(row_ids))
print("Template class count from sample:", len(class_cols))
if len(row_ids) < MIN_EXPECTED_ROWS:
    raise RuntimeError(
        f"Template row count too small ({len(row_ids)}). "
        "This looks like a non-scoring debug environment; refusing to generate a competition submission."
    )

raunak_aligned = _align_to_template(raunak, row_ids, class_cols, "Raunak")
meenal_aligned = _align_to_template(meenal, row_ids, class_cols, "Meenal")

pred_cols = {}
for c in class_cols:
    r = raunak_aligned[c].copy()
    m = meenal_aligned[c].copy()
    if r.isna().any() or m.isna().any():
        raise ValueError(f"NaNs for class={c}; refusing unsafe fallback")
    rank_raunak = r.rank(method="average", pct=True)
    rank_meenal = m.rank(method="average", pct=True)
    pred_cols[c] = 0.5 * rank_raunak + 0.5 * rank_meenal

merged = pd.DataFrame(pred_cols, index=raunak_aligned.index).reset_index().rename(columns={"index": "row_id"})
merged = merged[["row_id"] + class_cols]
if merged[class_cols].isna().any().any():
    raise ValueError("Blend produced NaNs; aborting submission generation")
merged.to_csv(OUT_PATH, index=False, float_format="%.10f")
print(merged.shape)
print(f"Wrote {OUT_PATH}")
"""


def notebook_json() -> dict:
    return {
        "cells": [
            {
                "cell_type": "code",
                "id": "blend-cell-v1",
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
