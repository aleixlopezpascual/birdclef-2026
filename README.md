# birdclef-2026

Documentation and code workspace for the Kaggle **BirdCLEF+ 2026** competition:

- Competition page: https://kaggle.com/competitions/birdclef-2026
- Full competition documentation for this repo: [`docs/competition-overview.md`](docs/competition-overview.md)

## Quick competition summary

BirdCLEF+ 2026 focuses on **acoustic species identification** from continuous field audio recorded in Brazil's Pantanal wetlands. The objective is to predict species presence in short time windows of audio and support biodiversity monitoring at scale.

- **Task type:** Multilabel audio event classification
- **Evaluation:** Macro-averaged ROC-AUC variant that skips classes with no true positives
- **Submission unit:** One prediction row per 5-second window (`row_id` + one column per species)
- **Competition format:** Kaggle code competition (Notebook-based submissions)
- **Dataset:** 46,213 files, 16.14 GB, 234 target species/classes, hidden test soundscapes

For full rules, timelines, code constraints, prizes, and a full dataset/file breakdown, see the detailed document linked above.

## Notebook deep-dive collection

To collect top public Kaggle notebooks for this competition (top score + top votes), run:

```bash
uv sync
uv run python scripts/collect_kaggle_notebooks.py \
  --competition birdclef-2026 \
  --top-n 20 \
  --output-dir data/external/kaggle-notebooks
```

Outputs are stored under:

- `data/external/kaggle-notebooks/notebooks/` (downloaded notebook sources)
- `data/external/kaggle-notebooks/metadata/` (rank buckets, deduped index, download status)

To generate the deep-dive strategy report from downloaded notebooks:

```bash
uv run python scripts/analyze_kaggle_notebooks.py
```

Report output: `docs/notebook-deep-dive.md`

## Baseline reproduction workspace

To snapshot a top notebook into a reproducible local baseline workspace:

```bash
uv run python scripts/prepare_baseline_repro.py \
  --ref nina2025/birdclef-2026-eos-6-bz
```

Output folder:

- `experiments/baselines/nina2025_birdclef-2026-eos-6-bz/`
  - source notebook copy
  - `kernel-metadata.json`
  - `manifest.json` (checksums + provenance)
  - baseline reproduction notes

## CV protocol and experiment tracking

- Validation protocol: `docs/cv-protocol.md`

Initialize tracking tables for CV/LB drift and experiment registry:

```bash
uv run python scripts/init_experiment_tracking.py
```

Tracking output folder:

- `experiments/tracking/leaderboard_tracking.csv`
- `experiments/tracking/experiment_registry.csv`

## Model portfolio scaffolding

- Portfolio blueprint: `docs/model-portfolio.md`
- Stream configs: `experiments/configs/model_portfolio/*_stream.json`
- Output contract: `experiments/configs/model_portfolio/output_schema.json`

Generate a stream manifest:

```bash
uv run python scripts/build_model_portfolio_manifest.py
```

## Fusion / calibration plan

- Fusion configs: `experiments/configs/fusion/`
- Generated plan artifact: `experiments/fusion/plan.json`

```bash
uv run python scripts/build_fusion_plan.py
```

## Runtime hardening and advanced ablations

- Runtime checklist: `docs/runtime-hardening.md`
- Advanced ablation matrix: `docs/advanced-ablation-plan.md`

Validate submission file contract before upload:

```bash
uv run python scripts/check_submission_contract.py --submission submission.csv
```

Run runtime-hardening checks and write tracking/report artifacts:

```bash
uv run python scripts/runtime_hardening_runner.py \
  --experiment-id baseline-runtime-v1 \
  --submission submission.csv \
  --min-class-columns 234 \
  --repeat 2
```

Register advanced ablation matrix runs:

```bash
uv run python scripts/run_ablation_matrix.py \
  --base-experiment-id baseline-runtime-v1
```

Optional smoke-test helper to generate a synthetic submission:

```bash
uv run python scripts/generate_mock_submission.py \
  --output experiments/runtime/mock/submission.csv \
  --rows 12 \
  --classes 234
```

## Raunak V6 threshold/calibration sweep packaging

Generate ready-to-push Kaggle notebook variants around the current best Raunak V6 baseline:

```bash
uv run python scripts/create_raunak_sweep_notebooks.py
```

Output:

- `experiments/kaggle_submission/raunak-v6-sweep-v1/<variant>/`
- `experiments/kaggle_submission/raunak-v6-sweep-v1/variants_manifest.json`

## Current leaderboard status

- Best submission so far: `kaggle-ported-raunak-v6-v1` with **0.949** public score.
- Raunak calibration sweep (`calib-a/b/c`) all scored **0.948** (regression vs champion).
- Next hedge run is active: `aleixlopez/birdclef-2026-meenal-v1` (ported Meenal Improved).

See detailed logs in:

- `experiments/tracking/leaderboard_tracking.csv`
- `experiments/tracking/experiment_registry.csv`
