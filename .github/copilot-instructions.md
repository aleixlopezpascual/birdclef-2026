# GitHub Copilot instructions for this repository

## Project basics
- Repository purpose: BirdCLEF+ 2026 Kaggle competition workflow (audio species identification).
- Main competition docs:
  - `docs/competition-overview.md`
  - `docs/notebook-deep-dive.md`
  - `README.md` (operational summary + latest experiment status)
- Experiment tracking source of truth:
  - `experiments/tracking/leaderboard_tracking.csv`
  - `experiments/tracking/experiment_registry.csv`

## Expected workflow
1. Prefer reproducible scripts under `scripts/` for any repeated process.
2. Keep notebook packaging artifacts under `experiments/kaggle_submission/`.
3. Record every leaderboard-relevant run in tracking CSVs with clear status and notes.
4. Preserve current best score as champion unless a new run clearly beats it.

## Kaggle competition specifics
- This is a **code competition**: notebook runs and competition scoring are separate steps.
- A notebook can be `COMPLETE` but still needs manual **Submit to Competition** to get LB score.
- Submission format must match `sample_submission.csv` exactly (`row_id`, class columns, row count).

## Documentation maintenance rules
- When experiment status changes, update `README.md` section:
  - `Current leaderboard status`
  - `What we have tried so far`
- Add/refresh docs only where relevant; do not create extra planning markdown files.
- Keep docs aligned with actual tracked state in CSV files.

## Coding and change conventions
- Make surgical changes; avoid unrelated refactors.
- Reuse existing patterns in `scripts/` and `experiments/configs/`.
- Validate generated artifacts before pushing Kaggle kernels.
- Use clear experiment IDs (e.g., `kaggle-two-model-blend-v1`) consistently across files.
