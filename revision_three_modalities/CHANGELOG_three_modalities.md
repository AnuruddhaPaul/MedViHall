# MedViHall: change log for the three-modality version

File: `main_revised.tex` (compiles to 48 pages with pdflatex + bibtex; `main_revised.pdf` is the build). Previous versions are kept as `main_revised_v1_backup.tex` and `main_revised_v2_before_three_modalities.tex`.

## 1. Scope
- Radiology removed from data, results, figures, tables, appendices and release statements. Benchmark: dermatology (900), histopathology (800), ophthalmology (600) = 2,300 images, 9 strata, 7,850 responses per model, 94,200 in total, 313,966 claims.
- One future-work paragraph on chest radiography (Section 8), with the reason stated.
- No Limitations section. Caveats remain in the body (Sections 3.4, 4, 5.6, 5.7, 6, 7).
- CheXagent: option (i). Kept in the model table and rankings, labelled out-of-domain; the specialisation claim is stated for HuatuoGPT-Vision and LLaVA-Med (six cells); CheXagent SRI reported separately.

## 2. Recomputed (no GPU; filtered data, one statistical configuration)
Bootstrap: 2,000 image-level resamples, stratified by design stratum, seed 42, paired. Permutation tests: 20,000, Holm. Spearman: 100,000 permutations, Fisher intervals.

| Quantity | Before | Now |
|---|---|---|
| Rank 1 | not reported | Qwen2.5-VL 0.428, first in every resample; Qwen3-VL 0.452; next three 0.473-0.486 not separated |
| Pairs separated | not reported | 64 of 66 |
| SRI, HuatuoGPT / LLaVA-Med | 1.31-1.85 in four modalities | 1.31-1.85 in three (six cells above 1); CheXagent 1.53-1.81 |
| Holm floor for SRI | 12/20,001 | 9/20,001 = 0.00045 (6 cells: 0.0003) |
| Modality extremes | radiology highest | histopathology highest (10 of 12), dermatology lowest (9 of 12) |
| Variance split model / modality / interaction | 38 / 48 / 14 % | 73 / 17 / 11 % (36 cells) |
| CHR range; rho(SMHR, CHR) | 0.00 | 0.614-0.743; 0.25 [-0.38, 0.72] |
| CHR-based SRI | contradicted SRI | 8 of 9 above 1; CheXagent in ophthalmology 0.89 (partial claim) |
| Cross-modality rho | not significant | 0.81, 0.77, 0.66; Holm over 3: 0.007, 0.009, 0.022 |
| "Three domain-adapted are the three worst" | held | false: CheXagent and LLaVA-Med have the two highest; HuatuoGPT is 8th. Replaced by a top-2 statement (0.96 / 0.53 / 0.44 in perturbation / random-order / Dirichlet draws) |
| Weights robustness | 89 % / 82 % | unchanged in statement; all nine SRI above 1 in every 30 % perturbation, min 1.12 |
| Mitigation subset | 500 images, 1,679 pairs | 328 images, 1,120 pairs per model |
| Decoding alone (LLaVA-1.6) | -0.046 | +0.005, not detectable; the apparent retrieval gain for LLaVA-1.6 vanishes against the greedy baseline |
| Mitigation | several effects | only HuatuoGPT contrastive decoding confirmed against both baselines; CHR up under retrieval for four of five models |
| Calibration | accuracy 12-28 %, confidence 52-91 % | accuracy 17-31 %, confidence 48-91 %; HuatuoGPT separated from LLaVA-Med (0.012-0.082) |
| Parse failures | 611 | 443 of 94,200 (0.5 %) |
| Pipeline-version disagreement | 11.3 % claims | 3.6 % claims / 1.7 % responses (664 responses); the old figure was mainly a radiology artefact |

## 3. Audit (Section 6) rewritten on 540 texts / 36 images
- Annotator agreement: ICC(2,1) 0.819-0.920; ICC(2,k) at least 0.965; Fleiss kappa fabrication 0.68, evasion 0.77, misclassification 0.56, severity 0.50, omission 0.36, reasoning 0.35, anatomical 0.39 (prevalence 2 %, unstable).
- Pipeline vs majority: any-hallucination F1 0.865 [0.841, 0.889]; flag-all rule 0.914 (higher); Cohen kappa 0.111. Fabrication kappa 0.33 (precision 0.71, recall 0.64); omission 0.09; misclassification 0.05; severity 0.13; evasion -0.08; reasoning 0.21.
- Item-level SMHR vs mean factual score: rho -0.32 [-0.40, -0.24] (n = 505); histopathology interval includes zero.
- Contribution 5 and the summary now say "fair agreement for fabrication, slight or none for the rest" (was "moderate").
- Removed: model-level correlation with five models (no recomputed value); "radiography F1 0.971".
- The radiology specialist persona is kept and described as an off-modality reader.

## 4. Text corrections not tied to radiology
- Abstract carries per-response SRI range and weight-draw robustness (C2).
- CRIMSON added to the aggregate-score sentence (B6); stale "could not be established" clause removed (B7).
- LLaVA-Med paragraphs merged; unsupported "SRI stays above 1" replaced by computed corrected SRI (B8).
- One bootstrap configuration stated (B9); Fig 6 uses permutation p (B10).
- CREST cell-stability and max_new_tokens claims removed (unverified).
- CREST author field in `ref.bib` set to "Guan and others"; missing `chapman2001simple` added; stub bibliography replaced by the real files merged and de-duplicated (105 entries).
- Floats set to `[tbp]` with relaxed fractions: Table 1 was never placed and pushed all tables to the end.
- Tables 2 (models) rebuilt: Omni tag dropped, precision column added, three type labels. Table 5 caption corrected to 540 items / 36 images. Appendix tables rebuilt for three modalities; coverage table and lexicon text without radiography; Table 14 now has a top-2 column.
- NOTE comments deleted; four `% OPEN:` comments remain (authors, two abstract-level references, release of control scripts). `\PH` macro removed.

## 5. Open items for you
1. Ethics sentence: `\TODO{state the position on ethical review}` is still in "Data availability and ethics".
2. Release: the repository was empty when the grader fetched it. Push before submission; the release must not contain radiology records; `human_annotations/` holds simulated annotations and must be labelled so.
3. Rotate or remove the hard-coded Hugging Face token (`HF_TOKEN`, cell 5) in `MedViHall_Phase3_Phase4_v4.ipynb` before the repository is public.
4. Reasons for the three planned models that were dropped (Aya-Vision-8B, LLaVA-Interleave-Qwen-7B, Gemma4:e4b) are not recorded; none is stated.
5. max_new_tokens limits are not stored in the result files; none is stated.
6. The old judge-rerun figures (195 / 11.3 %) could not be reproduced and were replaced by the recomputed numbers.
7. Not checked: REFUGE OS2/OS3 rule against the extraction script; lentigo/lichenoid mapping (disclosed in the Table 15 caption); arXiv IDs of 2026 preprints; text of Fig. 1 against the pipeline (the figure was regenerated and no longer claims 4-bit for all models).
8. Annotators are language-model personas; the text says so throughout.
