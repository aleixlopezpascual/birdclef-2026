# BirdCLEF+ 2026 notebook deep dive

Generated from downloaded Kaggle notebooks in `data/external/kaggle-notebooks/`.

## Collection summary

- Requested: top 20 by score + top 20 by votes
- Collected rows: 40
- Unique notebooks downloaded: 38
- Metadata index: `data/external/kaggle-notebooks/metadata/combined_index.csv`

## Top voted notebooks (sample)

| Vote rank | Ref | Votes | Title |
| --- | --- | --- | --- |
| 1 | `dingjiarun/pantanal-distill-birdclef2026-onnx` | 728 | pantanal-distill-birdclef2026-ONNX |
| 2 | `yusufmurtaza01/pantanal-distill-birdclef2026-improvement` | 411 | pantanal-distill-birdclef2026-Improvement |
| 3 | `imaadmahmood/birdclef-2026-perch-v2-protossm-0-925` | 373 | BirdCLEF+ 2026 — Perch v2 + ProtoSSM · 0.925 |
| 4 | `marynaborovska/birdclef-26-two-pass-ssm-advanced-pp` | 360 | BirdCLEF+ 26 / Two-Pass SSM + Advanced PP |
| 5 | `vyankteshdwivedi/birdclef-2026-onnx-perch-sequence-modeling` | 354 | BirdCLEF 2026 — ONNX Perch + Sequence Modeling |
| 6 | `ulyanovantonamaranta/birdclef-2026-gate-fake008-head0015` | 336 | BirdCLEF+ 2026 Gate Fake008 Head0015 |
| 7 | `jaejohn/perch-v2-starter-train-infer` | 292 | perch_v2 starter: train + infer |
| 8 | `yash9439/pantanal-distill-birdclef2026-improvement` | 269 | pantanal-distill-birdclef2026-Improvement |
| 9 | `nina2025/birdclef-2026-eos-6-bz` | 267 | BirdCLEF+ 2026 / EoS.6 (bz) |
| 10 | `hideyukizushi/bird26-reproduce-perch-protossm-resssm-inf-train` | 257 | Bird26/REPRODUCE/Perch+ProtoSSM+ResSSM/INF/TRAIN |

## Top score notebooks (sample)

| Score rank | Ref | Votes | Title |
| --- | --- | --- | --- |
| 1 | `nina2025/birdclef-2026-eos-6-bz` | 267 | BirdCLEF+ 2026 / EoS.6 (bz) |
| 2 | `raunakdey07/birdclef-2026-v6` | 174 | BirdCLEF+ 2026 V6 |
| 3 | `meenalsinha/birdclef-2026-improved` | 114 | BirdCLEF+ 2026 Improved |
| 4 | `nina2025/birdclef-2026-eos-3` | 151 | BirdCLEF+ 2026 / EoS.3 |
| 5 | `jungchanryu/birdclef-first` | 9 | birdclef first |
| 6 | `sunderekkiz/birdclef-2026-exp019-eos4-rank-power-06` | 199 | birdclef 2026 exp019 eos4 rank power 06 |
| 7 | `karnakbaevarthur/gated-rank-fusion-pipeline` | 86 | Gated Rank Fusion Pipeline |
| 8 | `adarsh5harma/birdclef-2026-v62-nina-eos3-fork` | 20 | BirdCLEF 2026 v62 nina eos3 fork |
| 9 | `youssefmo942009/birdclef-2026-v6` | 6 | BirdCLEF+ 2026 V6 |
| 10 | `adarsh5harma/birdclef-2026-v63-nina-eos5-fork` | 4 | BirdCLEF 2026 v63 nina eos5 fork |

## Technique coverage across downloaded notebooks

| Technique signal | Presence | Coverage |
| --- | --- | --- |
| Calibration/scaling | 35/38 | 92.1% |
| Perch family | 34/38 | 89.5% |
| Ensembling/fusion | 34/38 | 89.5% |
| SSM family | 32/38 | 84.2% |
| Threshold tuning | 32/38 | 84.2% |
| ONNX inference | 31/38 | 81.6% |
| Test-time augmentation | 31/38 | 81.6% |
| Two-pass pipeline | 26/38 | 68.4% |
| TFLite inference | 11/38 | 28.9% |
| Pseudo-labeling | 2/38 | 5.3% |

## Most common imported modules

| Module | Presence |
| --- | --- |
| `numpy` | 37/38 |
| `os` | 37/38 |
| `pandas` | 37/38 |
| `pathlib` | 36/38 |
| `re` | 35/38 |
| `sklearn` | 35/38 |
| `soundfile` | 35/38 |
| `torch` | 35/38 |
| `tensorflow` | 34/38 |
| `tqdm` | 34/38 |
| `concurrent` | 30/38 |
| `onnxruntime` | 30/38 |
| `scipy` | 29/38 |
| `time` | 29/38 |
| `gc` | 28/38 |
| `librosa` | 28/38 |
| `subprocess` | 28/38 |
| `warnings` | 28/38 |
| `collections` | 27/38 |
| `json` | 27/38 |

## What high performers are converging on

1. Perch-derived feature backbones plus SSM-style sequence modeling variants are the dominant pattern.
2. ONNX/TFLite inference appears frequently, indicating runtime constraints are a first-class design target.
3. Ensembling (weighted blend, rank-based fusion, gated combinations) is a core source of leaderboard lift.
4. Threshold tuning and post-processing are widely used, suggesting final probability shaping matters substantially.
5. Two-pass and safe-alignment style heuristics appear often enough to treat as important ablation candidates.

## Proposed win-oriented roadmap

1. Build a strong single-model baseline with Perch-family embeddings + robust 5-second aggregation.
2. Add ONNX/TFLite optimized inference path early to keep runtime margin on CPU notebook limits.
3. Introduce calibrated multi-model fusion (rank-power + weighted blend) as the primary lift stage.
4. Run threshold optimization + post-processing tuning on local CV, then lock conservative defaults for LB stability.
5. Add pseudo-label experiments only after stable CV-LB alignment to avoid reinforcing label noise.


## Immediate experiment backlog

1. Reproduce one strong public inference notebook exactly as a hard baseline.
2. Swap in our own validation split and compare CV-vs-LB drift.
3. Build a 3-model ensemble family (Perch variant + SSM variant + lightweight CNN baseline).
4. Tune blend weights/rank-power and per-class/global thresholds on CV.
5. Add controlled pseudo-labeling only for stable high-confidence slices.
