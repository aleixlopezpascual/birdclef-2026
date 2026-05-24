#!/usr/bin/env python3
"""Build a fusion and threshold optimization plan artifact."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


FUSION_CFG = Path("experiments/configs/fusion/fusion_strategy.json")
THRESHOLD_CFG = Path("experiments/configs/fusion/threshold_strategy.json")
OUTPUT = Path("experiments/fusion/plan.json")


def main() -> int:
    fusion = json.loads(FUSION_CFG.read_text(encoding="utf-8"))
    threshold = json.loads(THRESHOLD_CFG.read_text(encoding="utf-8"))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    artifact = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "fusion_strategy": fusion,
        "threshold_strategy": threshold,
        "ablation_order": [
            "raw_streams",
            "weighted_fusion",
            "rank_power_fusion",
            "temperature_scaling",
            "global_threshold",
            "per_class_overrides",
            "post_processing",
        ],
    }
    OUTPUT.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"Wrote fusion plan: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
