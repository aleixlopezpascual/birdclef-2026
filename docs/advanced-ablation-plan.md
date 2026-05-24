# Advanced ablation plan

Run these only after baseline, CV protocol, portfolio, and fusion stack are stable.

## Gate criteria

- CV and public LB are directionally aligned across recent promoted runs.
- Runtime pipeline is stable and submission contract checks are consistently passing.

## Ablation matrix

| Ablation | Variants | Promotion rule |
| --- | --- | --- |
| Two-pass inference | off / on | Keep only if CV improves and LB does not regress |
| Safe-align heuristic | off / v1 / v2 | Keep only if positive net delta after threshold retuning |
| Pseudo-labeling | off / high-confidence only | Keep only if gain persists across multiple seeds |

## Logging requirements

- Link every ablation run to `experiment_registry.csv`.
- Log CV/LB deltas in `leaderboard_tracking.csv`.
- Record runtime cost deltas relative to non-ablated baseline.
