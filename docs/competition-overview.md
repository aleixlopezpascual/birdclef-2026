# BirdCLEF+ 2026 competition overview

This document captures the essential details of the Kaggle **BirdCLEF+ 2026** competition so the project can align modeling, validation, and submission workflows with the official rules.

## 1. Competition snapshot

| Item | Details |
| --- | --- |
| Name | BirdCLEF+ 2026 |
| Host | Cornell Lab of Ornithology |
| URL | https://kaggle.com/competitions/birdclef-2026 |
| Core challenge | Acoustic species identification in the Pantanal (South America) |
| Domain | Passive acoustic monitoring (PAM), multilabel classification |
| Goal | Identify wildlife species from continuous field audio recordings |

## 2. What the competition is about

The competition asks participants to build machine learning systems that detect species from vocalizations in real-world recordings gathered across Brazil's Pantanal wetlands.

Organizers frame this as a biodiversity monitoring problem at scale:

- Large remote areas are difficult to monitor with regular field surveys.
- A network of acoustic recorders generates massive, continuous soundscape data.
- Manual annotation does not scale; robust automated identification is needed.

The intended impact is better evidence for conservation and ecosystem monitoring in one of the most biodiverse and threatened regions on Earth.

## 3. Task framing

- **Prediction target:** Probability that each species is present.
- **Granularity:** Each submission row corresponds to a **5-second** audio window (`row_id`).
- **Output shape:** One probability column per species.
- **Learning setting:** Multilabel audio event/species classification from noisy field recordings.

## 4. Evaluation metric

The leaderboard metric is a **macro-averaged ROC-AUC variant** that excludes classes without true positives in the ground truth.

Practical implication: class imbalance and rare-species behavior can strongly affect model selection and calibration.

## 5. Official timeline (UTC)

All deadlines are 11:59 PM UTC unless otherwise stated.

| Milestone | Date |
| --- | --- |
| Competition start | March 11, 2026 |
| Entry deadline | May 27, 2026 |
| Team merger deadline | May 27, 2026 |
| Final submission deadline | June 3, 2026 |

## 6. Code competition constraints

Submissions must be made through Kaggle Notebooks and comply with code-competition rules:

- CPU Notebook runtime must be **<= 90 minutes**.
- GPU submissions are effectively disabled for this competition context (submissions get only ~1 minute runtime).
- Internet access must be disabled.
- External data is allowed if freely and publicly available (including pre-trained models).
- Submission file name must be `submission.csv`.

## 7. Prizes and awards

### Main competition prizes

- 1st: $15,000
- 2nd: $10,000
- 3rd: $8,000
- 4th: $7,000
- 5th: $5,000

### Optional working note awards

Participants can also submit a working note to the CLEF 2026 conference.

- Two best working notes receive **$2,500 each**.
- Working note timeline includes:
  - June 3, 2026: competition deadline
  - June 17, 2026: working note submission deadline
  - June 24, 2026: acceptance notification
  - July 6, 2026: camera-ready deadline

Judging criteria include originality, quality, contribution, and presentation/readability.

## 8. Participation and metadata snapshot

At the captured page snapshot:

- 13,692 entrants
- 4,623 participants
- 3,842 teams
- 125,033 submissions

Tags include Earth and Nature, Animals, Multilabel Classification, Audio Event Classification, and Custom Metric.

## 9. Implications for this repository

To stay aligned with competition constraints, repository work should prioritize:

1. Fast and deterministic inference paths compatible with Kaggle CPU limits.
2. Validation strategies reflecting multilabel ROC-AUC behavior under strong class imbalance.
3. Robust preprocessing for noisy, real-world audio conditions across habitats and seasons.
4. Submission pipelines that reliably generate `submission.csv` with the expected schema.

## 10. Dataset overview and files

Dataset snapshot from the competition page:

- **Total files:** 46,213
- **Total size:** 16.14 GB
- **Primary formats:** `ogg`, `csv`, `txt`
- **License:** CC BY-NC-SA 4.0

The competition uses a **hidden test set**. At scoring time, `test_soundscapes/` is made available inside the submitted notebook environment.

### `train_audio/`

Short recordings of individual calls from birds, amphibians, reptiles, mammals, and insects sourced from xeno-canto and iNaturalist.

- Audio is standardized to **32 kHz** where applicable and converted to `.ogg`.
- File naming pattern: `[collection][file_id_in_collection].ogg`.
- Organizers note that relevant files should already be present, so additional scraping from source portals is not expected to help.

### `test_soundscapes/`

Hidden scoring audio populated during notebook submission.

- Roughly **600** recordings.
- Each file is **1 minute** long, `.ogg`, resampled to **32 kHz**.
- Filename pattern: `BC2026_Test_<fileID>_<site>_<date>_<timeUTC>.ogg`.
- Example: `BC2026_Test_0001_S05_20250227_010002.ogg`.
- Not every species seen in training appears in hidden test data.

### `train_soundscapes/`

Additional soundscapes from roughly similar locations as test recordings.

- Uses the same filename convention as test soundscapes.
- Some recording sites overlap with test, but dates/times do **not** overlap hidden test recordings.
- A labeled subset is provided in `train_soundscapes_labels.csv` with:
  - `filename` (soundscape file reference)
  - `start`, `end` (5-second segment boundaries)
  - `primary_label` (semicolon-separated present species codes)

Important competition note: some species present in hidden test may only appear in labeled `train_soundscapes` and not in `train_audio`.

### `train.csv`

Metadata table for training recordings. Key fields:

- `primary_label`: target class code (eBird code for birds; iNaturalist taxon ID for non-birds)
- `secondary_labels`: additional co-occurring labels (incomplete in some cases)
- `latitude`, `longitude`: recording location
- `author`: contributor/recordist
- `filename`: associated audio file name
- `rating`: quality (Xeno-canto style; `0` means unavailable; iNaturalist has no quality ratings)
- `collection`: `XC` or `iNat`

### `sample_submission.csv`

Reference submission template:

- `row_id` format: `[soundscape_filename]_[end_time]`
- Includes **234 species columns** that require probability predictions per 5-second window.

### `taxonomy.csv`

Class metadata for submission columns:

- **234 rows**, matching the **234 target columns** in submissions.
- Includes taxonomy info and class grouping (`Aves`, `Amphibia`, `Mammalia`, `Insecta`, `Reptilia`).
- Includes insect sonotypes (e.g., `47158son16`) treated as valid classes.
- `primary_label` defines the submission column name.

### `recording_location.txt`

Location context for the recording campaign:

- Pantanal, Mato Grosso do Sul, Brazil, South America
- Approximate deployment bounds:
  - Latitude: `-16.5` to `-21.6`
  - Longitude: `-55.9` to `-57.6`

## 11. Dataset implications for modeling

1. Build pipelines around **5-second prediction windows** over 1-minute soundscapes.
2. Expect weak/partial labels (`secondary_labels` incomplete, partial soundscape labels).
3. Treat class coverage carefully: training classes and hidden-test classes are not a perfect one-to-one presence match.
4. Leverage geolocation and source metadata (`collection`, coordinates, quality rating) as potential robustness signals.
5. Keep inference fast enough for notebook constraints when processing ~600 test soundscapes.

## 12. Citation

Stefan Kahl, Tom Denton, Larissa Sugai, Liliana Piatti, Ryan Holbrook, Holger Klinck, and Ashley Oldacre. *BirdCLEF+ 2026*. https://kaggle.com/competitions/birdclef-2026, 2026. Kaggle.
