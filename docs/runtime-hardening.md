# Runtime hardening checklist

Use this checklist before promoting an inference pipeline for submission.

## 1. Determinism

- Fixed seed values recorded in experiment registry.
- Same inputs produce identical `submission.csv` checksum.

## 2. Runtime budget

- End-to-end inference measured on representative soundscape batch.
- Runtime leaves margin under Kaggle CPU notebook limits.

## 3. Memory discipline

- Peak memory usage monitored during inference.
- No unbounded accumulators over full soundscape set.

## 4. Backend fallback

- Preferred backend order documented (ONNX/Torch/TFLite as applicable).
- Fallback behavior is explicit and tested.

## 5. Submission integrity

- `submission.csv` has `row_id` + all class columns.
- All probabilities are numeric and clipped to `[0, 1]`.
- No duplicated or missing `row_id`.

## 6. Code-competition blend safety (critical)

- Never submit blends built from cached `submission*.csv` artifacts from other notebooks.
- For scored submissions, generate all blended predictions in the same notebook run against the current hidden test rows.
- Add fail-fast guards before writing `submission.csv`:
  - template row count sanity check (reject tiny debug templates),
  - strict `row_id` coverage check for every blended source,
  - no NaN fallback that can silently alter output semantics.
