# BirdCLEF+ 2026 CV protocol

This protocol defines how experiments are evaluated locally and compared against public leaderboard movement.

## 1. Validation unit and target shape

- Predict probabilities per **5-second segment**.
- Evaluate with the same target layout as submission (`row_id` + one column per class).
- Keep class ordering identical to `taxonomy.csv` / submission schema.

## 2. Fold design

Use **grouped folds** to reduce leakage from near-duplicate context:

1. Group by soundscape identity (`filename`) for soundscape-labeled data.
2. For `train_audio`, group by recording source identity when possible (`filename` / source id).
3. Stratify approximately on positive label density to avoid empty-positive folds.

Recommended default:

- 5 folds
- fixed random seed
- deterministic fold assignment artifact persisted to disk

## 3. Local metrics

Primary:

- Macro ROC-AUC (competition-aligned, skipping classes with no positives in the evaluated slice)

Secondary:

- Per-class AUC distribution (median + low-tail quantiles)
- Calibration proxy (pre/post temperature scaling)

## 4. CV ↔ LB drift tracking

Every submitted experiment must log:

- experiment id / config hash
- CV score
- public LB score
- `delta_cv` vs previous best
- `delta_lb` vs previous best
- runtime and notes

Promotion rule:

- Promote only if CV improves and LB does not regress materially over repeated submissions.

## 5. Runtime constraints

Track and enforce:

- full inference wall-clock time on 1-minute soundscape batches
- memory footprint during inference
- deterministic output checksum for repeated runs

## 6. Required artifacts per experiment

1. config file / hash
2. fold assignment reference
3. CV summary report
4. generated submission file checksum
5. leaderboard tracking row
