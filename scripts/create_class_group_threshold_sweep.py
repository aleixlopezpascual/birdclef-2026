#!/usr/bin/env python3
"""Generate class-group threshold sweep configs from taxonomy and curated class lists."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path


TAXONOMY_CSV = Path("data/competition/raw/taxonomy.csv")
BASE_THRESHOLD_CFG = Path("experiments/configs/fusion/threshold_strategy.json")
SOUNDSCAPE_ONLY_FILE = Path("experiments/configs/fusion/class_groups/soundscape_only_classes.txt")
FEW_SHOT_FILE = Path("experiments/configs/fusion/class_groups/few_shot_classes.txt")
OUTPUT_ROOT = Path("experiments/configs/fusion/sweeps/class-group-v1")


@dataclass(frozen=True)
class Variant:
    slug: str
    global_threshold: float
    standard_threshold: float
    few_shot_threshold: float
    soundscape_only_threshold: float


VARIANTS = [
    Variant(
        slug="balanced",
        global_threshold=0.50,
        standard_threshold=0.50,
        few_shot_threshold=0.40,
        soundscape_only_threshold=0.35,
    ),
    Variant(
        slug="recall-heavy",
        global_threshold=0.48,
        standard_threshold=0.48,
        few_shot_threshold=0.34,
        soundscape_only_threshold=0.30,
    ),
    Variant(
        slug="conservative",
        global_threshold=0.52,
        standard_threshold=0.52,
        few_shot_threshold=0.45,
        soundscape_only_threshold=0.40,
    ),
]


def _read_class_list(path: Path) -> set[str]:
    rows: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        item = line.strip()
        if item and not item.startswith("#"):
            rows.add(item)
    return rows


def _read_taxonomy_labels(path: Path) -> list[str]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if "primary_label" not in (reader.fieldnames or []):
            raise ValueError(f"taxonomy missing required column primary_label: {path}")
        labels = [row["primary_label"].strip() for row in reader if row.get("primary_label", "").strip()]
    if not labels:
        raise ValueError(f"no primary_label values found in taxonomy: {path}")
    return labels


def _group_for_label(label: str, soundscape_only: set[str], few_shot: set[str]) -> str:
    if label in soundscape_only:
        return "soundscape_only"
    if label in few_shot:
        return "few_shot"
    return "standard"


def _threshold_for_group(group: str, variant: Variant) -> float:
    if group == "soundscape_only":
        return variant.soundscape_only_threshold
    if group == "few_shot":
        return variant.few_shot_threshold
    return variant.standard_threshold


def main() -> int:
    labels = _read_taxonomy_labels(TAXONOMY_CSV)
    base_cfg = json.loads(BASE_THRESHOLD_CFG.read_text(encoding="utf-8"))
    soundscape_only = _read_class_list(SOUNDSCAPE_ONLY_FILE)
    few_shot = _read_class_list(FEW_SHOT_FILE)

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []

    for variant in VARIANTS:
        variant_dir = OUTPUT_ROOT / variant.slug
        variant_dir.mkdir(parents=True, exist_ok=True)

        rows: list[tuple[str, float]] = []
        counts = {"soundscape_only": 0, "few_shot": 0, "standard": 0}
        for label in labels:
            group = _group_for_label(label, soundscape_only=soundscape_only, few_shot=few_shot)
            counts[group] += 1
            rows.append((label, _threshold_for_group(group, variant)))

        per_class_path = variant_dir / "per_class_thresholds.csv"
        with per_class_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["class_id", "threshold"])
            for class_id, threshold in rows:
                writer.writerow([class_id, f"{threshold:.4f}"])

        cfg = dict(base_cfg)
        cfg["strategy_name"] = f"class_group_{variant.slug}"
        cfg["global_threshold"] = variant.global_threshold
        cfg["per_class_overrides_path"] = str(per_class_path)
        (variant_dir / "threshold_strategy.json").write_text(
            json.dumps(cfg, indent=2), encoding="utf-8"
        )

        manifest.append(
            {
                "variant": variant.slug,
                "path": str(variant_dir),
                "global_threshold": variant.global_threshold,
                "thresholds": {
                    "standard": variant.standard_threshold,
                    "few_shot": variant.few_shot_threshold,
                    "soundscape_only": variant.soundscape_only_threshold,
                },
                "class_counts": counts,
            }
        )

    (OUTPUT_ROOT / "variants_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"Wrote {len(manifest)} class-group threshold variants under {OUTPUT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
