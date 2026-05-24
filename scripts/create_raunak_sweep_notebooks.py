#!/usr/bin/env python3
"""Create Raunak V6 sweep notebook packages with small calibration/blend variations."""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path("experiments/kaggle_submission/ported-raunak-v6-v1")
OUTPUT_ROOT = Path("experiments/kaggle_submission/raunak-v6-sweep-v1")
BASE_NOTEBOOK = BASE_DIR / "ported_raunak_v6_v1.ipynb"
BASE_METADATA = BASE_DIR / "kernel-metadata.json"


@dataclass(frozen=True)
class Variant:
    slug: str
    title_suffix: str
    texture_temp: float
    aves_temp: float
    file_scale_power: float
    rank_power: float
    smooth_alpha: float
    proto_weight: float
    sed_weight: float


VARIANTS = [
    Variant(
        slug="calib-a",
        title_suffix="Calib A",
        texture_temp=0.90,
        aves_temp=1.05,
        file_scale_power=0.40,
        rank_power=0.45,
        smooth_alpha=0.18,
        proto_weight=0.60,
        sed_weight=0.40,
    ),
    Variant(
        slug="calib-b",
        title_suffix="Calib B",
        texture_temp=1.00,
        aves_temp=1.15,
        file_scale_power=0.35,
        rank_power=0.35,
        smooth_alpha=0.24,
        proto_weight=0.62,
        sed_weight=0.38,
    ),
    Variant(
        slug="calib-c",
        title_suffix="Calib C",
        texture_temp=0.95,
        aves_temp=1.10,
        file_scale_power=0.50,
        rank_power=0.50,
        smooth_alpha=0.20,
        proto_weight=0.58,
        sed_weight=0.42,
    ),
]


def _replace_tunable_constants(src: str, variant: Variant) -> str:
    replacements = [
        (
            r"temperatures\[ci\] = 0\.95 if cls in TEXTURE_TAXA else 1\.10",
            (
                f"temperatures[ci] = {variant.texture_temp:.2f} "
                f"if cls in TEXTURE_TAXA else {variant.aves_temp:.2f}"
            ),
        ),
        (
            r"probs = file_confidence_scale\(probs, n_windows=N_WINDOWS, top_k=2, power=0\.4\)",
            (
                "probs = file_confidence_scale("
                f"probs, n_windows=N_WINDOWS, top_k=2, power={variant.file_scale_power:.2f})"
            ),
        ),
        (
            r"probs = rank_aware_scaling\(probs,\s+n_windows=N_WINDOWS, power=0\.[46]\)",
            (
                "probs = rank_aware_scaling("
                f"probs,    n_windows=N_WINDOWS, power={variant.rank_power:.2f})"
            ),
        ),
        (
            r"probs = adaptive_delta_smooth\(probs, n_windows=N_WINDOWS, base_alpha=0\.20\)",
            (
                "probs = adaptive_delta_smooth("
                f"probs, n_windows=N_WINDOWS, base_alpha={variant.smooth_alpha:.2f})"
            ),
        ),
        (
            r"pred = \(rank_proto \* 0\.595\) \+ \(rank_sed \* 0\.405\)",
            f"pred = (rank_proto * {variant.proto_weight:.3f}) + (rank_sed * {variant.sed_weight:.3f})",
        ),
    ]
    out = src
    for pattern, repl in replacements:
        out = re.sub(pattern, repl, out)
    return out


def build_variant_notebook(base_notebook: dict, variant: Variant) -> dict:
    notebook = copy.deepcopy(base_notebook)
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        updated = _replace_tunable_constants(src, variant)
        cell["source"] = [line + "\n" for line in updated.splitlines()]
    return notebook


def build_variant_metadata(base_metadata: dict, variant: Variant, code_file: str) -> dict:
    metadata = copy.deepcopy(base_metadata)
    metadata["id"] = f"aleixlopez/birdclef-2026-raunak-v6-{variant.slug}"
    metadata["title"] = f"BirdCLEF 2026 Raunak V6 {variant.title_suffix}"
    metadata["code_file"] = code_file
    return metadata


def main() -> int:
    base_notebook = json.loads(BASE_NOTEBOOK.read_text(encoding="utf-8"))
    base_metadata = json.loads(BASE_METADATA.read_text(encoding="utf-8"))

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    summary = []

    for variant in VARIANTS:
        variant_dir = OUTPUT_ROOT / variant.slug
        variant_dir.mkdir(parents=True, exist_ok=True)

        code_file = f"raunak_v6_{variant.slug.replace('-', '_')}.ipynb"
        notebook = build_variant_notebook(base_notebook, variant)
        metadata = build_variant_metadata(base_metadata, variant, code_file)

        (variant_dir / code_file).write_text(json.dumps(notebook, indent=2), encoding="utf-8")
        (variant_dir / "kernel-metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )

        summary.append(
            {
                "variant": variant.slug,
                "kaggle_id": metadata["id"],
                "path": str(variant_dir),
                "texture_temp": variant.texture_temp,
                "aves_temp": variant.aves_temp,
                "file_scale_power": variant.file_scale_power,
                "rank_power": variant.rank_power,
                "smooth_alpha": variant.smooth_alpha,
                "proto_weight": variant.proto_weight,
                "sed_weight": variant.sed_weight,
            }
        )

    (OUTPUT_ROOT / "variants_manifest.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"Wrote {len(summary)} variants under {OUTPUT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
