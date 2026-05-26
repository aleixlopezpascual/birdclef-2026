#!/usr/bin/env python3
"""Create Raunak V6 gate-parameter sweep notebooks."""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path("experiments/kaggle_submission/ported-raunak-v6-v1")
OUTPUT_ROOT = Path("experiments/kaggle_submission/raunak-v6-gate-sweep-v1")
BASE_NOTEBOOK = BASE_DIR / "ported_raunak_v6_v1.ipynb"
BASE_METADATA = BASE_DIR / "kernel-metadata.json"


@dataclass(frozen=True)
class Variant:
    slug: str
    title_suffix: str
    fake_blend: float
    temporal_radius: int


VARIANTS = [
    Variant(
        slug=f"fb{int(fake_blend * 1000):03d}-r{radius}",
        title_suffix=f"Gate FB{int(fake_blend * 1000):03d} R{radius}",
        fake_blend=fake_blend,
        temporal_radius=radius,
    )
    for fake_blend in (0.06, 0.08, 0.10)
    for radius in (2, 3, 4)
]


def _replace_tunable_constants(src: str, variant: Variant) -> str:
    kernel_width = (2 * variant.temporal_radius) + 1
    out = src
    out = re.sub(
        r"pred = np\.where\(fake_only, \(1\.0 - 0\.08\) \* pred \+ 0\.08 \* rank_proto, pred\)",
        (
            "pred = np.where(fake_only, "
            f"(1.0 - {variant.fake_blend:.2f}) * pred + {variant.fake_blend:.2f} * rank_proto, pred)"
        ),
        out,
    )
    out = re.sub(
        r"offs = np\.arange\(-3, 4, dtype=np\.float32\)",
        f"offs = np.arange(-{variant.temporal_radius}, {variant.temporal_radius + 1}, dtype=np.float32)",
        out,
    )
    out = re.sub(
        r"xp = np\.pad\(x, \(\(3, 3\), \(0, 0\)\), mode=\"edge\"\)",
        f"xp = np.pad(x, (({variant.temporal_radius}, {variant.temporal_radius}), (0, 0)), mode=\"edge\")",
        out,
    )
    out = re.sub(
        r"pa_ctx\[m\] = sum\(proto_kernel\[i\] \* xp\[i:i \+ len\(x\)\] for i in range\(7\)\)",
        f"pa_ctx[m] = sum(proto_kernel[i] * xp[i:i + len(x)] for i in range({kernel_width}))",
        out,
    )
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
    metadata["id"] = f"aleixlopez/birdclef-2026-raunak-v6-gate-{variant.slug}"
    metadata["title"] = f"BirdCLEF 2026 Raunak V6 Gate {variant.slug.upper()}"
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

        code_file = f"raunak_v6_gate_{variant.slug.replace('-', '_')}.ipynb"
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
                "fake_blend": variant.fake_blend,
                "temporal_radius": variant.temporal_radius,
            }
        )

    (OUTPUT_ROOT / "variants_manifest.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"Wrote {len(summary)} variants under {OUTPUT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
