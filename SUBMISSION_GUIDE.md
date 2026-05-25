# Raunak V6 Domain Tuning Submission Guide

## Overview
This guide coordinates manual submissions of domain-optimized Raunak V6 variants to Kaggle. Each variant targets specific gaps:

1. **Per-class thresholds** (Wave 1) — Optimize species-specific decision boundaries
2. **Non-bird specialist** (Wave 2) — Separate handling for non-bird taxa
3. **Soundscape-only boost** (Wave 3) — Direct multiplier for 28 rare species

**Current champion:** Raunak V6 base at **0.949 LB**

---

## Wave 1: Per-Class Threshold Variants (3 notebooks)

### Variant 1A: Conservative
- **Path:** `experiments/kaggle_submission/raunak-v6-per-class-tuning-v1/conservative/`
- **Notebook:** `raunak_v6_per_class_conservative.ipynb`
- **Kaggle ID:** `aleixlopez/birdclef-2026-raunak-v6-per-class-conservative`
- **Config:** 3 class groups with stratified thresholds
  - Bird: 0.50
  - Few-shot: 0.45
  - Soundscape-only: 0.35
  - Non-bird: 0.55
- **Expected:** Slightly more conservative predictions; may improve precision

### Variant 1B: Balanced
- **Path:** `experiments/kaggle_submission/raunak-v6-per-class-tuning-v1/balanced/`
- **Notebook:** `raunak_v6_per_class_balanced.ipynb`
- **Kaggle ID:** `aleixlopez/birdclef-2026-raunak-v6-per-class-balanced`
- **Config:** Middle-ground thresholds
  - Bird: 0.48
  - Few-shot: 0.40
  - Soundscape-only: 0.28
  - Non-bird: 0.52
- **Expected:** Balance between precision and recall

### Variant 1C: Aggressive
- **Path:** `experiments/kaggle_submission/raunak-v6-per-class-tuning-v1/aggressive/`
- **Notebook:** `raunak_v6_per_class_aggressive.ipynb`
- **Kaggle ID:** `aleixlopez/birdclef-2026-raunak-v6-per-class-aggressive`
- **Config:** Lower thresholds to boost recall
  - Bird: 0.46
  - Few-shot: 0.35
  - Soundscape-only: 0.24
  - Non-bird: 0.50
- **Expected:** Higher recall, may increase false positives

---

## Wave 2: Non-Bird Specialist (1 notebook)

### Variant 2A: Non-Bird Specialist
- **Path:** `experiments/kaggle_submission/raunak-v6-non-bird-specialist-v1/`
- **Notebook:** `raunak_v6_non_bird_specialist_v1.ipynb`
- **Kaggle ID:** `aleixlopez/birdclef-2026-raunak-v6-non-bird-specialist-v1`
- **Tuning:** Separate temperature scaling
  - Non-bird species: Temperature 1.15 (softer predictions)
  - Bird species: Temperature 0.95 (sharper predictions)
- **Expected:** Better handling of non-bird taxa (frogs, insects, reptiles)

**Launch after Wave 1:** Wait for Wave 1 results; use best performer as baseline if available.

---

## Wave 3: Soundscape-Only Boost (1 notebook)

### Variant 3A: Soundscape-Only Boost
- **Path:** `experiments/kaggle_submission/raunak-v6-soundscape-boost-v2/`
- **Notebook:** `raunak_v6_soundscape_boost_v2.ipynb`
- **Kaggle ID:** `aleixlopez/birdclef-2026-raunak-v6-soundscape-boost-v2`
- **Tuning:**
  - Multiplier for 28 soundscape-only species: 1.08×
  - Threshold for soundscape-only species: 0.28
- **Expected:** Boost recall for rare soundscape-only species

**Launch after Wave 1:** Use best Wave 1 or Wave 2 result as comparison.

---

## Submission Workflow

### Before Each Submission
1. Download the notebook from `experiments/kaggle_submission/<variant>/`
2. Verify the notebook includes all model dependencies (Perch, TensorFlow, etc.)
3. Test locally if possible to check for syntax errors

### During Submission
1. Open Kaggle Competitions → BirdCLEF+ 2026
2. Create New Notebook (or duplicate template)
3. Copy the notebook cells from the local file
4. Run the notebook end-to-end (watch for kernel timeout)
5. Submit the generated `submission.csv`

### After Submission
1. Wait for public leaderboard score
2. Record in `experiments/tracking/leaderboard_tracking.csv`:
   - experiment_id
   - timestamp_utc
   - lb_score
   - delta_lb (vs 0.949 base)
   - notes (key tuning parameters)
3. Share results in group/log

---

## Tracking Template

Add each submission to `experiments/tracking/leaderboard_tracking.csv`:

```csv
experiment_id,timestamp_utc,lb_score,delta_lb,model_family,fusion_method,threshold_method,notes
kaggle-raunak-v6-per-class-conservative,2026-05-25T16:00:00Z,0.950,0.001,perch+ssm,rank-blend-tuned,per-class-conservative,conservative thresholds; bird=0.50 soundscape=0.35
kaggle-raunak-v6-per-class-balanced,2026-05-25T17:00:00Z,0.951,0.002,perch+ssm,rank-blend-tuned,per-class-balanced,balanced thresholds; bird=0.48 soundscape=0.28
```

---

## Fallback & Success Criteria

**Fallback:** If all variants underperform, default back to Raunak V6 base (0.949 LB).

**Success:** At least one variant achieves **> 0.949 LB** (beat base).

**Target:** One variant reaches **0.950+** for a measurable improvement.
