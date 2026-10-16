# Figure manifest

Each entry lists the source result files, the script and function, the claim the figure supports, and a draft caption (two sentences, sample size and meaning of the error bars stated). Source data for every figure sits beside it as `<name>.csv`; vector PDF and 300 dpi PNG are in `paper_figures/`. Regenerate everything with `python make_figures.py`.

Venue sizes (fig_style.py): single column 3.4 in, double column 7.0 in, text height 9.0 in (placeholder until the venue is chosen).

## Fig 1 -- `fig01_overview`

- **Files:** `paper_figures/fig01_overview.pdf`, `.png`, `.csv`
- **Source result files:** medvihall_data/data/ground_truth/manifest_3500.json (image/stratum counts); medvihall_outputs/layer2_judge.jsonl, layer1_verdicts.jsonl (response/claim counts); compute_model_metrics.py (class weights)
- **Script / function:** `figs_a.py:fig01` (run via `make_figures.py`)
- **Claim supported:** The benchmark is a two-layer, claim-level pipeline whose output is a severity-weighted rate.
- **Draft caption:** Overview of MedViHall: 3,500 images from four modalities are shown to 12 VLMs, responses are split into claims, checked by an automated Layer 1 and an LLM-judge Layer 2, and aggregated into severity-weighted metrics (SMHR). Counts are read from the result files; the pipeline description follows the stage scripts.
- **Size:** 7.00 x 2.35 in

## Fig 2 -- `fig02_smhr_ranking`

- **Files:** `paper_figures/fig02_smhr_ranking.pdf`, `.png`, `.csv`
- **Source result files:** `medvihall_outputs/layer2_judge.jsonl`; `medvihall_outputs/layer1_verdicts.jsonl`; medvihall_outputs/metrics_summary.json (cross-check); `medvihall_data/data/ground_truth/manifest_3500.json`
- **Script / function:** `figs_a.py:fig02` (run via `make_figures.py`)
- **Claim supported:** Medical specialists have higher SMHR than most general VLMs; neighbouring ranks are not always separable.
- **Draft caption:** SMHR of 12 VLMs on 3,500 images (11,750 responses per model); lower is safer, and medical specialists are shaded. Bars are 95% image-level bootstrap intervals (2,000 resamples, seed 42), and the right-hand column gives each model's 95% bootstrap rank range, so models with overlapping ranges are not ordered.
- **Size:** 3.40 x 3.00 in
- **Ranking caveat:** Adjacent models whose 95% CIs overlap (stratified bootstrap): qwen25vl~gemma3, gemma3~internvl3, internvl3~qwen35, qwen35~qwen3vl, idefics3~qwen2vl. Under the more conservative unstratified bootstrap: qwen25vl~gemma3, gemma3~internvl3, internvl3~qwen35, qwen35~qwen3vl, idefics3~qwen2vl. The paper should not claim a strict order inside these runs. Adjacent pairs whose PAIRED difference CI contains 0 (cannot be separated): qwen25vl vs gemma3 (diff 0.002 [-0.006, 0.011]); gemma3 vs internvl3 (diff 0.007 [-0.002, 0.016]); idefics3 vs qwen2vl (diff 0.007 [-0.001, 0.015]) 63 of 66 model pairs have a paired-difference CI that excludes 0.
- **Caveat (llava_med decoder):** 50% of core-run llava_med Q1 responses start mid-sentence; its core SMHR is 0.791 vs 0.728 with the fixed decoder on the same responses' keys. See figure_checks.md.

## Fig 3 -- `fig03_modality_fingerprints`

- **Files:** `paper_figures/fig03_modality_fingerprints.pdf`, `.png`, `.csv`
- **Source result files:** `medvihall_outputs/layer2_judge.jsonl`; `medvihall_outputs/layer1_verdicts.jsonl`; medvihall_outputs/metrics_summary.json (cross-check)
- **Script / function:** `figs_a.py:fig03` (run via `make_figures.py`)
- **Claim supported:** Hallucination burden depends on modality (radiology is hardest for most models) and is dominated by a few classes.
- **Draft caption:** (a) SMHR by model and modality (cell CIs in the source CSV). (b) Share of flagged hallucinations by class within each modality, pooled over the 12 models (353,625 flagged claims/omissions on 3,500 images). The thick line separates general VLMs (above) from medical specialists (below).
- **Size:** 7.00 x 3.10 in
- **Caveat (llava_med decoder):** 50% of core-run llava_med Q1 responses start mid-sentence; its core SMHR is 0.791 vs 0.728 with the fixed decoder on the same responses' keys. See figure_checks.md.

## Fig 4 -- `fig04_specialization_paradox`

- **Files:** `paper_figures/fig04_specialization_paradox.pdf`, `.png`, `.csv`
- **Source result files:** `medvihall_outputs/layer2_judge.jsonl`; `medvihall_outputs/layer1_verdicts.jsonl`; medvihall_outputs/metrics_summary.json (SRI cross-check, reference model)
- **Script / function:** `figs_a.py:fig04` (run via `make_figures.py`)
- **Claim supported:** Every medical specialist has SRI > 1 in every modality: it hallucinates more than the best general VLM (12/12 intervals exclude 1).
- **Draft caption:** Specialist Ratio Index (SRI) per medical specialist and modality; values above 1 mean the specialist hallucinates more than the best general VLM named under each modality. Bars are 95% image-level bootstrap intervals (2,000 resamples; reference model held fixed) over 3,500 images (1200, 900, 800, 600 per modality).
- **Size:** 3.40 x 2.90 in
- **Ranking caveat:** Within a modality the three specialists' SRI intervals overlap in several cells (see source CSV); do not rank specialists against each other from Fig 4.
- **Caveat (llava_med decoder):** 50% of core-run llava_med Q1 responses start mid-sentence; its core SMHR is 0.791 vs 0.728 with the fixed decoder on the same responses' keys. See figure_checks.md.

## Fig 5 -- `fig05_normal_image_paradox`

- **Files:** `paper_figures/fig05_normal_image_paradox.pdf`, `.png`, `.csv`
- **Source result files:** `medvihall_outputs/layer2_judge.jsonl`; `medvihall_outputs/layer1_verdicts.jsonl`; medvihall_data/data/ground_truth/manifest_3500.json (strata)
- **Script / function:** `figs_a.py:fig05` (run via `make_figures.py`)
- **Claim supported:** Whether normal images are hallucinated on more or less than abnormal ones depends on the modality; the Q4 counterfactual prompt changes SMHR on normal images.
- **Draft caption:** SMHR on normal strata (S1, DS1, HS1, OS1; filled) versus abnormal strata (open) for Q1-Q3 by modality (left four panels; 1,250 normal and 2,250 abnormal images), and on normal images for the false-premise Q4 counterfactual prompt versus Q1-Q3 (right). Bars are 95% image-level bootstrap intervals (2,000 resamples).
- **Size:** 7.00 x 3.35 in
- **Caveat (llava_med decoder):** 50% of core-run llava_med Q1 responses start mid-sentence; its core SMHR is 0.791 vs 0.728 with the fixed decoder on the same responses' keys. See figure_checks.md.

## Fig 6 -- `fig06_cross_modal_transfer`

- **Files:** `paper_figures/fig06_cross_modal_transfer.pdf`, `.png`, `.csv`
- **Source result files:** `medvihall_outputs/pillar_e_cross_modal_transfer.json`; medvihall_outputs/metrics_summary.json (rho recomputed)
- **Script / function:** `figs_b.py:fig06` (run via `make_figures.py`)
- **Claim supported:** A model's SMHR rank in one modality predicts its rank in the other modalities only partly; radiology transfers worst.
- **Draft caption:** Spearman correlation between the 12 models' SMHR rankings in each pair of modalities (n = 12 models; each SMHR from the full 3,500-image benchmark). Marks show p < 0.05 without (*) and with (†) Holm correction for six pairs; no confidence interval is drawn, so with n = 12 weaker correlations should be read as inconclusive.
- **Size:** 3.40 x 3.05 in

## Fig 7 -- `fig07_metric_concordance`

- **Files:** `paper_figures/fig07_metric_concordance.pdf`, `.png`, `.csv`
- **Source result files:** `medvihall_outputs/pillar_c_metric_concordance.json`; medvihall_outputs/metrics_summary.json (SMHR per cell)
- **Script / function:** `figs_b.py:fig07` (run via `make_figures.py`)
- **Claim supported:** SMHR agrees with MediHall Score and partly with CREST on model rankings; individual model-by-modality cells disagree.
- **Draft caption:** SMHR against (a) CREST and (b) MediHall Score for 12 models in 4 modalities (48 cells, 3,500 images; one marker per cell, marker shape identifies the model as in Fig. 2). Spearman ρ is shown for the 12 model-level values and for the 48 cells, numbered cells are the six largest standardised SMHR-versus-CREST disagreements (none exist for MediHall), and no confidence intervals are shown.
- **Size:** 7.00 x 3.20 in
- **Caveat (llava_med decoder):** 50% of core-run llava_med Q1 responses start mid-sentence; its core SMHR is 0.791 vs 0.728 with the fixed decoder on the same responses' keys. See figure_checks.md.

## Fig 8 -- `fig08_calibration`

- **Files:** `paper_figures/fig08_calibration.pdf`, `.png`, `.csv`
- **Source result files:** medvihall_outputs/pillar_d_calibration_results.json (ECE, ACE, CIs, rank_stability)
- **Script / function:** `figs_b.py:fig08` (run via `make_figures.py`)
- **Claim supported:** Verbalised-confidence calibration error is large for every model but its model ranking changes little across decoding settings.
- **Draft caption:** (a) Expected (ECE) and adaptive (ACE) calibration error of stated confidence for five models under six decoding configurations (strict correctness label; 699-1,495 labelled responses per cell from a 500-image subset); bars are 95% bootstrap CIs on ECE. (b) ECE rank of each model per configuration (mean pairwise Spearman ρ = 0.93, five models).
- **Size:** 7.00 x 2.90 in
- **Ranking caveat:** Greedy-decoding ECE, adjacent models in ECE order with overlapping 95% CIs: chexagent~llava16, qwen25vl~llava_med, llava_med~huatuogpt. The ranking among those models is not supported even though rank stability across configs is high.

## Fig 9 -- `fig09_mitigation`

- **Files:** `paper_figures/fig09_mitigation.pdf`, `.png`, `.csv`
- **Source result files:** medvihall_outputs/pillar_b_mitigation_results.json (paired_vs_baseline: delta, delta_ci95)
- **Script / function:** `figs_b.py:fig09` (run via `make_figures.py`)
- **Claim supported:** No strategy helps every model, and RAG raises SMHR for chexagent, huatuogpt, llava_med.
- **Draft caption:** Change in SMHR relative to the matched greedy baseline for retrieval-augmented generation and contrastive decoding (five models, 1,659-1,678 paired image-query responses on a 500-image subset). Bars are 95% paired image-level bootstrap intervals (2,000 resamples); red outlines mark strategies that increase SMHR (3 of 10 model-strategy cells, 1 with an interval excluding 0).
- **Size:** 3.40 x 2.75 in
- **Ranking caveat:** RAG and contrastive-decoding delta CIs overlap for: qwen25vl, huatuogpt, llava_med. "Best strategy per model" should only be claimed where the two intervals are separated (llava16, chexagent); paired-difference between strategies was not computed in the saved results.

## Fig 12 -- `fig12_annotation_agreement`

- **Files:** `paper_figures/fig12_annotation_agreement.pdf`, `.png`, `.csv`
- **Source result files:** `annotation_results/A3_flag_agreement_overall.csv`; `annotation_results/B1_judge_vs_human_per_class.csv`; `annotation_results/D3_annotator_agreement_with_majority_and_judge.csv`; medvihall_outputs/annotation/annotation_key.csv (item/image counts)
- **Script / function:** `figs_b.py:fig12` (run via `make_figures.py`)
- **Claim supported:** Simulated annotators agree moderately with each other on most hallucination classes, and the automatic judge agrees with their majority well only for fabrication.
- **Draft caption:** (a) Agreement per hallucination class among six simulated (AI-persona) annotators (Fleiss κ) and between the LLM judge and their majority label (Cohen κ), 720 items from 48 images. (b) Each annotator's mean κ with the majority of the other five; bars are 95% item-bootstrap intervals (2,000 resamples), which are optimistic because items share images, and no clinician annotations are included.
- **Size:** 7.00 x 3.00 in
- **Caveat (provenance):** annotators are AI personas, not clinicians; say so in the caption (the draft caption does).

## Tables

### T1_dataset_strata
- Files: `paper_tables/T1_dataset_strata.tex`, `paper_tables/T1_dataset_strata.csv`
- Source: `medvihall_data/data/ground_truth/manifest_3500.json`
- Function: `tables.py:t1`
- Supports: Dataset and strata counts.
- Draft caption: Benchmark composition: 3,500 images in 13 design strata. Normal strata receive four prompts (Q1--Q4), abnormal strata three (Q1--Q3).

### T2_models
- Files: `paper_tables/T2_models.tex`, `paper_tables/T2_models.csv`
- Source: `MedViHall_Phase3_Phase4_v4.ipynb (MODEL_REGISTRY: label, repo id)`; `medvihall_outputs/metrics_summary.json (is_medical)`; `models/MiniCPM-V-2_6/model.safetensors.index.json`
- Function: `tables.py:t2`
- Supports: Model list.
- Draft caption: The 12 evaluated VLMs, in the fixed presentation order (general models, then medical specialists).

### T3_main_results
- Files: `paper_tables/T3_main_results.tex`, `paper_tables/T3_main_results.csv`
- Source: `medvihall_outputs/layer2_judge.jsonl`; `medvihall_outputs/layer1_verdicts.jsonl`; `medvihall_outputs/metrics_summary.json (cross-check)`
- Function: `tables.py:t3`
- Supports: Main SMHR / CHR results.
- Draft caption: Core-run results for 12 VLMs on 3,500 images. Intervals are 95\% image-level bootstrap CIs (2,000 resamples, stratified by design stratum, seed 42); $^{\dagger}$ medical specialist. CHR = share of responses containing at least one fabrication or omission.

### T4_mitigation
- Files: `paper_tables/T4_mitigation.tex`, `paper_tables/T4_mitigation.csv`
- Source: `medvihall_outputs/pillar_b_mitigation_results.json`
- Function: `tables.py:t4`
- Supports: Mitigation deltas.
- Draft caption: Mitigation results on a 500-image subset (greedy decoding, paired image-query responses). $\Delta$ = strategy minus matched baseline with 95\% paired image-level bootstrap CI (2,000 resamples); $^{*}$ CI excludes 0, (up) = SMHR increased; $^{\dagger}$ medical specialist. Fine-tuning results are not available.

### T5_annotation_agreement
- Files: `paper_tables/T5_annotation_agreement.tex`, `paper_tables/T5_annotation_agreement.csv`
- Source: `annotation_results/A1_score_agreement_overall.csv`; `annotation_results/A3_flag_agreement_overall.csv`; `annotation_results/B1_judge_vs_human_per_class.csv`
- Function: `tables.py:t5`
- Supports: Annotation agreement (simulated annotators).
- Draft caption: Agreement among six \emph{simulated (AI-persona) annotators} on 720 items (48 distinct images), and between the LLM judge and the annotator majority. No clinician annotations are included. Intervals are 95\% item-level bootstrap CIs and are optimistic because items share images; $^{a}$ rare class, $\kappa$ unstable.

## Page budget and main/appendix split

Heights below are at the sizes set in `fig_style.py` (page text height 9.0 in; two single-column figures can sit side by side).

| Fig | Width x height (in) | Space | Placement | Why |
|---|---|---|---|---|
| 1 | 7.0 x 2.4 | 26% of a page (full width) | main | introduces the pipeline; no data |
| 2 | 3.4 x 3.0 | 33% of a column | main | headline ranking; the rank-range column makes the CI caveat visible |
| 3 | 7.0 x 3.1 | 34% of a page (full width) | main | modality dependence plus class composition in one figure |
| 4 | 3.4 x 2.9 | 32% of a column | main | the specialisation paradox is the central claim; all 12 SRI intervals sit above 1 |
| 5 | 7.0 x 3.4 | 37% of a page (full width) | appendix | direction of the normal-vs-abnormal gap is not uniform (ophthalmology: normal lower; others mixed); only the Q4 effect is clear, and it fits one sentence in the text |
| 6 | 3.4 x 3.0 | 34% of a column | appendix | 3 of 6 pairs significant, radiology transfers weakly; one sentence plus the appendix figure is enough |
| 7 | 7.0 x 3.2 | 36% of a page (full width) | appendix | MediHall agreement is near-definitional (rho = -1); CREST rho can be quoted in text |
| 8 | 7.0 x 2.9 | 32% of a page (full width) | appendix | calibration is a secondary pillar; quote ECE range and rank stability in text |
| 9 | 3.4 x 2.8 | 31% of a column | main | mitigation is a headline contribution, but note it covers 5 models on a 500-image subset and no fine-tuning arm |
| 10 | -- | -- | main (recommended) -- NOT AVAILABLE | no Pillar A result file exists |
| 11 | -- | -- | appendix -- NOT AVAILABLE | no Pillar H result file exists |
| 12 | 7.0 x 3.0 | 33% of a page (full width) | appendix | only valid if labelled as simulated annotators; must not be placed as clinician validation |

Main-paper figures made here (1, 2, 3, 4, 9) need about 1.1 pages (5.5 in of full-width figures plus 8.7 in of single-column figures that pair up). Your recommended main set (1, 2, 3, 4, 9, 10) holds, except that Fig 10 (Pillar A) cannot be made, so the main paper currently has five figures. To save space: place Fig 2 and Fig 4 side by side as one full-width strip, and keep 5-8 and 12 in the appendix.

