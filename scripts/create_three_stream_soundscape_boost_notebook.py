#!/usr/bin/env python3
"""Create a three-stream blend notebook with explicit soundscape-only class boosting."""

from __future__ import annotations

import json
from pathlib import Path


OUTPUT_DIR = Path("experiments/kaggle_submission/three-stream-soundscape-boost-v1")

SOUNDSCAPE_ONLY_CLASSES = [
    "1491113",
    "25073",
    "47158son01",
    "47158son02",
    "47158son03",
    "47158son04",
    "47158son05",
    "47158son06",
    "47158son07",
    "47158son08",
    "47158son09",
    "47158son10",
    "47158son11",
    "47158son12",
    "47158son13",
    "47158son14",
    "47158son15",
    "47158son16",
    "47158son17",
    "47158son18",
    "47158son19",
    "47158son20",
    "47158son21",
    "47158son22",
    "47158son23",
    "47158son24",
    "47158son25",
    "517063",
]


def notebook_source() -> str:
    classes_literal = ", ".join([f'"{c}"' for c in SOUNDSCAPE_ONLY_CLASSES])
    return f"""import glob
import pandas as pd

OUT_PATH = "submission.csv"
RAUNAK_TOKENS = ["aleixlopez", "birdclef-2026-ported-raunak-v6-v1"]
MEENAL_TOKENS = ["aleixlopez", "birdclef-2026-meenal-v1"]
EOS6_TOKENS = ["aleixlopez", "birdclef-2026-ported-eos6-v1"]
WEIGHTS = {{
    "raunak": 0.40,
    "meenal": 0.40,
    "eos6": 0.20,
}}
SOUNDSCAPE_ONLY_CLASSES = {{{classes_literal}}}
SOUNDSCAPE_BOOST_FACTOR = 1.08


def _find_submission(required_tokens):
    candidates = glob.glob("/kaggle/input/notebooks/**/submission.csv", recursive=True)
    matches = []
    for path in candidates:
        normalized = path.lower().replace("\\\\", "/")
        if all(token in normalized for token in required_tokens):
            matches.append(path)
    if not matches:
        raise FileNotFoundError(f"Could not find submission.csv matching tokens={{required_tokens}}")
    return sorted(matches)[-1]


def _find_sample_submission():
    candidates = glob.glob("/kaggle/input/**/sample_submission.csv", recursive=True)
    if not candidates:
        raise FileNotFoundError("sample_submission.csv not found under /kaggle/input")
    return sorted(candidates)[0]


def _align_to_template(df, row_ids, class_cols, source_name):
    if "row_id" not in df.columns:
        raise ValueError(f"{{source_name}}: source submission is missing row_id")
    missing_cols = [c for c in class_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"{{source_name}}: source submission missing class columns: {{missing_cols[:5]}}")
    source = df[["row_id"] + class_cols].copy()
    source["row_id"] = source["row_id"].astype(str).str.strip()
    source = source.drop_duplicates(subset=["row_id"]).set_index("row_id")
    template_index = pd.Index(row_ids)
    missing_rows = int((~template_index.isin(source.index)).sum())
    if missing_rows:
        raise ValueError(
            f"{{source_name}}: {{missing_rows}} row_id values from sample_submission are missing in source submission"
        )
    aligned = source.reindex(row_ids)
    if aligned.isna().any().any():
        raise ValueError(f"{{source_name}}: NaNs found after row_id alignment; refusing to generate unsafe blend")
    return aligned


raunak_path = _find_submission(RAUNAK_TOKENS)
meenal_path = _find_submission(MEENAL_TOKENS)
eos6_path = _find_submission(EOS6_TOKENS)
sample_path = _find_sample_submission()
print("Using Raunak submission:", raunak_path)
print("Using Meenal submission:", meenal_path)
print("Using EoS6 submission:", eos6_path)
print("Using sample submission template:", sample_path)

raunak = pd.read_csv(raunak_path)
meenal = pd.read_csv(meenal_path)
eos6 = pd.read_csv(eos6_path)
sample = pd.read_csv(sample_path)

if "row_id" not in sample.columns:
    raise ValueError("sample_submission.csv missing row_id")
sample["row_id"] = sample["row_id"].astype(str).str.strip()
class_cols = [c for c in sample.columns if c != "row_id"]
row_ids = sample["row_id"].tolist()

raunak_aligned = _align_to_template(raunak, row_ids, class_cols, "Raunak")
meenal_aligned = _align_to_template(meenal, row_ids, class_cols, "Meenal")
eos6_aligned = _align_to_template(eos6, row_ids, class_cols, "EoS6")

merged = sample[["row_id"]].copy()
for c in class_cols:
    rank_raunak = raunak_aligned[c].rank(method="average", pct=True)
    rank_meenal = meenal_aligned[c].rank(method="average", pct=True)
    rank_eos6 = eos6_aligned[c].rank(method="average", pct=True)
    merged[c] = (
        WEIGHTS["raunak"] * rank_raunak
        + WEIGHTS["meenal"] * rank_meenal
        + WEIGHTS["eos6"] * rank_eos6
    )

for c in SOUNDSCAPE_ONLY_CLASSES:
    if c in merged.columns:
        merged[c] = (merged[c] * SOUNDSCAPE_BOOST_FACTOR).clip(0.0, 1.0)

merged = merged[["row_id"] + class_cols]
if merged[class_cols].isna().any().any():
    raise ValueError("Blend produced NaNs; aborting submission generation")
merged.to_csv(OUT_PATH, index=False, float_format="%.10f")
print(merged.shape)
print(f"Wrote {{OUT_PATH}}")
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
        "id": "aleixlopez/birdclef-2026-three-stream-soundscape-boost-v1",
        "title": "BirdCLEF 2026 Three Stream Soundscape Boost V1",
        "code_file": "three_stream_soundscape_boost_v1.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": False,
        "enable_internet": False,
        "competition_sources": ["birdclef-2026"],
        "kernel_sources": [
            "aleixlopez/birdclef-2026-ported-raunak-v6-v1",
            "aleixlopez/birdclef-2026-meenal-v1",
            "aleixlopez/birdclef-2026-ported-eos6-v1",
        ],
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "three_stream_soundscape_boost_v1.ipynb").write_text(
        json.dumps(notebook_json(), indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "kernel-metadata.json").write_text(
        json.dumps(metadata_json(), indent=2), encoding="utf-8"
    )
    print(f"Wrote Kaggle package at: {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
