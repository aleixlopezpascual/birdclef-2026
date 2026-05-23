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
