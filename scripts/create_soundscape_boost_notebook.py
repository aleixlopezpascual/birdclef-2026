#!/usr/bin/env python3
"""Create soundscape-only boost variant with multiplier and optimized thresholds."""

from __future__ import annotations

import copy
import csv
import json
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path("experiments/kaggle_submission/ported-raunak-v6-v1")
OUTPUT_DIR = Path("experiments/kaggle_submission/raunak-v6-soundscape-boost-v2")
BASE_NOTEBOOK = BASE_DIR / "ported_raunak_v6_v1.ipynb"
BASE_METADATA = BASE_DIR / "kernel-metadata.json"
SOUNDSCAPE_ONLY_FILE = Path("experiments/configs/fusion/class_groups/soundscape_only_classes.txt")


@dataclass(frozen=True)
class SoundscapeVariant:
    slug: str
    title_suffix: str
    multiplier: float
    threshold: float


VARIANT = SoundscapeVariant(
    slug="v2",
    title_suffix="Soundscape-Only Boost",
    multiplier=1.08,
    threshold=0.28,
)


def _read_soundscape_only_species() -> set[str]:
    """Read soundscape-only species from file."""
    species = set()
    if SOUNDSCAPE_ONLY_FILE.exists():
        for line in SOUNDSCAPE_ONLY_FILE.read_text(encoding="utf-8").splitlines():
            item = line.strip()
            if item and not item.startswith("#"):
                species.add(item)
    return species


def _insert_soundscape_boost_logic(variant: SoundscapeVariant) -> str:
    """Insert soundscape-only species boost logic."""
    code = f'''
# Soundscape-only species boost
import pandas as pd
import numpy as np

# Read soundscape-only species list
SOUNDSCAPE_ONLY_SPECIES = {{
'''
    
    # Add soundscape species list
    species = _read_soundscape_only_species()
    for s in sorted(species):
        code += f"    '{s}',\n"
    
    code += f'''}}

print(f"Loaded {{len(SOUNDSCAPE_ONLY_SPECIES)}} soundscape-only species")

# Apply soundscape-only boost
if 'submission' in locals():
    submission_copy = submission.copy()
    
    for col in submission_copy.columns:
        if col != 'row_id' and col in SOUNDSCAPE_ONLY_SPECIES:
            # Apply multiplier to soundscape-only predictions
            submission_copy[col] = submission_copy[col] * {variant.multiplier:.2f}
            submission_copy[col] = submission_copy[col].clip(0, 1)  # Ensure valid probability
    
    # Apply threshold for soundscape species
    for col in submission_copy.columns:
        if col != 'row_id' and col in SOUNDSCAPE_ONLY_SPECIES:
            submission_copy[col] = (submission_copy[col] > {variant.threshold:.4f}).astype(int)
    
    submission = submission_copy
    print(f"Applied soundscape-only boost: {{len(SOUNDSCAPE_ONLY_SPECIES)}} species with multiplier {variant.multiplier:.2f}")
'''
    return code


def build_variant_notebook(base_notebook: dict, variant: SoundscapeVariant) -> dict:
    """Build soundscape boost notebook."""
    notebook = copy.deepcopy(base_notebook)
    
    # Add soundscape boost cell at the end
    new_cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": _insert_soundscape_boost_logic(variant).split("\n"),
    }
    notebook["cells"].append(new_cell)
    
    return notebook


def build_variant_metadata(base_metadata: dict, variant: SoundscapeVariant, code_file: str) -> dict:
    """Build variant metadata."""
    metadata = copy.deepcopy(base_metadata)
    metadata["id"] = f"aleixlopez/birdclef-2026-raunak-v6-soundscape-boost-{variant.slug}"
    metadata["title"] = f"BirdCLEF 2026 Raunak V6 {variant.title_suffix}"
    metadata["code_file"] = code_file
    return metadata


def main() -> int:
    """Generate soundscape-only boost variant."""
    base_notebook = json.loads(BASE_NOTEBOOK.read_text(encoding="utf-8"))
    base_metadata = json.loads(BASE_METADATA.read_text(encoding="utf-8"))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    code_file = f"raunak_v6_soundscape_boost_{VARIANT.slug}.ipynb"
    notebook = build_variant_notebook(base_notebook, VARIANT)
    metadata = build_variant_metadata(base_metadata, VARIANT, code_file)

    (OUTPUT_DIR / code_file).write_text(json.dumps(notebook, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    # Save species list for reference
    species = _read_soundscape_only_species()
    (OUTPUT_DIR / "soundscape_only_species.txt").write_text(
        "\n".join(sorted(species)), encoding="utf-8"
    )

    manifest = {
        "variant": VARIANT.slug,
        "kaggle_id": metadata["id"],
        "path": str(OUTPUT_DIR),
        "multiplier": VARIANT.multiplier,
        "threshold": VARIANT.threshold,
        "species_count": len(species),
        "title": VARIANT.title_suffix,
    }
    (OUTPUT_DIR / "variant_info.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"✓ Soundscape-only boost variant created at {OUTPUT_DIR}")
    print(f"  - Multiplier: {VARIANT.multiplier:.2f}")
    print(f"  - Threshold: {VARIANT.threshold:.4f}")
    print(f"  - Species targeted: {len(species)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
