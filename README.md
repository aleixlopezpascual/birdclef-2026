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

## Two-model blend packaging

Build a competition notebook that blends the two current 0.949 models (Raunak V6 + Meenal V1):

```bash
uv run python scripts/create_two_model_blend_notebook.py
```

> [!WARNING]
> **Do not submit cached-output CSV blends as competition entries.**
> For BirdCLEF code-competition scoring, blending must happen inside the same scoring run that generates
> predictions for the current hidden test set. Reusing `submission*.csv` artifacts from other kernels can produce
> scoring errors or invalid leaderboard behavior, even when file schema looks correct.

## Three-stream blend packaging

Build a competition notebook that rank-blends three existing streams
(Raunak V6 + Meenal V1 + EoS6) with conservative weights:

```bash
uv run python scripts/create_three_stream_blend_notebook.py
```

## Class-group threshold sweep

Generate per-class threshold sweep variants for three groups
(`soundscape_only`, `few_shot`, `standard`) using taxonomy order:

```bash
uv run python scripts/create_class_group_threshold_sweep.py
```

Outputs:

- `experiments/configs/fusion/sweeps/class-group-v1/<variant>/per_class_thresholds.csv`
- `experiments/configs/fusion/sweeps/class-group-v1/<variant>/threshold_strategy.json`
- `experiments/configs/fusion/sweeps/class-group-v1/variants_manifest.json`

## Three-stream + soundscape-only boost packaging

Build a three-stream blend variant that applies a conservative multiplicative
boost on the 28 soundscape-only classes before writing `submission.csv`:

```bash
uv run python scripts/create_three_stream_soundscape_boost_notebook.py
```

## Three-stream + non-bird specialization packaging

Build a three-stream blend variant that applies class-specific boost factors
for non-bird classes (Amphibia/Insecta/Mammalia/Reptilia):

```bash
uv run python scripts/create_three_stream_non_bird_specialized_notebook.py
```

## Parallel three-stream sweep packaging

Create a parallel-ready family of three-stream blend notebooks (baseline, boosts,
and combo variants) for rapid back-to-back Kaggle submissions:

```bash
uv run python scripts/create_three_stream_parallel_sweep_notebooks.py
```

Outputs:

- `experiments/kaggle_submission/three-stream-parallel-sweep-v1/<variant>/`
- `experiments/kaggle_submission/three-stream-parallel-sweep-v1/variants_manifest.json`

## Current leaderboard status

- Best submission so far: `kaggle-ported-raunak-v6-v1` with **0.949** public score.
- Meenal hedge run (`kaggle-ported-meenal-improved-v1`) scored **0.949** (tie with champion).
- New self-contained blends both completed and scored **0.949** (tie, no gain):
  - `kaggle-blend-m7-m3-v1` (M7 0.965 + M3 0.035)
  - `kaggle-blend-m7-m4-v1` (M7 0.70 + M4 0.30)
- Raunak calibration sweep (`calib-a/b/c`) all scored **0.948** (regression vs champion).
- Two-model blend v2 scored **0.500** (blend bug due row alignment mismatch; fail-fast fix now applied).

### ⚠️ Research findings (deep dive complete — 2026-05-26)

**Key discovery:** Raunak V6 already includes ALL major techniques found in top public notebooks:
- TTA (5 circular shifts), ResidualSSM 2nd pass, site/hour priors, MLP probes, Gates 1-5 (fake/temporal/SED/sonotype/rare-class)

**5 domain-tuning notebooks generated earlier are BUGGY — do not submit:**
- `raunak-v6-per-class-{conservative,balanced,aggressive}`, `non-bird-specialist`, `soundscape-boost-v2`
- Bug: all use binary thresholding `(score > threshold).astype(int)` which **destroys ROC-AUC** (rank-based metric)
- Marked `DO_NOT_SUBMIT` in `leaderboard_tracking.csv`

**Gap to top LB (~0.963) is mainly from multi-model ensemble diversity**, not missing techniques.

**Recommended next path:**
1. Fix two-model blend using pre-computed Kaggle dataset CSVs (Nina's approach)
2. Sweep gate parameters (fake blend 0.06–0.10, temporal radius 2–4)
3. Research report: `session-state/files/research/do-a-research-about-the-discussions-topi.md`

## What we have tried so far

| Experiment | Notebook / ID | Result | Outcome |
| --- | --- | --- | --- |
| Constant baseline | `kaggle-constant-baseline-v1` | 0.500 | Floor sanity-check only |
| Perch starter port | `kaggle-ported-perch-starter-v1` | 0.825 | Strong baseline jump |
| Raunak V6 port | `kaggle-ported-raunak-v6-v1` | **0.949** | Current champion |
| Raunak sweep calib-a | `kaggle-raunak-v6-sweep-calib-a` | 0.948 | Regressed vs champion |
| Raunak sweep calib-b | `kaggle-raunak-v6-sweep-calib-b` | 0.948 | Regressed vs champion |
| Raunak sweep calib-c | `kaggle-raunak-v6-sweep-calib-c` | 0.948 | Regressed vs champion |
| Meenal Improved port | `kaggle-ported-meenal-improved-v1` | 0.949 | Ties champion (good hedge) |
| Two-model blend (Raunak+Meenal) | `kaggle-two-model-blend-v1` | 0.500 | v2 failed due row alignment mismatch; generator patched to fail-fast (no silent 0.5 fill) |
| Two-model blend rerun | `kaggle-two-model-blend-v3` | failed | fail-fast detected 3 missing `row_id` in Meenal source |
| Two-model blend rerun | `kaggle-two-model-blend-v4` | failed | fallback still produced NaNs in blend output check |
| Two-model blend rerun | `kaggle-two-model-blend-v5` | failed | still collapsed; source template issue persisted |
| Two-model blend rerun | `kaggle-two-model-blend-v6` | failed | switched template source; still not robust enough |
| Two-model blend rerun | `kaggle-two-model-blend-v7` | scoring_error | cached-source blending still invalid for hidden scoring; path now hardened to fail-fast |
| Two-model blend rerun | `kaggle-two-model-blend-v8` | failed (expected) | hard fail-fast guard blocked unsafe small-template run |
| Self-contained blend (M7+M3) | `kaggle-blend-m7-m3-v1` | 0.949 | Stable run, ties champion (no uplift) |
| Self-contained blend (M7+M4) | `kaggle-blend-m7-m4-v1` | 0.949 | Stable run, ties champion (no uplift) |

### Current in-flight

- `aleixlopez/birdclef-2026-two-model-blend-v1` is now in **fail-fast safety mode** (no further submissions from this cached-source blend path).
- Three-stream candidates remain packaged (not yet submitted in this cycle):
  - `aleixlopez/birdclef-2026-three-stream-blend-v1`
  - `aleixlopez/birdclef-2026-three-stream-soundscape-boost-v1`
  - `aleixlopez/birdclef-2026-three-stream-non-bird-specialized-v1`
- Parallel sweep family is also packaged (`three-stream-parallel-sweep-v1`) with 5 variants:
  - baseline, soundscape-boost, non-bird-specialized, combo-boost, eos-heavy-combo
- After completion/push, submit manually to competition to get public LB score.

See detailed logs in:

- `experiments/tracking/leaderboard_tracking.csv`
- `experiments/tracking/experiment_registry.csv`
