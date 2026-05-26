#!/usr/bin/env python3
"""Create per-class threshold tuning notebook variants from Raunak V6 base."""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path("experiments/kaggle_submission/ported-raunak-v6-v1")
OUTPUT_ROOT = Path("experiments/kaggle_submission/raunak-v6-per-class-tuning-v1")
BASE_NOTEBOOK = BASE_DIR / "ported_raunak_v6_v1.ipynb"
BASE_METADATA = BASE_DIR / "kernel-metadata.json"
PER_CLASS_CONFIGS = Path("experiments/configs/fusion/sweeps/per-class-v1")


@dataclass(frozen=True)
class Variant:
    slug: str
    title_suffix: str
    config_variant: str  # Which per-class-v1 variant to use


VARIANTS = [
    Variant(
        slug="conservative",
        title_suffix="Per-Class Conservative",
        config_variant="conservative",
    ),
    Variant(
        slug="balanced",
        title_suffix="Per-Class Balanced",
        config_variant="balanced",
    ),
    Variant(
        slug="aggressive",
        title_suffix="Per-Class Aggressive",
        config_variant="aggressive",
    ),
]


def _insert_per_class_threshold_loading(notebook_source: str, variant: Variant) -> str:
    """Insert per-class threshold loading and application logic."""
    # Add import and loading code after the main ensemble cell
    per_class_csv_path = f"../configs/fusion/sweeps/per-class-v1/{variant.config_variant}/per_class_thresholds.csv"

    threshold_code = f'''
# Per-class threshold tuning ({variant.config_variant})
import pandas as pd
import numpy as np

# Load per-class thresholds
per_class_csv = "{per_class_csv_path}"
try:
    per_class_df = pd.read_csv(per_class_csv)
    per_class_thresholds = dict(zip(per_class_df['class_id'], per_class_df['threshold']))
    print(f"Loaded {{len(per_class_thresholds)}} per-class thresholds from {{per_class_csv}}")
except Exception as e:
    print(f"Warning: Could not load per-class thresholds: {{e}}")
    per_class_thresholds = {{}}

# Apply per-class thresholds to submission
if per_class_thresholds and 'submission' in locals():
    submission_copy = submission.copy()
    for class_id, threshold in per_class_thresholds.items():
        if class_id in submission_copy.columns:
            submission_copy[class_id] = (submission_copy[class_id] > threshold).astype(int)
    print(f"Applied per-class thresholds. Result shape: {{submission_copy.shape}}")
    submission = submission_copy
'''
    return notebook_source + "\n" + threshold_code


def build_variant_notebook(base_notebook: dict, variant: Variant) -> dict:
    """Build variant notebook by adding per-class threshold logic."""
    notebook = copy.deepcopy(base_notebook)
    
    # Insert the per-class threshold loading code at the end
    # Find the last code cell and append logic after it
    last_code_cell_idx = -1
    for i, cell in enumerate(notebook.get("cells", [])):
        if cell.get("cell_type") == "code":
            last_code_cell_idx = i
    
    if last_code_cell_idx >= 0:
        # Add a new code cell with per-class threshold loading
        new_cell = {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": _insert_per_class_threshold_loading("", variant).split("\n"),
        }
        notebook["cells"].insert(last_code_cell_idx + 1, new_cell)
    
    return notebook


def build_variant_metadata(base_metadata: dict, variant: Variant, code_file: str) -> dict:
    """Build variant metadata."""
    metadata = copy.deepcopy(base_metadata)
    metadata["id"] = f"aleixlopez/birdclef-2026-raunak-v6-per-class-{variant.slug}"
    metadata["title"] = f"BirdCLEF 2026 Raunak V6 {variant.title_suffix}"
    metadata["code_file"] = code_file
    return metadata


def main() -> int:
    """Generate per-class threshold sweep variants."""
    base_notebook = json.loads(BASE_NOTEBOOK.read_text(encoding="utf-8"))
    base_metadata = json.loads(BASE_METADATA.read_text(encoding="utf-8"))

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    summary = []

    for variant in VARIANTS:
        variant_dir = OUTPUT_ROOT / variant.slug
        variant_dir.mkdir(parents=True, exist_ok=True)

        code_file = f"raunak_v6_per_class_{variant.slug}.ipynb"
        notebook = build_variant_notebook(base_notebook, variant)
        metadata = build_variant_metadata(base_metadata, variant, code_file)

        (variant_dir / code_file).write_text(
            json.dumps(notebook, indent=2), encoding="utf-8"
        )
        (variant_dir / "kernel-metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )

        summary.append(
            {
                "variant": variant.slug,
                "kaggle_id": metadata["id"],
                "path": str(variant_dir),
                "config_variant": variant.config_variant,
                "title": variant.title_suffix,
            }
        )

    (OUTPUT_ROOT / "variants_manifest.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"✓ Wrote {len(summary)} per-class threshold variants under {OUTPUT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
