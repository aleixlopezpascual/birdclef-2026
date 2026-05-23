#!/usr/bin/env python3
"""Analyze downloaded Kaggle notebooks and generate a strategy report."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class NotebookSignals:
    ref: str
    title: str
    votes: int
    buckets: str
    flags: Dict[str, bool]
    imports: List[str]


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def extract_code(notebook_path: Path) -> str:
    data = json.loads(notebook_path.read_text(encoding="utf-8", errors="ignore"))
    chunks: List[str] = []
    for cell in data.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", "")
        chunks.append("".join(source) if isinstance(source, list) else str(source))
    return "\n".join(chunks)


def extract_imports(code: str) -> List[str]:
    modules = set()
    for mod in re.findall(r"^\s*import\s+([a-zA-Z0-9_\.]+)", code, flags=re.MULTILINE):
        modules.add(mod.split(".")[0])
    for mod in re.findall(r"^\s*from\s+([a-zA-Z0-9_\.]+)\s+import\s+", code, flags=re.MULTILINE):
        modules.add(mod.split(".")[0])
    return sorted(modules)


def main() -> int:
    root = Path("data/external/kaggle-notebooks")
    notebooks_root = root / "notebooks"
    metadata_root = root / "metadata"
    combined = read_csv(metadata_root / "combined_index.csv")
    top_votes = read_csv(metadata_root / "top_votes.csv")
    top_score = read_csv(metadata_root / "top_score.csv")

    patterns = {
        "Perch family": r"\bperch\b",
        "SSM family": r"protossm|resssm|\bssm\b",
        "ONNX inference": r"onnxruntime|InferenceSession|\.onnx",
        "TFLite inference": r"tflite_runtime|interpreter",
        "Ensembling/fusion": r"ensemble|blend|fusion|rank[_\s-]*power|gated|gate",
        "Threshold tuning": r"threshold|thr_|optimize.*threshold",
        "Test-time augmentation": r"\btta\b|test[-\s]*time",
        "Pseudo-labeling": r"\bpseudo\b",
        "Calibration/scaling": r"temperature|calibrat|logit",
        "Two-pass pipeline": r"two[-\s]*pass|stage[-\s]*2|second pass",
        "Safe align heuristic": r"safealign|safe_align",
    }

    signals: List[NotebookSignals] = []
    flag_counts: Counter[str] = Counter()
    import_counts: Counter[str] = Counter()

    by_ref = {row["ref"]: row for row in combined}
    for ref, row in by_ref.items():
        nb_dir = notebooks_root / ref.replace("/", "_")
        ipynb_files = list(nb_dir.glob("*.ipynb"))
        if not ipynb_files:
            continue
        code = extract_code(ipynb_files[0])
        flags = {name: bool(re.search(rx, code, flags=re.IGNORECASE)) for name, rx in patterns.items()}
        for name, present in flags.items():
            if present:
                flag_counts[name] += 1
        imports = extract_imports(code)
        for mod in imports:
            import_counts[mod] += 1
        signals.append(
            NotebookSignals(
                ref=ref,
                title=row.get("title", ""),
                votes=int(row.get("votes", "0") or "0"),
                buckets=row.get("buckets", ""),
                flags=flags,
                imports=imports,
            )
        )

    total = len(signals)
    top_modules = import_counts.most_common(20)
    top_patterns = [(k, v, round(v * 100.0 / total, 1) if total else 0.0) for k, v in flag_counts.most_common()]

    deep_dive = {
        "total_notebooks": total,
        "pattern_coverage": [{"pattern": k, "count": c, "pct": p} for k, c, p in top_patterns],
        "top_imports": [{"module": m, "count": c} for m, c in top_modules],
    }
    (metadata_root / "deep_dive.json").write_text(json.dumps(deep_dive, indent=2), encoding="utf-8")

    def table_rows(rows: List[Dict[str, str]], rank_col: str) -> str:
        out = []
        for row in rows[:10]:
            out.append(
                f"| {row.get(rank_col,'')} | `{row.get('ref','')}` | {row.get('votes','')} | {row.get('title','').replace('|','/')} |"
            )
        return "\n".join(out)

    coverage_rows = "\n".join([f"| {k} | {c}/{total} | {p}% |" for k, c, p in top_patterns])
    imports_rows = "\n".join([f"| `{m}` | {c}/{total} |" for m, c in top_modules])

    strategy = """1. Build a strong single-model baseline with Perch-family embeddings + robust 5-second aggregation.
2. Add ONNX/TFLite optimized inference path early to keep runtime margin on CPU notebook limits.
3. Introduce calibrated multi-model fusion (rank-power + weighted blend) as the primary lift stage.
4. Run threshold optimization + post-processing tuning on local CV, then lock conservative defaults for LB stability.
5. Add pseudo-label experiments only after stable CV-LB alignment to avoid reinforcing label noise.
"""

    doc = f"""# BirdCLEF+ 2026 notebook deep dive

Generated from downloaded Kaggle notebooks in `data/external/kaggle-notebooks/`.

## Collection summary

- Requested: top 20 by score + top 20 by votes
- Collected rows: 40
- Unique notebooks downloaded: {total}
- Metadata index: `data/external/kaggle-notebooks/metadata/combined_index.csv`

## Top voted notebooks (sample)

| Vote rank | Ref | Votes | Title |
| --- | --- | --- | --- |
{table_rows(top_votes, "bucket_rank")}

## Top score notebooks (sample)

| Score rank | Ref | Votes | Title |
| --- | --- | --- | --- |
{table_rows(top_score, "bucket_rank")}

## Technique coverage across downloaded notebooks

| Technique signal | Presence | Coverage |
| --- | --- | --- |
{coverage_rows}

## Most common imported modules

| Module | Presence |
| --- | --- |
{imports_rows}

## What high performers are converging on

1. Perch-derived feature backbones plus SSM-style sequence modeling variants are the dominant pattern.
2. ONNX/TFLite inference appears frequently, indicating runtime constraints are a first-class design target.
3. Ensembling (weighted blend, rank-based fusion, gated combinations) is a core source of leaderboard lift.
4. Threshold tuning and post-processing are widely used, suggesting final probability shaping matters substantially.
5. Two-pass and safe-alignment style heuristics appear often enough to treat as important ablation candidates.

## Proposed win-oriented roadmap

{strategy}

## Immediate experiment backlog

1. Reproduce one strong public inference notebook exactly as a hard baseline.
2. Swap in our own validation split and compare CV-vs-LB drift.
3. Build a 3-model ensemble family (Perch variant + SSM variant + lightweight CNN baseline).
4. Tune blend weights/rank-power and per-class/global thresholds on CV.
5. Add controlled pseudo-labeling only for stable high-confidence slices.
"""

    Path("docs/notebook-deep-dive.md").write_text(doc, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
