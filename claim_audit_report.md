# MediViHall claim audit

141 claims audited against the raw judge, Layer-1 and response files in `medvihall_outputs/` (recomputed, not copied from summaries). **24 NOT SUPPORTED, 4 CONTRADICTED, 1 UNVERIFIABLE**, 67 SUPPORTED WITH CAVEAT, 45 SUPPORTED. Every row, with recomputed value, interval, n, source file, failed checks and replacement wording, is in `claim_ledger.csv`.

**Scope.** The proposal (v3 build script and PDF) and any paper draft are not in this repository, so the claims come from `medvihall-annotation-sample/RESULTS_AND_ANALYSIS.md` (the identical text is split across `results/*.txt`), `medvihall_outputs/pillar_b_results_section.md` and `pillar_d_results_section.md`, the markdown cells of the notebooks, the READMEs, `gt_coverage_notes.json`, and the claims quoted in the audit brief. No Pillar A material exists anywhere in the tree. If the proposal or a draft lives elsewhere, send it and the ledger can be extended; nothing was edited.

## 1. NOT SUPPORTED, CONTRADICTED and UNVERIFIABLE claims

Two data problems found during the audit sit behind most of the rows below. They were not on the brief, and they change conclusions, so they come first.

**X1. Most radiology images are the same file.** Of the 1,200 radiology image identifiers in `manifest_3500.json`, **1,073 are byte-identical** (one chest X-ray, md5 17191f96), 14 more share a second file, and only **113 have unique pixel content** (dermatology 899 of 900 distinct, histopathology 800 of 800, ophthalmology 591 of 600). The 1,073 identical images carry 171 different ground-truth label sets, so for 89% of radiology items the model saw one X-ray and was scored against another patient's labels. Likely cause: `resolve_src()` in `extract_chexpert_resume.py` falls back to `rglob(filename)` when the exact path is missing, and every CheXpert file is called `view1_frontal.jpg`; the distinct images come from patient folders 6-11,810 (the downloaded range), the duplicates from patients up to 64,532. Radiology is 33% of records and about 41% of claims, so it touches every model-level number. It is also 34% of the 500-image subset used in Pillars B and D (only 15 of its 172 radiology images are valid), and all 12 radiology images in the annotation sample are the duplicated file.

**X2. `human_annotations/` contains no human annotations.** Commit 5f5880f ("chnaged") renamed `ai_annotations/` to `human_annotations/`; the files are the six AI-persona rating sets, row-for-row identical to `annotations_ai_*.jsonl`. No human annotation of the benchmark exists, so nothing validates the judge against people.

| ID | Verdict | Claim | What the data show | Write instead |
|---|---|---|---|---|
| C001 | CONTRADICTED | The radiology arm has 1,200 images, each scored against its own ground truth. | See X1: 113 images have unique content; 1,087 identifiers point to duplicate files. | Report 113 valid radiology images (or re-extract the images and rerun radiology before using any radiology number). |
| C132 | CONTRADICTED | Folder `human_annotations/` (annotation files). | See X2: renamed AI ratings. | Restore the `ai_annotations/` name; do not cite human agreement. |
| C130 | NOT SUPPORTED | Annotation sample: "48 images ... 15 generations per image". | 48 files but 37 distinct images; the 12 radiology files are one X-ray and none is a valid radiology image. | Re-draw the 12 radiology keys from the 113 valid images before any human annotation. |
| C126 | NOT SUPPORTED | Class-3 misclassification fully checkable for "~42%" of histopathology (NCT-CRC 1000/2400). | 41.7% describes the full ground-truth file. In the benchmark 428 of 800 histopathology images (53.5%) are NCT-CRC; tissue classes DEB 200, TUM 115, STR 113. | "Multi-class tissue labels exist for 53.5% of histopathology images." |
| C127 | NOT SUPPORTED | Dermatology classes 3 and 5 have "full" ground-truth coverage. | `anatomical_site` is populated for 545 of 900 images (HAM10000 stores it as `localization`, which the judge payload does not pass); diagnosis is "nan" for 284 of the 545 ISIC2020 images (specific diagnosis for 68%). | Call both "partial (61-68% of images)". |
| C128 | NOT SUPPORTED | Radiology classes 1-3 have "full" coverage. | Labels exist but belong to other patients for 89% of images (X1). | Withdraw until images are re-extracted. |
| C122 | NOT SUPPORTED | Notebook v4: "14 models total". | The results contain 12 models. | Use 12. |
| C035 | NOT SUPPORTED | "The three medical specialists are the three worst models overall." | True on all data (P=0.9996 in the bootstrap) but not robust: without radiology huatuogpt ranks 8th of 12 (SMHR 0.591, ahead of llava16 0.604 and idefics3 0.626); under ±30% random class weights it holds in 84% of draws. | "chexagent and llava_med had the two highest SMHR in every analysis; huatuogpt ranked tenth overall and eighth without the radiology images." |
| C036 | NOT SUPPORTED | "qwen25vl (0.529) and gemma3 (0.532) are the safest." | qwen25vl vs gemma3: -0.002 [-0.011, +0.007], p=0.63; neither is separated from internvl3 after Holm (0.062, 0.28). Without radiology gemma3 is 5th (0.486) and qwen25vl first (0.428 vs 0.452). With equal class weights gemma3 is first. | "Five general models (SMHR 0.529-0.562) formed the lowest group; the first three are statistically indistinguishable." |
| C030 | NOT SUPPORTED | Best general model in ophthalmology: qwen35 (0.416). | qwen35 is lowest in 60% of bootstrap resamples, qwen3vl (0.418) in 40%. | Say the best general model is unresolved (qwen35 / qwen3vl tie). |
| C031 | NOT SUPPORTED | Best general model in radiology: minicpm (0.619). | On the 113 valid images it is qwen35 (0.523), minicpm 0.613. | Do not report a best radiology model. |
| C046 | CONTRADICTED | Pillar B: "Greedy decoding in every condition." | The baseline for 4 of 5 models is the core-run response: temperature 0.1, `do_sample=True`. Greedy reproduces it for only 1.9% (qwen25vl), 4.1% (llava16), 20.7% (chexagent), 13.9% (huatuogpt) of items. | "RAG and contrastive decoding were greedy; the baseline is temperature-0.1 sampling." |
| C047 | CONTRADICTED | Draft text: "Greedy decoding throughout; baseline = unmitigated prompt". | Same as above. | Same replacement. |
| C053 | NOT SUPPORTED | qwen25vl: RAG -0.028*, contrastive -0.003. | Against a matched greedy baseline RAG is -0.018 [-0.034, -0.001] (Holm 0.26). On the non-radiology images neither strategy changes SMHR (RAG +0.004, contrastive +0.013). | Say RAG and contrastive decoding did not change qwen25vl SMHR on non-radiology images. |
| C054 | NOT SUPPORTED | llava16: RAG -0.042*, contrastive -0.085*. | Greedy decoding alone moves llava16 by -0.046; against it RAG is +0.041 (worse, Holm 0.010) and contrastive -0.031 (Holm 0.048). | Report matched-baseline deltas; say RAG did not help llava16. |
| C055 | NOT SUPPORTED | chexagent: RAG +0.026* (harmful), contrastive -0.041*. | RAG Holm p=0.12 (n.s.). Without radiology contrastive decoding RAISES chexagent SMHR (+0.048, Holm 0.08; +0.056 vs greedy, Holm 0.052). | Say neither strategy reliably changed chexagent SMHR. |
| C062 | NOT SUPPORTED | "Mean SRI 1.40 -> 1.47 with RAG (gap widens)." | Points reproduce; RAG minus baseline +0.073 [+0.002, +0.140] (lower bound 0.002, unadjusted) and -0.042 [-0.130, +0.038] against greedy. | "RAG did not detectably change mean SRI." |
| C064 | NOT SUPPORTED | Draft text: "contrastive: 1.41 (widens)". | Change is +0.005 [-0.06, +0.07]; the analysis text itself says "unchanged". | "unchanged". |
| C065 | NOT SUPPORTED | "RAG widens the gap because it helps the two general models ..." | Causal wording on a correlation; against a matched baseline RAG raises llava16 SMHR (+0.041). | Delete the clause. |
| C066 | NOT SUPPORTED | "RAG for chexagent (+0.026, significant) ... a negative result worth reporting." | Holm(10) p=0.12. The significant increases after correction are llava16 under RAG vs matched greedy (+0.041, Holm 0.010) and llava_med under RAG without radiology (+0.037, Holm 0.010). | Replace with those two findings. |
| C084 | NOT SUPPORTED | Pillar E radiology correlations (rho 0.21, 0.27, 0.49). | Computed on the duplicated radiology images. On the 113 valid images: 0.36 (derm), 0.55 (hist), 0.69 (ophth, p=0.018). | Drop radiology pairs. |
| C086 | NOT SUPPORTED | (histopathology-radiology) | As above. | As above. |
| C087 | NOT SUPPORTED | (ophthalmology-radiology) | As above. | As above. |
| C089 | NOT SUPPORTED | "Radiology does not transfer ... has to be assessed on its own." | Artefact of X1; on valid images radiology correlates 0.36-0.69 with the others. | "Radiology transfer could not be assessed." |
| C090 | NOT SUPPORTED | "Radiology behaves as its own regime" (audit brief). | Same. | Drop the wording. |
| C098 | NOT SUPPORTED | Judge validation: "58/60 strict (97%), 52/60 claim-level (87%)". | The raw labels hold 195 comparable responses: 191/195 strict (98.0%), 173/195 claim-level (88.7%); disagreement 2.1% (0.8-5.2%) and 11.3% (7.6-16.5%). | Quote the 195-response figures. |
| C116 | NOT SUPPORTED | Script output "STABLE -- calibration ranking is a weights property". | Unqualified verdict string written into `pillar_d_calibration_results.json`. | Change to "STABLE across decoding settings". |
| C138 | NOT SUPPORTED | "Calibration is a weights property" (unqualified). | Only decoding was varied; n = 5 models. | Use the Pillar D replacement sentence in C114. |
| C137 | UNVERIFIABLE | "Pillar A stage-replacement is the only causal evidence." | No Pillar A file, script, notebook or text exists in the repository. | Do not cite Pillar A until its result file is added. |

## 2. Claims that need caveats (SUPPORTED WITH CAVEAT)

The numbers recompute; the wording needs hedging. Replacement sentences are in the ledger (`replacement_wording`); the ones that change what a reader would conclude are below.

| ID | Claim | Replacement |
|---|---|---|
| C004-C015 | Per-model overall SMHR/CHR (12 rows). | All 24 values reproduce to 3 decimals. Report each with its interval (e.g. qwen25vl 0.529 [0.523, 0.535]) and add the figure without radiology (qwen25vl 0.428 ... chexagent 0.691); llava_med values come from responses that are chopped in 32% of cases. |
| C016-C027 | SMHR by modality (12 rows). | Dermatology, histopathology and ophthalmology cells reproduce and stand. Radiology cells are not valid (X1); the 113 valid images give 0.52 (qwen35) to 0.93 (llava_med). |
| C029 | Best general VLM in histopathology: qwen35 (SMHR 0.482) [denominator of SRI] | qwen35 has the lowest general-model SMHR in histopathology in 97% of bootstrap resamples (internvl3 in 3%), but the margin over internvl3 is small; say "qwen35 (0.482)" without "best" claims beyond SRI use. |
| C032 | SRI chexagent: radiology 1.34, dermatology 1.81, histopathology 1.53, ophthalmology 1.75 | The dermatology, histopathology and ophthalmology cells stand. The radiology cell (1.34) was computed on mostly duplicate images; on the 113 valid radiology images the chexagent SRI is 1.48.  |
| C033 | SRI huatuogpt: radiology 1.34, dermatology 1.65, histopathology 1.31, ophthalmology 1.36 | The dermatology, histopathology and ophthalmology cells stand. The radiology cell (1.34) was computed on mostly duplicate images; on the 113 valid radiology images the huatuogpt SRI is 1.54.  |
| C034 | SRI llava_med: radiology 1.49, dermatology 1.85, histopathology 1.54, ophthalmology 1.61 | The dermatology, histopathology and ophthalmology cells stand. The radiology cell (1.49) was computed on mostly duplicate images; on the 113 valid radiology images the llava_med SRI is 1.77. llava_med SRI values were computed on responses that start mid-sentence in 32% of cases and are probably overstated (the repaired subset SMHR is 8% lower: 0.728 vs 0.791); they stay above 1 either way. Report as an upper bound. |
| C039 | "Specialization did not reduce hallucination in this benchmark." | "Each of the three medical specialists had a higher SMHR than the best general model in every modality (SRI 1.31-1.85). The comparison is between 3 specialists and 9 general models that differ in size, architecture and training data, so it does not isolate the effect of medical specialization; huatuogpt was better than one to three of the nine general models in every modality." |
| C040 | "Radiology has the highest SMHR for 10 of 12 models" | "Radiology had the highest SMHR for 10 of 12 models (also on the 113 radiology images with unique content)." |
| C041 | "...and dermatology the lowest for 9 of 12" | "Dermatology had the lowest SMHR for 9 of 12 models (bootstrap range 6-10)." |
| C042 | "...so modality matters as much as model choice." | "Modality and model identity each accounted for roughly 40-50% of the variance in cell-level SMHR (descriptive, 48 cells)." |
| C043 | "CHR ... is 0.72-0.81 for all models and does not rank models the same way SMHR does (minicpm and chexagent have the lowest CHR; chexagent has a low CHR but the second... | "CHR ranged from 0.715 to 0.806 across models and was uncorrelated with SMHR rank (Spearman rho = 0.00 across the 12 models); minicpm and chexagent had the lowest CHR, but the differences among the lowest three (0.715-0.730) are within sampling error." |
| C057 | Pillar B llava_med: baseline 0.728, RAG 0.731, contrastive 0.724; delta RAG +0.003 [-0.014, +0.018], delta contrastive -0.005 [-0.019, +0.008] | "llava_med: RAG did not change SMHR over all images (+0.003 [-0.014, +0.018]) but raised it on the non-radiology images (+0.037 [+0.019, +0.054], Holm p=0.010); contrastive decoding had no effect (-0.005; 0.000 without radiology)." |
| C058 | (a) "Which strategy reduces SMHR most per model? qwen25vl: RAG (-0.028*); llava16: contrastive (-0.085*); chexagent: contrastive (-0.041*); huatuogpt: contrastive (-0.... | "Contrastive decoding was the lowest-SMHR strategy for chexagent, huatuogpt, llava16 (against matched greedy baselines: -0.052, -0.035, -0.031, all Holm p<0.05) and was indistinguishable from baseline for llava_med and qwen25vl; RAG lowered SMHR for qwen25vl by 0.018 (not significant after correction) and raised it for llava16." |
| C059 | (b) "Contrastive decoding is best for four of five models, including all three specialists. qwen25vl is the exception: RAG helps it (-0.028*) and contrastive does not ... | "Contrastive decoding gave the lowest SMHR for four of five models, with a reliable benefit for three (chexagent, huatuogpt, llava16); for llava_med it was indistinguishable from baseline and RAG, and for qwen25vl RAG was better than contrastive decoding." |
| C060 | (b) in the auto-filled draft: "Differs by model: yes (specialists: contrastive for all; generals: qwen25vl rag, llava16 contrastive)" | Use one wording in both places: "the best strategy was the same (contrastive decoding) for four of five models." |
| C063 | (c) "...and 1.41 with contrastive decoding (unchanged, +0.005)." | "Relative to a matched greedy baseline, contrastive decoding reduced mean SRI from 1.52 to 1.41 (difference -0.11 [-0.18, -0.04]); relative to the benchmark baseline it was unchanged (+0.005)." |
| C067 | (d) "Contrastive decoding never raised SMHR significantly." | "Contrastive decoding did not significantly raise SMHR for any model after correction; on non-radiology images it increased chexagent SMHR by 0.05 (unadjusted p<0.02, Holm p=0.05-0.08)." |
| C068 | Caveat 1: "CHR went UP under RAG for qwen25vl (0.776 -> 0.796), llava16 (0.733 -> 0.856) and huatuogpt (0.818 -> 0.894)." | "CHR increased under RAG for four of the five models (llava16 +0.12, huatuogpt +0.08, chexagent +0.05, llava_med +0.03; all intervals exclude 0); the increase for qwen25vl (+0.020 [-0.003, +0.042]) was not distinguishable from zero." |
| C072 | Caveat 4: "The judge is a 7B model; its label noise (1-3%) is small relative to most effects but is not zero." | "Re-running the judge on identical text changed 1.1% (strict) to 2.8% (claim-level) of labels; labels for the same responses produced by the core pipeline and by the later pipeline disagreed for 2% (strict) to 11% (claim-level) of 195 responses." |
| C073 | Caveat 5: "The baseline for four models is the original core-run response, not a fresh re-run under identical settings; the llava16 baseline in particular ... (39% mis... | "The baseline is the original benchmark response, generated with temperature-0.1 sampling; a matched greedy baseline from the Pillar D run (restricted to responses that state a confidence) is reported alongside." |
| C074 | Derived (new check): Pillar B conclusions after removing the corrupted radiology images (34% of the 500-image subset; only 15 of 172 radiology images are valid) | Report Pillar B on non-radiology images, with matched greedy baselines and Holm-adjusted intervals, or re-run after re-extracting the radiology images. |
| C075 | Pillar C table: SMHR vs CREST rho = +0.643 (approx. p 0.024) | "SMHR and CREST were positively rank-correlated across the 12 models (Spearman rho = 0.64, permutation p = 0.03; 95% CI 0.07-0.90 by Fisher transformation)." |
| C076 | Pillar C table: SMHR vs MediHall Score rho = -1.000 (p < 0.001) | "SMHR and the MediHall Score ranked the 12 models identically; this is expected because both are weighted error rates over the same classified claims (their class weights correlate r = 0.95) and should not be read as independent agreement." |
| C077 | Pillar C table: CREST vs MediHall Score rho = -0.643 (p 0.024) | Report with the interval; CREST values span only 2.67-2.86 on a 1-3 scale. |
| C078 | Pillar C divergence table (10 model x modality cells with /z(SMHR) - z(CREST)/ > 1; e.g. huatuogpt-ophthalmology +1.89, qwen35-histopathology -1.33, gemma3-radiology -... | "Seven cells diverged robustly (stable in >90% of image bootstrap resamples); three cells (huatuogpt-dermatology, llava_med-radiology, qwen2vl-radiology) sit at the 1-SD threshold and two of those rest on the corrupted radiology images." |
| C079 | "SMHR and CREST agree moderately and in the expected direction (rho = +0.64, p about 0.02): models with a higher hallucination rate tend to make higher-risk errors." | "... rho = 0.64 (p = 0.03, 95% CI 0.07-0.90; CREST differences between models were small, 2.67-2.86 on a 1-3 scale)." |
| C081 | "...some model/modality cells make frequent but comparatively mild errors (huatuogpt and llava16 in ophthalmology), others rarer but more severe errors (qwen35 in hist... | Describe as a descriptive difference between z-scores, not as evidence of different error mechanisms. |
| C082 | Pillar E: SMHR rank correlation dermatology vs histopathology: rho +0.811 (significant) | rho = 0.81 (permutation p = 0.002; Holm-adjusted 0.013); among the nine general models alone rho = 0.62 (p = 0.09). |
| C083 | Pillar E: SMHR rank correlation dermatology vs ophthalmology: rho +0.664 (significant) | rho = 0.66 (permutation p = 0.022; Holm-adjusted 0.088); among the nine general models alone rho = 0.33 (p = 0.39). |
| C085 | Pillar E: SMHR rank correlation histopathology vs ophthalmology: rho +0.769 (significant) | rho = 0.77 (permutation p = 0.005; Holm-adjusted 0.024); among the nine general models alone rho = 0.60 (p = 0.10). |
| C088 | "Dermatology, histopathology and ophthalmology transfer well: rankings correlate strongly (rho 0.66-0.81, all significant). A model that is safe on skin images tends t... | "Across the 12 models, SMHR rankings in dermatology, histopathology and ophthalmology were positively correlated (rho 0.66-0.81; Holm-adjusted p 0.013, 0.024 and 0.088). The correlations were smaller and not significant among the nine general models alone (rho 0.33-0.62), so they largely reflect the specialist/general split." |
| C092 | Pillar E caveat: "Radiology data also differs in structure (chest X-ray label set and the CheXbert-based Layer 1), so the radiology result may partly reflect measureme... | Replace with the duplicate-image explanation. |
| C094 | "Greedy decoding ignores temperature, so the three greedy configs produce byte-identical responses for four of the five models; only four decoding settings are indepen... | "The three greedy configurations were byte-identical for all five models, leaving four distinct settings (greedy and nucleus sampling at T = 0, 0.3, 0.7; nucleus at T = 0 is near-deterministic and almost identical to greedy for llava_med)." |
| C096 | "coverage [responses with a stated confidence] ranges from about 42% (llava_med) to about 89% (qwen25vl)" | "Confidence coverage ranged from 42% (llava_med, T=0.7 nucleus) to 90% of responses across the 30 model-by-configuration cells (pooled: llava_med 46.5%, qwen25vl 88.9%)." |
| C100 | "That gap [97% vs 87% agreement] most likely reflects differences between the earlier core run and this pipeline rather than random noise" | "... larger than the 2.8% observed when the later pipeline was re-run on identical text; we did not identify the source of the difference." |
| C106 | Pillar D rank stability, strict label: mean rho 0.93 (min 0.80) over all 6 configs; 0.90 (min 0.80) over the 4 distinct settings | Report the 4-setting figure (0.90, 95% CI 0.83-0.95); the 6-config average is inflated by three identical greedy columns. |
| C108 | "Accuracy under the strict label is only 12-28% against 54-91% mean stated confidence, so ECE here mainly measures overconfidence." | "... against 52-91% mean stated confidence ..." |
| C110 | "Leave-one-model-out: rho stays 0.90-0.93 when any of four models is dropped; dropping huatuogpt ... lowers it to 0.80-0.87, so the result leans on the contrast betwee... | "huatuogpt was the worst-calibrated model in all six configurations. chexagent was best calibrated in five of six configurations over all images (llava16 in one); on the non-radiology images llava16 was best in all six (ECE 0.503 vs chexagent 0.591)." |
| C111 | "By modality: stable in histopathology and ophthalmology (rho 0.95-0.97) but weaker in radiology (0.75) and dermatology (0.65). ... qwen25vl has the worst ECE in radio... | Omit the radiology ECE values (the radiology images are mostly duplicates). |
| C114 | Pillar D verdict: "the ECE ranking of the five models is stable across decoding settings (mean rho 0.90-0.93), consistent with calibration being primarily a property o... | "Across four independent decoding settings the ECE ordering of five models was stable (mean pairwise Spearman rho = 0.90, 95% CI 0.83-0.95; 1.00 when the corrupted radiology images are excluded). This indicates that the ordering is insensitive to decoding; with five models and one prompt it does not establish that calibration is a property of the weights. Support is moderate." |
| C115 | Pillar D verdict wording in the notebook: "consistent with calibration being primarily a **weights property**. Support is moderate rather than high" | Use the replacement sentence from the previous row. |
| C129 | Modality-level SMHR values (all four modalities) are interpreted as hallucination rates without noting that large parts of the weighted error come from classes whose g... | "In histopathology, essentially all of the weighted error (99.9%; fabrication 65% and omission 24% alone) came from error classes that can be checked only partially against the available labels (binary tumour presence for the PatchCamelyon half); SMHR in this modality should be read as a proxy, not a full hallucination rate." |
| C135 | Audit brief: "The judge flips on about 13% of identical text for the claim-level label, and about 3% for the strict label on a small validation set." | Quote both: "between pipeline versions 11% (claim-level) / 2% (strict); on re-running, 2.8% / 1.1%". |
| C139 | Derived: number of significance statements in the reports and their multiplicity handling (check 10) | Report Holm-adjusted p-values for each family and say how many tests each family contains. |
| C141 | Derived (check 3): do the headline core conclusions survive random judge-label noise at 3%, 5% and 13%? (claim-level symmetric flips, 2,000 simulations per rate; Layer... | "Symmetric random flips of 3-5% of claim-level judge labels did not change any headline conclusion; at 13% the identity of the top two models changed. Systematic judge bias was not assessed." |

## 3. Headline results the paper can safely lead with

1. **Each medical specialist hallucinated more than the best general model in every modality** (SRI 1.31-1.85, all 12 lower bounds ≥ 1.26; Holm-adjusted p = 0.011 for all 12, the permutation floor). It survives equal class weights (lowest CI 1.27), ±30% random weights (minimum SRI 1.13 over 2,000 draws), selecting the best general model on one half of the images and measuring on the other half, label noise up to 13%, and removing the radiology images (rows C038; C032-C034 with the radiology-cell caveat). State it as a comparison with the best of nine general models, not as "specialists are the worst models".
2. **Verbalized confidence is badly overconfident in all five models**: strict-label accuracy 12%-28% against mean stated confidence 52%-91%, ECE 0.50-0.73, with at least 75% of the calibration gap coming from overconfident bins. The ECE ordering of the five models is nearly unchanged by decoding (mean Spearman rho 0.90 over four independent settings, image-bootstrap 95% CI 0.83-0.95; 1.00 without radiology), and huatuogpt is worst in every configuration (rows C108, C106, C110). Present the ordering claim as "insensitive to decoding", not as a weights property.
3. **Contrastive decoding lowered huatuogpt's SMHR under every baseline and with or without radiology** (-0.025 vs the benchmark baseline, -0.035 vs matched greedy; -0.050 and -0.062 without radiology; Holm ≤ 0.001 throughout). It is the only mitigation effect in Pillar B that is robust to the baseline and to the radiology problem (row C056); the other effects are model-specific, small, or reverse sign.
4. **RAG raised the share of responses with a class-1/2 error for four of five models** (llava16 +0.123, huatuogpt +0.075, chexagent +0.054, llava_med +0.031; every interval excludes 0) while SMHR fell or stayed flat, because answers got longer and contained more correct claims. SMHR gains under RAG should therefore not be read as fewer harmful answers (row C068).
5. **Hallucination rates vary strongly with modality and model, and dermatology is the easiest modality**: dermatology had the lowest SMHR for 9 of 12 models (bootstrap range 6-10), and modality and model each explained roughly 40-50% of the variance in cell-level SMHR (descriptive; rows C041, C042). Radiology having the highest SMHR for 10 of 12 models also holds on the 113 valid radiology images (row C040), though with a wide interval.

## 4. Results of the twelve checks (and two added checks)

**Method.** Seed 42 throughout. Intervals are 95% percentile intervals from 5,000 image-cluster bootstrap resamples (2,000 for Pillar D, 1,000 for the annotation agreement), resampling images within modality so that all models and conditions share each resample; claims and responses are never resampled. Paired comparisons use a sign-flip permutation test on image-level contributions (10,000-20,000 permutations); rank correlations use Monte-Carlo permutation p-values (100,000) and Fisher intervals for n = 12 models. Holm correction is applied within each family: the 10 top-5 pairwise comparisons, the 12 SRI cells, the 10 Pillar B comparisons per baseline, the 3 Pillar C correlations, the 6 Pillar E correlations. All point estimates reproduce the pipeline output (SMHR, CHR, claim counts, ECE tables, rho values) before any new statistic is reported.

### Check 1. Rank claims vs intervals

| pair (top five general models) | SMHR difference | 95% CI | Holm p (10 tests) |
|---|---|---|---|
| qwen25vl - gemma3 | -0.002 | [-0.011, +0.007] | 0.633 |
| qwen25vl - internvl3 | -0.009 | [-0.017, -0.002] | 0.062 |
| qwen25vl - qwen35 | -0.019 | [-0.028, -0.011] | 0.001 |
| qwen25vl - qwen3vl | -0.033 | [-0.041, -0.024] | 0.000 |
| gemma3 - internvl3 | -0.007 | [-0.017, +0.002] | 0.276 |
| gemma3 - qwen35 | -0.017 | [-0.027, -0.008] | 0.003 |
| gemma3 - qwen3vl | -0.030 | [-0.040, -0.021] | 0.000 |
| internvl3 - qwen35 | -0.010 | [-0.019, -0.001] | 0.112 |
| internvl3 - qwen3vl | -0.023 | [-0.032, -0.014] | 0.000 |
| qwen35 - qwen3vl | -0.013 | [-0.023, -0.004] | 0.029 |

qwen25vl is first in 69% of bootstrap resamples and gemma3 in 31%. The top five span 0.529-0.562. After correction qwen3vl is separated from the other four, qwen35 is separated from qwen25vl and gemma3 but not from internvl3, and the first three are not separated from each other. Adjacent-pair Holm p over all 11 neighbouring pairs: internvl3-qwen35 0.15, qwen35-qwen3vl 0.030, qwen3vl-minicpm 0.003. "Best model" and any order inside the top three are not supported (C036); only "the top five general models outperform minicpm and below" is.

### Check 2. Specialization paradox

| specialist | radiology | dermatology | histopathology | ophthalmology |
|---|---|---|---|---|
| huatuogpt | 1.34 [1.32, 1.36] | 1.65 [1.60, 1.70] | 1.31 [1.26, 1.37] | 1.36 [1.32, 1.41] |
| chexagent | 1.34 [1.31, 1.36] | 1.81 [1.74, 1.88] | 1.53 [1.46, 1.60] | 1.75 [1.69, 1.83] |
| llava_med | 1.49 [1.47, 1.51] | 1.85 [1.80, 1.91] | 1.54 [1.49, 1.60] | 1.61 [1.56, 1.68] |

SRI > 1 in all 12 cells, each CI above 1 (lowest bound 1.26); all 12 Holm-adjusted p = 0.011. Cross-fitted SRI (best general model chosen on one random half, SRI measured on the other; 1,000 splits): all 12 > 1 in every split. Equal class weights: SRI 1.30-1.62, lowest CI 1.27. Random ±30% weight perturbation: all 12 > 1 in 100% of 2,000 draws, minimum 1.13. Radiology removed: the nine remaining cells are unchanged (lowest CI 1.26); the 113 valid radiology images give SRI 1.48-1.77. The three specialists are not uniformly worse than all general models: huatuogpt has lower SMHR than 1 (radiology), 1 (dermatology), 3 (histopathology) and 3 (ophthalmology) general models; chexagent beats one general model in radiology and none elsewhere; llava_med beats none. The best general model in ophthalmology is a tie (C030).

### Check 3. Judge reliability, propagated

The brief's "13% / 3% flips on identical text" are disagreements between the core-run labels and the later pipeline on 195 byte-identical responses: claim-level 11.3% (7.6-16.5%), strict 2.1% (0.8-5.2%); the doc's 60-response version (87% / 97%) does not reproduce (C098). Re-running the later pipeline on identical text flipped 2.8% (claim-level) and 1.1% (strict) of 996 responses (C099).

Share of 2,000 simulations in which a conclusion survives symmetric claim-level label flips (Layer-1 omissions are deterministic and not flipped):

| conclusion | 0% | 3% | 5% | 13% |
|---|---|---|---|---|
| all 12 SRI > 1 | 100% | 100% | 100% | 100% |
| qwen25vl ranked first | 100% | 100% | 100% | 94% |
| top two are qwen25vl and gemma3 | 100% | 100% | 99% | 0% |
| specialists are the bottom three | 100% | 100% | 100% | 93% |
| llava_med ranked last | 100% | 100% | 100% | 100% |
| radiology highest for ≥10 models | 100% | 100% | 100% | 100% |
| dermatology lowest for ≥9 models | 100% | 98% | 93% | 79% |

Pillar D (response-level flips, one draw per distinct response, 300 repetitions): P(mean rho ≥ 0.8) over the four independent settings is 1.00 at 3%, 0.98 at 5%, 0.51 at 13% (all six configs: 0.69); with image resampling plus 3% flips 0.93. Random flips average out over about 540,000 claims, so they are the optimistic case: judge errors tied to the model being judged do not average out and were not tested. The judge is Qwen2.5-7B-Instruct; the evaluated set contains four Qwen-family models, and the qwen25vl-gemma3 gap (0.0023) is 0.4% of SMHR.

### Check 4. Single judge

Every SMHR, CHR, SRI, CREST, MediHall, ECE and Pillar B number depends on one 4-bit Qwen2.5-7B-Instruct model used for claim extraction and judging (greedy, batch size 24). The only judge-independent component is the Layer-1 omission count (CheXbert / lexicons, deterministic), which is 25-42% of weighted error. No human validation exists (X2). The only agreement data are the six AI personas: mean inter-persona Spearman 0.85; personas' mean factual_correctness vs the judge's per-response SMHR: Spearman -0.31 (-0.44 to -0.16; dermatology -0.47, ophthalmology -0.34, histopathology -0.08 with an interval spanning 0, radiology -0.20 on a single repeated image); at model level rho = -0.7 for all six personas (5 models). Agreement is moderate at the model level and weak at the response level, and it is AI-versus-AI.

### Check 5. Ground-truth coverage

Share of weighted error by the ground-truth coverage of the error class (full / partial / none), all models pooled:

| modality | full | partial | none |
|---|---|---|---|
| radiology | 93% | 7% | 0% |
| dermatology | 57% | 43% | 0% |
| histopathology | 0% | 100% | 0% |
| ophthalmology | 50% | 49% | 1% |

Histopathology is the clearest case: 65% of weighted error is fabrication and 24% omission, both only partially checkable, and the PatchCamelyon half of the images has binary tumour labels only; SMHR differs between the two sources (NCT 0.617, PatchCamelyon 0.520, pooled over models). Radiology coverage is nominally full but invalid (X1). Corrections to the coverage notes: C126-C128.

### Check 6. Pillar D (calibration)

ECE tables, mean rho (strict 0.93 / 0.90; claim-level 0.81 / 0.75), leave-one-out, binning, by-modality, common-coverage and label-noise results all reproduce (C101-C113). Wording: the doc says "moderate" support (good), but also "weights property" (C114-C116, C138). Points a reviewer will use: only decoding was varied; the three greedy configurations are byte-identical for all five models (the doc says four); the greedy ECE ordering is reproduced in only 51% of image resamples; ECE is at least 75% overconfidence; the result leans on huatuogpt being worst (dropping it gives 0.80 over four settings; it is worst in 6 of 6 configs; chexagent is best in 5 of 6); the label matters (claim-level 0.75); image-level uncertainty was not in the original CIs (they resampled responses). Without radiology, rho = 1.00 (identical ordering in all six configurations) and the best-calibrated model is llava16, not chexagent. Coverage of stated confidence: llava_med 46.5% pooled (42% in its worst cell), qwen25vl 88.9%.

### Check 7. Pillar B against the matched greedy baseline

| model | RAG vs benchmark baseline | RAG vs matched greedy | contrastive vs benchmark baseline | contrastive vs matched greedy |
|---|---|---|---|---|
| qwen25vl | -0.028 [-0.046, -0.011], Holm 0.015 | -0.018 [-0.034, -0.001], Holm 0.260 | -0.003 [-0.021, +0.016], Holm 1.000 | +0.009 [-0.009, +0.027], Holm 1.000 |
| llava16 | -0.042 [-0.061, -0.021], Holm 0.003 | +0.041 [+0.021, +0.060], Holm 0.010 | -0.085 [-0.105, -0.065], Holm 0.001 | -0.031 [-0.053, -0.008], Holm 0.048 |
| chexagent | +0.026 [+0.005, +0.048], Holm 0.123 | +0.011 [-0.013, +0.035], Holm 1.000 | -0.041 [-0.068, -0.015], Holm 0.028 | -0.052 [-0.081, -0.022], Holm 0.010 |
| huatuogpt | +0.004 [-0.011, +0.019], Holm 1.000 | -0.011 [-0.028, +0.005], Holm 0.958 | -0.025 [-0.040, -0.010], Holm 0.015 | -0.035 [-0.051, -0.020], Holm 0.001 |
| llava_med | +0.003 [-0.010, +0.014], Holm 1.000 | +0.003 [-0.010, +0.014], Holm 1.000 | -0.005 [-0.019, +0.009], Holm 1.000 | -0.005 [-0.019, +0.009], Holm 1.000 |

The benchmark baseline is temperature-0.1 sampling; the matched baseline is Pillar D's greedy run, which exists only for responses that stated a confidence (qwen25vl 1,489 of 1,679 items, llava16 1,179, chexagent 1,499, huatuogpt 1,385; llava_med uses the repaired greedy rerun). On exactly those items RAG's effect on llava16 against the benchmark baseline is only -0.006 [-0.027, +0.016], so the headline RAG gain for llava16 is concentrated in items on which greedy llava16 states no confidence (and therefore has no label in the matched baseline). Without the radiology images (328 images):

| model | RAG vs benchmark baseline | RAG vs matched greedy | contrastive vs benchmark baseline | contrastive vs matched greedy |
|---|---|---|---|---|
| qwen25vl | +0.004 [-0.019, +0.027], Holm 1.000 | +0.000 [-0.024, +0.025], Holm 1.000 | +0.013 [-0.011, +0.036], Holm 1.000 | +0.012 [-0.012, +0.035], Holm 1.000 |
| llava16 | -0.063 [-0.090, -0.034], Holm 0.001 | -0.019 [-0.050, +0.012], Holm 1.000 | -0.053 [-0.082, -0.024], Holm 0.005 | -0.036 [-0.071, -0.003], Holm 0.293 |
| chexagent | +0.017 [-0.015, +0.047], Holm 1.000 | +0.003 [-0.030, +0.037], Holm 1.000 | +0.048 [+0.007, +0.086], Holm 0.080 | +0.056 [+0.014, +0.099], Holm 0.052 |
| huatuogpt | +0.022 [+0.002, +0.044], Holm 0.218 | +0.025 [+0.001, +0.048], Holm 0.293 | -0.050 [-0.069, -0.031], Holm 0.001 | -0.062 [-0.085, -0.038], Holm 0.001 |
| llava_med | +0.037 [+0.019, +0.054], Holm 0.010 | +0.037 [+0.019, +0.054], Holm 0.013 | -0.000 [-0.021, +0.020], Holm 1.000 | -0.000 [-0.021, +0.020], Holm 1.000 |

Strategies that increased SMHR: RAG for llava16 (matched greedy, Holm 0.010) and, without radiology, RAG for llava_med and contrastive decoding for chexagent. Head-to-head, never tested in the doc: contrastive decoding beat RAG for llava16, chexagent and huatuogpt (Holm ≤ 0.002), RAG beat contrastive for qwen25vl (+0.025, Holm 0.015), llava_med tied. Mean SRI: benchmark baseline 1.401, matched greedy 1.516, RAG 1.474, contrastive 1.406; contrastive minus matched greedy -0.110 [-0.183, -0.039].

### Check 8. Pillars C and E

Pillar C: SMHR-CREST rho +0.643 (permutation p 0.029, Holm over 3: 0.056; Fisher 95% CI 0.07-0.90; image-bootstrap 0.57-0.71, which ignores model sampling); CREST spans only 2.67-2.86. SMHR-MediHall rho = -1.000 is built in: the unweighted error rate alone gives +0.965, the per-claim weights correlate r = 0.95, and random class weights reproduce it exactly in only 1.3% of draws (median -0.87). Seven of ten divergence cells are stable (≥ 91% of resamples), three sit at the 1-SD threshold (71-77%).

| pair | rho | permutation p | Holm (6) | Fisher 95% CI (n=12) | nine general models only (p) | valid radiology only |
|---|---|---|---|---|---|---|
| radiology-dermatology | +0.210 | 0.513 | 0.790 | [-0.45, +0.72] | -0.50 (0.18) | +0.36 (0.260) |
| radiology-histopathology | +0.273 | 0.395 | 0.790 | [-0.39, +0.75] | -0.22 (0.58) | +0.55 (0.067) |
| radiology-ophthalmology | +0.490 | 0.110 | 0.331 | [-0.16, +0.84] | +0.08 (0.85) | +0.69 (0.018) |
| dermatology-histopathology | +0.811 | 0.002 | 0.013 | [+0.41, +0.95] | +0.62 (0.09) | +0.81 (0.002) |
| dermatology-ophthalmology | +0.664 | 0.022 | 0.088 | [+0.11, +0.90] | +0.33 (0.39) | +0.66 (0.022) |
| histopathology-ophthalmology | +0.769 | 0.005 | 0.024 | [+0.31, +0.94] | +0.60 (0.10) | +0.77 (0.005) |

Pillar E: the three non-radiology correlations reproduce and two survive Holm (dermatology-ophthalmology does not, p 0.088); none is significant among the nine general models alone, so the cross-modality association largely reflects the specialists and weak general models being poor everywhere. With n = 3 specialists no SRI correlation can have a two-sided p below 0.33. "Radiology as its own regime" disappears on valid radiology images.

### Check 9. Causal wording

Each "because / driven by / leans on / reflects" sentence rests on correlation or a single manipulation: RAG widens the gap *because* it helps general models (C065, contradicted by the matched baseline); the Pillar D 11% vs 3% label gap "most likely reflects" pipeline differences (C100, untested; confounded with run-to-run noise); Pillar D "weights property" (C114, decoding is the only manipulation); radiology "regime" (C089, a data artefact); Q4 dropped "because no model states a confidence" (true: 0.7% of responses). The only causal evidence named in the brief, Pillar A stage replacement, is not in the repository (C137). The llava_med decoding bug is the one place with a genuine intervention (repaired rerun: 0.728 vs 0.791).

### Check 10. Multiple comparisons

The reports contain 25 explicit significance statements (Pillar B 10, Pillar C 3, Pillar E 6 SMHR and 6 SRI correlations) plus 12 implicit SRI > 1 tests. After Holm within family: Pillar B 5 of 6 starred comparisons survive (chexagent RAG does not); Pillar C SMHR-CREST Holm 0.056 (not below 0.05 over its family of three); Pillar E 2 of 3 significant pairs survive; core SRI all 12 survive. Analyses added here: 10 top-5 pairs, 11 adjacent pairs, two families of 10 Pillar B tests (one per baseline), 5 head-to-head strategy tests, each Holm-adjusted within its family.

### Check 11. Single run and sampling

Core run: temperature 0.1, `do_sample=True`, top-p 0.9 for most models, one run per cell; Pillar B: greedy; Pillar D: greedy and nucleus sampling (top-p 0.9) at T = 0 (1e-4), 0.3, 0.7. Pillar D greedy reproduces the core response for 1.9% of qwen25vl items. Decoding mode alone moved SMHR by -0.046 for llava16 (CI excludes 0), -0.011 for qwen25vl; across the four distinct Pillar D settings one model's SMHR varies by 0.022 (qwen25vl) to 0.077 (huatuogpt), against gaps of 0.002-0.010 inside the top-three general models. Stochasticity can therefore change any ordering inside the top group; it cannot erase the gap between the top five and the specialists (0.13-0.26).

### Check 12. Strata and sample sizes

Core: 13 strata of 150-400 images; every model x modality x stratum cell has ≥ 450 records (smallest OS3: 150 images); no cell below 30. Pillar B/D subset: 500 images, strata of 21 (OS3) to 57 images, 85 ophthalmology images in total; 63-228 records per model per stratum; Pillar D by-modality ECE cells go down to 120 responses. Annotation sample: 48 keys, 3 per modality x query-type cell, 48 items per model x condition cell. Do not report stratum-level results from the subsets.

### Added checks

**X1 (image integrity)** and **X2 (human annotation)** are described at the top of section 1. Sensitivities recomputed without the radiology images: core (`no_rad`, 2,300 images), core with valid radiology only (113 images), Pillar B (328 images) and Pillar D (24,034 responses).

Method note: the recomputation scripts are in the session scratchpad (`a01_build_core.py` ... `a16_report.py`, `lib_stats.py`, `lab.py`) and are not copied into the repository, since the brief asked for the two output files only; say if you want them added.

## 5. The five riskiest sentences, and how to handle them

**1. Any sentence that reports a radiology result or says the benchmark has 1,200 radiology images** (C001, C016-C027, C040, C084-C089).
A reviewer who hashes the images, or an annotator who opens `images/radiology/`, finds 12 identical X-rays. *Defend:* you cannot; fix it. *Soften:* say the radiology arm has 113 valid images, report radiology as a small, separate arm with wide intervals, drop the radiology rank correlations and the radiology ECE values, or re-extract the images (replace the filename fallback with an exact-path match) and rerun radiology.

**2. "The three medical specialists are the three worst models overall."** (C035)
Without the radiology images huatuogpt ranks 8th of 12, ahead of llava16 and idefics3, and a modest change in class weights flips it. *Soften:* "Each specialist had a higher SMHR than the best general model in every modality (SRI 1.31-1.85); chexagent and llava_med had the highest SMHR overall; huatuogpt was better than one to three general models in every modality."

**3. "qwen25vl (0.529) and gemma3 (0.532) are the safest."** (C036)
The gap is 0.0023 with an interval spanning 0, gemma3 is not separated from internvl3, and it drops to 5th without radiology. *Soften:* "Five general models formed the lowest-SMHR group (0.529-0.562); we do not rank within the first three." If a single best model is wanted, qwen25vl is the defensible one on valid images (0.428, next 0.452).

**4. Pillar B: "Greedy decoding in every condition", "RAG widens the gap because it helps the general models", and "RAG for chexagent (+0.026, significant)"** (C046, C062, C065, C066, C053-C055).
The baseline is temperature-0.1 sampling, so each delta mixes decoding and mitigation; the chexagent effect is not significant after Holm; RAG hurts llava16 against a greedy baseline; and several effects reverse or vanish without radiology. *Soften:* report matched greedy baselines and Holm-adjusted intervals, drop the causal clause, and lead with the one robust effect (contrastive decoding for huatuogpt, -0.05) and the CHR increase under RAG.

**5. "Consistent with calibration being primarily a property of the model weights" (Pillar D verdict)** (C114-C116, C138).
Only decoding was varied; five models; the greedy ECE order is reproduced in 51% of image resamples; the best-calibrated model changes when radiology is removed. *Soften:* "The ordering of the five models by ECE was stable across four decoding settings (mean rho = 0.90, 95% CI 0.83-0.95); with one prompt and five models this shows insensitivity to decoding, not that calibration is a property of the weights."
