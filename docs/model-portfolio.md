# Model portfolio blueprint

This portfolio follows the deep-dive finding that winning solutions combine complementary model families before fusion.

## Streams

1. **Perch-centric stream**
   - Strong semantic acoustic features
   - Default “anchor” stream for stable performance

2. **SSM-enhanced stream**
   - Sequence modeling focus (temporal structure over windows)
   - Used to complement Perch with different error profile

3. **Lightweight CNN/alternative stream**
   - Lower-latency model family to diversify the ensemble
   - Useful for runtime-safe fallback and diversity in fusion

## Output contract

All streams must export identical prediction artifacts:

- one row per `row_id`
- one probability column per class
- same class ordering as submission schema

Use `experiments/configs/model_portfolio/output_schema.json` as the compatibility contract.

## Required metadata per stream run

- `experiment_id`
- `config_hash`
- fold configuration reference
- runtime summary
- output checksum
