# Quick Reference: Raunak V6 Domain Tuning Submissions

## TL;DR
- ✅ **5 ready-to-submit Kaggle notebooks** for Raunak V6 domain tuning
- 🎯 **Target:** Beat 0.949 LB with per-class threshold optimization
- 📊 **Tracking:** All submissions logged in `experiments/tracking/leaderboard_tracking.csv`

---

## Submission Checklist

### Wave 1: Per-Class Thresholds (3 notebooks)
```
☐ Conservative  → aleixlopez/birdclef-2026-raunak-v6-per-class-conservative
☐ Balanced      → aleixlopez/birdclef-2026-raunak-v6-per-class-balanced
☐ Aggressive    → aleixlopez/birdclef-2026-raunak-v6-per-class-aggressive
```
**Expected:** 1-2 variants beat 0.949 base

### Wave 2: Non-Bird Specialist (1 notebook)
```
☐ Non-Bird      → aleixlopez/birdclef-2026-raunak-v6-non-bird-specialist-v1
```
**Launch after:** Wave 1 LB feedback

### Wave 3: Soundscape-Only Boost (1 notebook)
```
☐ Soundscape    → aleixlopez/birdclef-2026-raunak-v6-soundscape-boost-v2
```
**Launch after:** Wave 1/2 LB feedback

---

## Key Thresholds by Variant

| Variant | Bird | Few-Shot | Soundscape | Non-Bird | Strategy |
|---------|------|----------|-----------|----------|----------|
| Conservative | 0.50 | 0.45 | 0.35 | 0.55 | Boost rare species, strict non-bird |
| Balanced | 0.48 | 0.40 | 0.28 | 0.52 | Precision-recall balance |
| Aggressive | 0.46 | 0.35 | 0.24 | 0.50 | Maximum recall for soundscape species |

---

## Files to Know

| File | Purpose |
|------|---------|
| `SUBMISSION_GUIDE.md` | Step-by-step Kaggle submission workflow |
| `IMPLEMENTATION_SUMMARY.md` | Detailed rationale, design, and reproducibility |
| `experiments/kaggle_submission/raunak-v6-*/` | Notebook packages ready to upload |
| `experiments/configs/fusion/sweeps/per-class-v1/` | Per-class threshold CSVs |
| `experiments/tracking/leaderboard_tracking.csv` | Submit results here |

---

## One-Line Success Criteria

**Minimum:** One variant > 0.949 LB ✅  
**Target:** One variant ≥ 0.950 LB 🎯  
**Stretch:** Multiple variants > 0.950 LB 🚀

---

## After Each Submission

1. Record in `leaderboard_tracking.csv`:
   ```
   experiment_id,timestamp_utc,lb_score,delta_lb,threshold_method,notes
   kaggle-raunak-v6-per-class-conservative,2026-05-25T16:30:00Z,0.950,0.001,per-class-conservative,"Bird=0.50 Soundscape=0.35"
   ```

2. Decide next wave based on delta_lb

3. Update README if new champion found

---

## Fallback

If all variants fail: Keep Raunak V6 base (0.949) as final submission.

---

## Questions?

- See `IMPLEMENTATION_SUMMARY.md` for detailed design rationale
- See `SUBMISSION_GUIDE.md` for step-by-step Kaggle workflow
- Check `experiments/tracking/leaderboard_tracking.csv` for all past submissions
