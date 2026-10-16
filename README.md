# MedViHall

**Not All Hallucinations Cost the Same: MedViHall, a Severity-Weighted Benchmark for Medical Vision-Language Models**

MedViHall scores hallucinations in medical VLM answers by clinical severity rather than counting them equally.
Twelve VLMs are evaluated on three modalities: dermatology, histopathology and ophthalmology (2,300 images; 7,850 responses per model; 94,200 responses in total).
Metrics: SMHR (severity-weighted medical hallucination rate), CHR (clinically harmful response rate) and SRI (specialisation ratio index).

## Repository layout

| Path | Content |
|---|---|
| `paper/` | LaTeX source (`main.tex`), bibliography (`ref.bib`), tables (`T*.tex`), figures (`fig*.png`), compiled `main.pdf`, `CHANGELOG.md` |
| `tools/make_release.py` | Builds the filtered, GitHub-ready copy of the full project folder |
| `tools/rejoin_chunks.py` | Rejoins files that were split into `*.parts/` and verifies SHA-256 |

Build the paper: `cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main`.

## Paper, figures and tables

- **Compiled paper:** [`paper/main.pdf`](paper/main.pdf) (LaTeX source: [`paper/main.tex`](paper/main.tex), bibliography: [`paper/ref.bib`](paper/ref.bib)).
- **Figures:** PNGs `paper/fig*.png` (Fig. 1 overview, 2 SMHR ranking, 3 modality fingerprints, 4 specialisation paradox, 5 normal-image paradox, 6 cross-modal transfer, 7 metric concordance, 8 calibration, 9 mitigation, 12 annotation agreement). Vector PDFs and the underlying data are in `paper_figures/` (`fig*.pdf`, `fig*.csv`).
- **Tables:** `paper/T1_dataset_strata.tex`, `T2_models.tex`, `T3_main_results.tex`, `T4_mitigation.tex`, `T5_annotation_agreement.tex`. The same tables with CSV data are in `paper_tables/`.
- **Three-modality revision:** scripts, results and change log in `revision_three_modalities/` (`CHANGELOG_three_modalities.md`).
- **Legacy summaries:** older summary files in `medvihall_outputs/` and `paper_tables/` were computed before radiology was removed and still carry a radiology breakdown; the paper and `revision_three_modalities/` are authoritative.

## Release conventions

- **Modalities.** The released data covers dermatology, histopathology and ophthalmology only. Radiology records are removed.
- **Images.** Dataset images are not redistributed; obtain them from the original sources under their licences.
- **Model weights.** Not stored in this repository.
- **Large files.** GitHub rejects files over 100 MB, so larger files are stored as `<name>.parts/part_000, part_001, ...` (each at most 95 MB) with a `MANIFEST.json`. Restore with `python tools/rejoin_chunks.py --all .`.
- **Secrets.** API keys and Hugging Face tokens in notebooks and scripts are replaced by placeholders (`hf_REDACTED`, `sk-REDACTED`). Supply your own via environment variables (`HF_TOKEN`, `OPENAI_API_KEY`).
- **Annotations.** The inter-annotator study files under `human_annotations/` contain simulated annotations, as described in the paper's audit section; they are not clinician labels.
