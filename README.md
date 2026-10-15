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

## Release conventions

- **Modalities.** The released data covers dermatology, histopathology and ophthalmology only. Radiology records are removed.
- **Images.** Dataset images are not redistributed; obtain them from the original sources under their licences.
- **Model weights.** Not stored in this repository.
- **Large files.** GitHub rejects files over 100 MB, so larger files are stored as `<name>.parts/part_000, part_001, ...` (each at most 95 MB) with a `MANIFEST.json`. Restore with `python tools/rejoin_chunks.py --all .`.
- **Secrets.** Hugging Face tokens in notebooks and scripts are replaced by `hf_REDACTED`. Supply your own token via the `HF_TOKEN` environment variable.
- **Annotations.** The inter-annotator study files under `human_annotations/` contain simulated annotations, as described in the paper's audit section; they are not clinician labels.
