# Raunak V6 Domain Tuning Implementation Summary

**Date:** 2026-05-25  
**Branch:** aleixlopezpascual/crispy-giggle  
**Objective:** Beat Raunak V6 base (0.949 LB) by targeting three domain-specific gaps

---

## What Was Built

### 1. Per-Class Threshold Infrastructure
**File:** `scripts/generate_per_class_thresholds.py`

Generates species-specific thresholds based on domain knowledge:
- **234 species** mapped into 4 groups:
  - 161 bird species (Aves)
  - 28 soundscape-only species (rare, training data in soundscapes only)
  - 25 few-shot species (limited training examples)
  - 20 non-bird species (Insecta, Reptilia, Amphibia, Mammalia)

**Output:** `experiments/configs/fusion/sweeps/per-class-v1/`
- 3 variants: conservative, balanced, aggressive
- Each variant has a `per_class_thresholds.csv` with thresholds for all 234 species

### 2. Wave 1: Per-Class Tuning Notebooks (3 variants)
**File:** `scripts/create_per_class_tuning_notebooks.py`  
**Output:** `experiments/kaggle_submission/raunak-v6-per-class-tuning-v1/`

Extended Raunak V6 base with per-class threshold post-processing:

| Variant | Bird | Few-Shot | Soundscape | Non-Bird | Rationale |
|---------|------|----------|-----------|----------|-----------|
| **Conservative** | 0.50 | 0.45 | 0.35 | 0.55 | Strict non-bird handling; boost rare species |
| **Balanced** | 0.48 | 0.40 | 0.28 | 0.52 | Middle ground; optimize for macro-AUC |
| **Aggressive** | 0.46 | 0.35 | 0.24 | 0.50 | Maximum recall; catch rare soundscape species |

Each notebook:
- Loads ported Raunak V6 base predictions
- Applies per-class threshold CSV at post-processing step
- Outputs `submission.csv` compatible with Kaggle

### 3. Wave 2: Non-Bird Specialist Notebook (1 variant)
**File:** `scripts/create_non_bird_specialist_notebook.py`  
**Output:** `experiments/kaggle_submission/raunak-v6-non-bird-specialist-v1/`

Separate temperature tuning for non-bird taxa:
- Non-bird species: Temperature 1.15 (softer predictions, less polarized)
- Bird species: Temperature 0.95 (sharper predictions, more polarized)
- Handles ~20 non-bird species (frogs, insects, reptiles) with domain-specific scaling

### 4. Wave 3: Soundscape-Only Boost Notebook (1 variant)
**File:** `scripts/create_soundscape_boost_notebook.py`  
**Output:** `experiments/kaggle_submission/raunak-v6-soundscape-boost-v2/`

Direct optimization for 28 soundscape-only species:
- **Multiplier:** 1.08× (boost predictions slightly)
- **Threshold:** 0.28 (lower than general species)
- Targets rare species that only appear in soundscape training data

---

## Design Rationale

### Why Per-Class Thresholds?
- **Current bottleneck:** Raunak V6 uses global or per-group thresholds
- **Opportunity:** Each species has different baseline rates, SNR, and training distribution
- **Mechanism:** Different thresholds for bird vocalizations (high-SNR) vs. frogs (lower SNR) vs. rare species (data scarcity)

### Why Non-Bird Specialist?
- **Domain gap:** Non-bird taxa (20 species) have distinct acoustic characteristics
  - Frog calls: repetitive, structured patterns
  - Insect sounds: high-frequency, background noise
  - Reptile vocalizations: rare, low-power signals
- **Mechanism:** Temperature scaling allows differential confidence calibration without retraining

### Why Soundscape-Only Boost?
- **Challenge:** 28 species only appear in soundscape training data (rare)
- **Risk:** Underconfident predictions due to less direct supervision
- **Mechanism:** Direct multiplier (1.08×) + lower threshold (0.28) combined to boost signal for rare species

---

## Submission Strategy

### Wave 1 (Per-Class): Submit 3 variants in parallel
- Goal: Identify best threshold strategy
- Expected feedback: 1-2 variants likely beat 0.949 base
- Decision point: Use winning variant as baseline for Waves 2 & 3

### Wave 2 (Non-Bird): Submit 1 variant
- Condition: Launch after Wave 1 LB feedback
- Goal: Isolated test of non-bird temperature tuning
- Expected impact: Modest improvement if non-bird taxa are limiting

### Wave 3 (Soundscape-Only): Submit 1 variant
- Condition: Launch after Wave 1/2 LB feedback
- Goal: Boost recall on rare soundscape species
- Expected impact: Depends on macro-AUC weight for rare classes

**Total submissions:** 5 notebooks (Wave 1: 3, Wave 2: 1, Wave 3: 1)

---

## Tracking & Metrics

### Leaderboard CSV Columns
All submissions tracked in `experiments/tracking/leaderboard_tracking.csv`:
- `experiment_id` — Kaggle kernel ID / submission tag
- `timestamp_utc` — When submitted
- `lb_score` — Public leaderboard score
- `delta_lb` — Change vs. 0.949 base
- `threshold_method` — Which tuning approach
- `notes` — Key parameters and observations

### Success Criteria
- ✅ At least one variant beats 0.949 (delta_lb > 0)
- 🎯 Target: One variant reaches 0.950+ for measurable improvement
- 🚀 Stretch: Multiple variants > 0.950 (robust strategy)

---

## Files Created

### Scripts (for reproducibility)
- `scripts/generate_per_class_thresholds.py` — Generate per-class threshold CSVs
- `scripts/create_per_class_tuning_notebooks.py` — Create Wave 1 variants
- `scripts/create_non_bird_specialist_notebook.py` — Create Wave 2 variant
- `scripts/create_soundscape_boost_notebook.py` — Create Wave 3 variant

### Notebook Packages
- `experiments/kaggle_submission/raunak-v6-per-class-tuning-v1/{conservative,balanced,aggressive}/`
- `experiments/kaggle_submission/raunak-v6-non-bird-specialist-v1/`
- `experiments/kaggle_submission/raunak-v6-soundscape-boost-v2/`

### Configs
- `experiments/configs/fusion/sweeps/per-class-v1/{variant}/per_class_thresholds.csv`

### Documentation
- `SUBMISSION_GUIDE.md` — Step-by-step manual submission workflow
- This file: Implementation summary and rationale

---

## Next Steps (Manual)

1. **Submit Wave 1** (3 per-class variants to Kaggle)
   - Upload notebooks to Kaggle
   - Run each end-to-end
   - Record LB scores in leaderboard_tracking.csv

2. **Analyze Wave 1** results
   - Compare delta_lb for each variant
   - Identify best performer
   - Adapt Wave 2/3 if needed

3. **Submit Wave 2** (non-bird specialist)
   - Based on Wave 1 learnings

4. **Submit Wave 3** (soundscape-only boost)
   - Based on Wave 1/2 learnings

5. **Update README** with final results
   - Record champion experiment_id and LB score
   - Document what worked / what didn't

---

## Fallback Plan

If all variants underperform (delta_lb ≤ 0):
- Keep Raunak V6 base (0.949) as final submission
- Document failure modes for future reference
- Consider ensemble or alternative approaches

---

## Reproducibility

To regenerate all artifacts:
```bash
cd experiments/kaggle_submission
python scripts/generate_per_class_thresholds.py
python scripts/create_per_class_tuning_notebooks.py
python scripts/create_non_bird_specialist_notebook.py
python scripts/create_soundscape_boost_notebook.py
```
