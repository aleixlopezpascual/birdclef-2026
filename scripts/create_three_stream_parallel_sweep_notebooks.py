#!/usr/bin/env python3
"""Create a parallel-ready sweep of three-stream blend Kaggle notebook packages."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path


OUTPUT_ROOT = Path("experiments/kaggle_submission/three-stream-parallel-sweep-v1")
TAXONOMY_CSV = Path("data/competition/raw/taxonomy.csv")
SOUNDSCAPE_ONLY_FILE = Path("experiments/configs/fusion/class_groups/soundscape_only_classes.txt")

CLASS_FACTORS = {
    "Amphibia": 1.08,
    "Insecta": 1.10,
    "Mammalia": 1.06,
    "Reptilia": 1.20,
}


@dataclass(frozen=True)
class Variant:
    slug: str
    title_suffix: str
    w_raunak: float
    w_meenal: float
    w_eos6: float
    soundscape_boost: float
    use_non_bird_factors: bool


VARIANTS = [
    Variant(
        slug="baseline",
        title_suffix="Baseline",
        w_raunak=0.40,
        w_meenal=0.40,
        w_eos6=0.20,
        soundscape_boost=1.0,
        use_non_bird_factors=False,
    ),
    Variant(
        slug="soundscape-boost",
        title_suffix="Soundscape Boost",
        w_raunak=0.40,
        w_meenal=0.40,
        w_eos6=0.20,
        soundscape_boost=1.08,
        use_non_bird_factors=False,
    ),
    Variant(
        slug="non-bird-specialized",
        title_suffix="Non Bird Specialized",
        w_raunak=0.40,
        w_meenal=0.40,
        w_eos6=0.20,
        soundscape_boost=1.0,
        use_non_bird_factors=True,
    ),
    Variant(
        slug="combo-boost",
        title_suffix="Combo Boost",
        w_raunak=0.40,
        w_meenal=0.40,
        w_eos6=0.20,
        soundscape_boost=1.08,
        use_non_bird_factors=True,
    ),
    Variant(
        slug="eos-heavy-combo",
        title_suffix="EoS Heavy Combo",
        w_raunak=0.35,
        w_meenal=0.35,
        w_eos6=0.30,
        soundscape_boost=1.08,
        use_non_bird_factors=True,
    ),
]


def _read_class_list(path: Path) -> list[str]:
    out: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        item = line.strip()
        if item and not item.startswith("#"):
            out.append(item)
    return out


def _build_non_bird_factor_map() -> dict[str, float]:
    out: dict[str, float] = {}
    with TAXONOMY_CSV.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = row.get("primary_label", "").strip()
            class_name = row.get("class_name", "").strip()
            if not label:
                continue
            if class_name in CLASS_FACTORS:
                out[label] = CLASS_FACTORS[class_name]
    return out


def notebook_source(
    *,
    variant: Variant,
    soundscape_only_classes: list[str],
    non_bird_factor_map: dict[str, float],
) -> str:
    soundscape_literal = ", ".join([f'"{c}"' for c in sorted(soundscape_only_classes)])
    non_bird_literal = ",\n    ".join(
        [f'"{class_id}": {factor:.2f}' for class_id, factor in sorted(non_bird_factor_map.items())]
    )
    return f"""import glob
import pandas as pd

OUT_PATH = "submission.csv"
RAUNAK_TOKENS = ["aleixlopez", "birdclef-2026-ported-raunak-v6-v1"]
MEENAL_TOKENS = ["aleixlopez", "birdclef-2026-meenal-v1"]
EOS6_TOKENS = ["aleixlopez", "birdclef-2026-ported-eos6-v1"]
WEIGHTS = {{
    "raunak": {variant.w_raunak:.2f},
    "meenal": {variant.w_meenal:.2f},
    "eos6": {variant.w_eos6:.2f},
}}
SOUNDSCAPE_ONLY_CLASSES = {{{soundscape_literal}}}
SOUNDSCAPE_BOOST_FACTOR = {variant.soundscape_boost:.2f}
USE_NON_BIRD_FACTORS = {str(variant.use_non_bird_factors)}
NON_BIRD_FACTOR_MAP = {{
    {non_bird_literal}
}}


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

if SOUNDSCAPE_BOOST_FACTOR > 1.0:
    for c in SOUNDSCAPE_ONLY_CLASSES:
        if c in merged.columns:
            merged[c] = (merged[c] * SOUNDSCAPE_BOOST_FACTOR).clip(0.0, 1.0)

if USE_NON_BIRD_FACTORS:
    for c, factor in NON_BIRD_FACTOR_MAP.items():
        if c in merged.columns:
            merged[c] = (merged[c] * factor).clip(0.0, 1.0)

merged = merged[["row_id"] + class_cols]
if merged[class_cols].isna().any().any():
    raise ValueError("Blend produced NaNs; aborting submission generation")
merged.to_csv(OUT_PATH, index=False, float_format="%.10f")
print(merged.shape)
print(f"Wrote {{OUT_PATH}}")
"""


def notebook_json(*, source: str) -> dict:
    return {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [line + "\n" for line in source.splitlines()],
            }
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def metadata_json(variant: Variant, code_file: str) -> dict:
    return {
        "id": f"aleixlopez/birdclef-2026-three-stream-parallel-{variant.slug}-v1",
        "title": f"BirdCLEF 2026 Three Stream Parallel {variant.title_suffix} V1",
        "code_file": code_file,
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
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    soundscape_only = _read_class_list(SOUNDSCAPE_ONLY_FILE)
    non_bird_map = _build_non_bird_factor_map()
    manifest: list[dict[str, object]] = []

    for variant in VARIANTS:
        variant_dir = OUTPUT_ROOT / variant.slug
        variant_dir.mkdir(parents=True, exist_ok=True)
        code_file = f"three_stream_parallel_{variant.slug.replace('-', '_')}_v1.ipynb"
        effective_non_bird_map = non_bird_map if variant.use_non_bird_factors else {}
        source = notebook_source(
            variant=variant,
            soundscape_only_classes=soundscape_only,
            non_bird_factor_map=effective_non_bird_map,
        )

        (variant_dir / code_file).write_text(
            json.dumps(notebook_json(source=source), indent=2), encoding="utf-8"
        )
        metadata = metadata_json(variant, code_file=code_file)
        (variant_dir / "kernel-metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )

        manifest.append(
            {
                "variant": variant.slug,
                "kaggle_id": metadata["id"],
                "path": str(variant_dir),
                "weights": {
                    "raunak": variant.w_raunak,
                    "meenal": variant.w_meenal,
                    "eos6": variant.w_eos6,
                },
                "soundscape_boost": variant.soundscape_boost,
                "use_non_bird_factors": variant.use_non_bird_factors,
            }
        )

    (OUTPUT_ROOT / "variants_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"Wrote {len(manifest)} variants under {OUTPUT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
