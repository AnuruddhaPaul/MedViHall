# MediViHall annotation sample (blind)


720 model generations for blind human review of hallucinations in medical vision-language models, with the 48 images they describe.

## Contents

| Path | What |
|---|---|
| `annotation_sheet.csv` | The 720 items (open in Excel/Sheets; UTF-8). Fill in the last four columns. |
| `annotation_sheet.jsonl` | Same items, one JSON object per line. |
| `images/<modality>/*.jpg` | The 48 images. `image_path` in the sheet is relative to the repo root. |

Each of the 48 images (one image + one question) was answered by 5 models under 3 conditions, giving 15 generations per image. Items are shuffled and carry random IDs (`A0001`…`A0720`); model and condition are intentionally **not** shown so annotation stays blind.

## Columns

| Column | Meaning |
|---|---|
| `item_id` | Random item ID |
| `image_path` | Image shown to the model |
| `modality` | radiology / dermatology / histopathology / ophthalmology |
| `question` | The question the model was asked (includes a request for a 0–100% confidence) |
| `response` | The model's full answer |
| `hallucination_present (Y/N)` | **Annotator:** does the answer assert anything not supported by the image, or omit a finding that is clearly present? |
| `hallucination_types / notes` | **Annotator:** free text (what is wrong, which claim) |
| `severity (0-3)` | **Annotator:** suggested scale 0 = none, 1 = minor, 2 = moderate, 3 = clinically dangerous |
| `annotator` | **Annotator:** your initials |

Judge each answer on its own against the image. Ignore the stated confidence when deciding whether a claim is wrong. Do not try to guess which model wrote an answer.

## Sampling

Questions were drawn stratified by modality × query type (Q1–Q4) and spread across the image strata, 3 questions per cell. Responses that were empty, errors, under 8 words, or that started mid-sentence were excluded before sampling (repetition loops were kept and flagged internally). Details: see the project report.

## Image licences (read before sharing)

The images come from public research datasets (CheXpert, ISIC 2020, HAM10000, NCT-CRC-HE, PatchCamelyon, ORIGA, REFUGE, G1020). Several carry restrictions on redistribution (for example CheXpert's research-use agreement and the non-commercial terms on ISIC/HAM10000), so **keep this repository private** and share it only with the annotators.

## Results and analysis

`RESULTS_AND_ANALYSIS.md` is a single file with the results and analysis of all experiments (core benchmark and Pillars B-E). The same content is split into one text file per experiment in `results/`, with machine-readable numbers in `results/raw/`.

**Annotators: annotate the sheet first and read the results afterwards.** The results show which models and mitigation strategies perform better, which could bias a blind annotation. The key that maps item IDs to models and conditions is deliberately not in this repository.
