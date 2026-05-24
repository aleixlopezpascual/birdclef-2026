#!/usr/bin/env python3
"""Build a manifest for configured model portfolio streams."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


CONFIG_DIR = Path("experiments/configs/model_portfolio")
OUTPUT_DIR = Path("experiments/portfolio")


def main() -> int:
    stream_files = sorted(
        p
        for p in CONFIG_DIR.glob("*_stream.json")
        if p.is_file()
    )
    if not stream_files:
        raise FileNotFoundError(f"No stream configs found in {CONFIG_DIR}")

    streams = []
    for path in stream_files:
        cfg = json.loads(path.read_text(encoding="utf-8"))
        streams.append(
            {
                "stream_name": cfg.get("stream_name"),
                "family": cfg.get("family"),
                "enabled": bool(cfg.get("enabled", True)),
                "config_path": str(path),
                "output_schema_ref": cfg.get("output_schema_ref"),
            }
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "config_dir": str(CONFIG_DIR),
        "stream_count": len(streams),
        "enabled_stream_count": sum(1 for s in streams if s["enabled"]),
        "streams": streams,
    }
    out = OUTPUT_DIR / "manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote portfolio manifest: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
