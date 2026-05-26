#!/usr/bin/env python3
"""Generate per-class threshold CSV from taxonomy and species class groups."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


TAXONOMY_CSV = Path("data/competition/raw/taxonomy.csv")
SOUNDSCAPE_ONLY_FILE = Path("experiments/configs/fusion/class_groups/soundscape_only_classes.txt")
FEW_SHOT_FILE = Path("experiments/configs/fusion/class_groups/few_shot_classes.txt")
OUTPUT_ROOT = Path("experiments/configs/fusion/sweeps/per-class-v1")


@dataclass(frozen=True)
class ThresholdVariant:
    """Threshold configuration for a sweep variant."""

    slug: str
    variant_name: str
    standard_threshold: float
    bird_threshold: float
    few_shot_threshold: float
    soundscape_only_threshold: float
    non_bird_threshold: float


VARIANTS = [
    ThresholdVariant(
        slug="conservative",
        variant_name="Conservative (prioritize precision)",
        standard_threshold=0.50,
        bird_threshold=0.50,
        few_shot_threshold=0.45,
        soundscape_only_threshold=0.35,
        non_bird_threshold=0.55,
    ),
    ThresholdVariant(
        slug="balanced",
        variant_name="Balanced (precision-recall balance)",
        standard_threshold=0.49,
        bird_threshold=0.48,
        few_shot_threshold=0.40,
        soundscape_only_threshold=0.28,
        non_bird_threshold=0.52,
    ),
    ThresholdVariant(
        slug="aggressive",
        variant_name="Aggressive (prioritize recall)",
        standard_threshold=0.48,
        bird_threshold=0.46,
        few_shot_threshold=0.35,
        soundscape_only_threshold=0.24,
        non_bird_threshold=0.50,
    ),
]


def _read_class_list(path: Path) -> set[str]:
    """Read class identifiers from a plain-text file (one per line)."""
    rows: set[str] = set()
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        item = line.strip()
        if item and not item.startswith("#"):
            rows.add(item)
    return rows


def _read_taxonomy(path: Path) -> list[dict]:
    """Read taxonomy CSV and return list of species records."""
    records: list[dict] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("primary_label", "").strip():
                records.append(row)
    return records


def _classify_species(
    label: str,
    taxonomy: list[dict],
    soundscape_only: set[str],
    few_shot: set[str],
) -> tuple[str, str]:
    """Classify a species by label.

    Returns: (group: str, class_name: str)
    - group: 'soundscape_only', 'few_shot', 'bird', 'non_bird', or 'standard'
    - class_name: from taxonomy (e.g. 'Aves', 'Insecta', 'Reptilia')
    """
    # Find the species in taxonomy to get class_name
    class_name = "unknown"
    for record in taxonomy:
        if record.get("primary_label") == label:
            class_name = record.get("class_name", "unknown").strip()
            break

    if label in soundscape_only:
        return "soundscape_only", class_name
    if label in few_shot:
        return "few_shot", class_name
    if class_name == "Aves":
        return "bird", class_name
    return "non_bird", class_name


def _threshold_for_group(group: str, variant: ThresholdVariant) -> float:
    """Get threshold for a species group."""
    if group == "soundscape_only":
        return variant.soundscape_only_threshold
    if group == "few_shot":
        return variant.few_shot_threshold
    if group == "bird":
        return variant.bird_threshold
    if group == "non_bird":
        return variant.non_bird_threshold
    return variant.standard_threshold


def main() -> int:
    """Generate per-class threshold configs for all variants."""
    taxonomy = _read_taxonomy(TAXONOMY_CSV)
    soundscape_only = _read_class_list(SOUNDSCAPE_ONLY_FILE)
    few_shot = _read_class_list(FEW_SHOT_FILE)

    print(f"Loaded taxonomy: {len(taxonomy)} species")
    print(f"Soundscape-only: {len(soundscape_only)} species")
    print(f"Few-shot: {len(few_shot)} species")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []

    for variant in VARIANTS:
        variant_dir = OUTPUT_ROOT / variant.slug
        variant_dir.mkdir(parents=True, exist_ok=True)

        # Generate per-class thresholds
        rows: list[tuple[str, float, str, str]] = []
        group_counts = {"soundscape_only": 0, "few_shot": 0, "bird": 0, "non_bird": 0, "standard": 0}

        for record in taxonomy:
            label = record.get("primary_label", "").strip()
            if not label:
                continue

            group, class_name = _classify_species(label, taxonomy, soundscape_only, few_shot)
            threshold = _threshold_for_group(group, variant)
            group_counts[group] = group_counts.get(group, 0) + 1
            rows.append((label, threshold, group, class_name))

        # Write per-class thresholds CSV
        per_class_path = variant_dir / "per_class_thresholds.csv"
        with per_class_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["class_id", "threshold", "group", "taxonomy_class"])
            for label, threshold, group, class_name in rows:
                writer.writerow([label, f"{threshold:.4f}", group, class_name])

        # Write manifest entry
        manifest.append(
            {
                "variant_slug": variant.slug,
                "variant_name": variant.variant_name,
                "path": str(variant_dir),
                "thresholds": {
                    "standard": variant.standard_threshold,
                    "bird": variant.bird_threshold,
                    "few_shot": variant.few_shot_threshold,
                    "soundscape_only": variant.soundscape_only_threshold,
                    "non_bird": variant.non_bird_threshold,
                },
                "group_counts": group_counts,
                "total_classes": len(rows),
            }
        )

        print(f"\n✓ {variant.slug}: {group_counts}")

    # Write manifest
    manifest_path = OUTPUT_ROOT / "variants_manifest.json"
    import json

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\n✓ Generated {len(manifest)} variants under {OUTPUT_ROOT}")
    print(f"✓ Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
