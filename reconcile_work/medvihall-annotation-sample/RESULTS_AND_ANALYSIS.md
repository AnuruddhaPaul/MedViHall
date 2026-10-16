# MediViHall: results and analysis (all experiments)

One-file version of everything in `results/`. Each section is also a separate text file in `results/`; raw numbers are in `results/raw/`.

> If you are annotating the blind sheet in this repository, annotate first and read this file afterwards.


---

## overview

```text
MEDVIHALL - OVERVIEW OF EXPERIMENTS AND WHERE TO FIND EACH RESULT

NOTE FOR ANNOTATORS: this folder contains aggregate model-level results. If you are annotating the
720-item sheet in this repository, annotate first and read these results afterwards, so that the
blind annotation is not influenced by which model or strategy performs better.

What MediViHall is
A benchmark and analysis of hallucination in medical vision-language models (VLMs). Models answer
questions about medical images in four modalities (radiology, dermatology, histopathology,
ophthalmology). Every answer is split into individual claims, each claim is checked against structured
ground truth and a language-model judge, and errors are classified into a 7-class hallucination
taxonomy. Results are reported with SMHR (severity-weighted hallucination rate), CHR and SRI.

Metrics
- SMHR: class-weighted share of hallucinated claims (weights: classes 1,2 = 1.0; 3 = 0.7; 4 = 0.5;
  5 = 0.4; 6 = 0.1; 7 = 0.6; a Layer-1 omission counts as a class-2 error and as one extra claim).
  Lower is safer.
- CHR: share of responses that contain at least one class 1 or class 2 hallucination (or an omission).
- SRI (specialist ratio index): SMHR of a medical specialist model / SMHR of the best general model in
  the same modality. SRI > 1 means the specialist hallucinates MORE than the best general VLM.
- CREST (Pillar C): mean clinical-risk rating (1-3) over erroneous claims; higher = worse.
- MediHall Score (Pillar C): mean per-claim score in [0,1]; higher = better.
- ECE / ACE (Pillar D): calibration error of the model's stated 0-100% confidence against whether the
  response contained zero hallucinations (10 equal-width / 10 equal-mass bins).

Labeling pipeline (used for all experiments)
Claim extraction (local Qwen2.5-7B-Instruct, 4-bit) -> Layer 1 automatic check (CheXbert for radiology;
scispaCy/negspaCy lexicons for the other modalities) -> Layer 2 LLM judge assigning the 7-class
taxonomy. The judge is a 7B model; within-pipeline relabeling changed 1.1% (strict) / 2.8% (claim-level)
of labels.

Experiments and files
| Experiment | Question | File |
| Core benchmark | Which of 12 VLMs hallucinate least? Do specialists beat general models? | 01_core_benchmark_smhr_chr_sri.txt |
| Pillar B (RQ8) | Which mitigation (RAG, visual contrastive decoding) reduces hallucination most? | 02_pillar_b_mitigation_rq8.txt |
| Pillar C (RQ9) | Do CREST / MediHall Score agree with SMHR? | 03_pillar_c_metric_concordance_rq9.txt |
| Pillar D (RQ10) | Is verbalized calibration a weights property or a decoding artifact? | 04_pillar_d_calibration_rq10.txt |
| Pillar E (RQ5) | Does hallucination safety transfer across modalities? | 05_pillar_e_cross_modal_transfer_rq5.txt |
| Annotation sample | The 720 blind items in this repository | 06_annotation_sample.txt |
| Known issues | Data-quality problems found and what they affect | 07_data_quality_and_known_issues.txt |
| Raw numbers | Machine-readable result files | raw/*.json |

Models (core benchmark, 12): general - qwen25vl, qwen3vl, qwen2vl, qwen35, gemma3, idefics3, internvl3,
minicpm, llava16; medical specialists - chexagent (radiology), huatuogpt, llava_med.
Pillars B and D use a 5-model representative subset: qwen25vl (best general), llava16 (worst general),
chexagent, huatuogpt, llava_med (the three specialists), on a 500-image stratified subset
(1,679 image-question calls per model).
```


---

## core benchmark smhr chr sri

```text
CORE BENCHMARK - 12 VLMs, 141,000 RESPONSES (11,750 per model)

Question: which models hallucinate least, and do medical specialists beat general models?

SMHR and CHR per model (sorted by SMHR, lower = safer)
| rank | model     | type       | SMHR  | CHR   | responses | judge parse errors |
|------|-----------|------------|-------|-------|-----------|--------------------|
| 1    | qwen25vl  | general    | 0.529 | 0.785 | 11750     | 46                 |
| 2    | gemma3    | general    | 0.532 | 0.731 | 11750     | 59                 |
| 3    | internvl3 | general    | 0.539 | 0.760 | 11750     | 65                 |
| 4    | qwen35    | general    | 0.549 | 0.773 | 11750     | 97                 |
| 5    | qwen3vl   | general    | 0.562 | 0.730 | 11750     | 51                 |
| 6    | minicpm   | general    | 0.580 | 0.715 | 11750     | 35                 |
| 7    | idefics3  | general    | 0.636 | 0.800 | 11750     | 38                 |
| 8    | qwen2vl   | general    | 0.643 | 0.797 | 11750     | 34                 |
| 9    | llava16   | general    | 0.675 | 0.741 | 11750     | 21                 |
| 10   | huatuogpt | specialist | 0.691 | 0.806 | 11750     | 134                |
| 11   | chexagent | specialist | 0.748 | 0.719 | 11750     | 27                 |
| 12   | llava_med | specialist | 0.794 | 0.750 | 11750     | 4                  |

SMHR by modality
| model     | radiology | dermatology | histopathology | ophthalmology |
|-----------|-----------|-------------|----------------|---------------|
| qwen25vl  | 0.728     | 0.348       | 0.533          | 0.455         |
| gemma3    | 0.633     | 0.461       | 0.575          | 0.465         |
| internvl3 | 0.652     | 0.447       | 0.504          | 0.470         |
| qwen35    | 0.675     | 0.496       | 0.482          | 0.416         |
| qwen3vl   | 0.764     | 0.415       | 0.521          | 0.418         |
| minicpm   | 0.619     | 0.533       | 0.646          | 0.442         |
| idefics3  | 0.644     | 0.602       | 0.651          | 0.627         |
| qwen2vl   | 0.828     | 0.435       | 0.564          | 0.571         |
| llava16   | 0.746     | 0.565       | 0.716          | 0.571         |
| huatuogpt | 0.827     | 0.574       | 0.631          | 0.564         |
| chexagent | 0.826     | 0.629       | 0.736          | 0.727         |
| llava_med | 0.921     | 0.645       | 0.745          | 0.669         |

Best general VLM per modality (denominator of SRI)
| modality       | best general VLM | its SMHR |
|----------------|------------------|----------|
| dermatology    | qwen25vl         | 0.348    |
| histopathology | qwen35           | 0.482    |
| ophthalmology  | qwen35           | 0.416    |
| radiology      | minicpm          | 0.619    |

SRI per specialist per modality (> 1 = specialist hallucinates MORE than the best general VLM)
| specialist | radiology | dermatology | histopathology | ophthalmology |
|------------|-----------|-------------|----------------|---------------|
| chexagent  | 1.34      | 1.81        | 1.53           | 1.75          |
| huatuogpt  | 1.34      | 1.65        | 1.31           | 1.36          |
| llava_med  | 1.49      | 1.85        | 1.54           | 1.61          |

Findings
- The three medical specialists are the three worst models overall (SMHR 0.69-0.79 vs 0.53-0.68 for the
  nine general models). qwen25vl (0.529) and gemma3 (0.532) are the safest.
- Every SRI value is above 1 (1.31-1.85): in every modality, each specialist hallucinates more than the best
  general VLM. Specialization did not reduce hallucination in this benchmark.
- Radiology has the highest SMHR for 10 of 12 models and dermatology the lowest for 9 of 12, so modality matters as much as model choice.
- CHR (share of responses with a class-1/2 error) is 0.72-0.81 for all models and does not rank models
  the same way SMHR does (minicpm and chexagent have the lowest CHR; chexagent has a low CHR but the second-highest SMHR).

Caveats
- The llava_med figures (SMHR 0.794) were computed on responses whose beginnings were cut off in about
  one third of cases (decoding bug, see 07_data_quality_and_known_issues.txt). Re-labeling the repaired
  responses on the 500-image subset gives SMHR 0.728 instead of 0.791, so the llava_med rank and its SRI
  values are probably overstated. This has not been re-run for the full 11,750 responses.
- Labels come from a 7B LLM judge plus automatic checks; they were not human-verified.
```


---

## pillar b mitigation rq8

```text
PILLAR B (RQ8) - COMPARATIVE MITIGATION EFFICACY

Question: which hallucination-mitigation strategy lowers SMHR most, per model, and does mitigation
close the specialist-vs-general gap?

Design
- 5 models (qwen25vl, llava16, chexagent, huatuogpt, llava_med) x 500-image stratified subset x
  1,679 image-question calls per model = 8,395 calls per condition. Greedy decoding in every condition;
  identical per-question-type token budgets (Q1 700, Q2 220, Q3 480, Q4 280).
- Baseline: the unmitigated prompt (original core-run responses for four models; llava_med was re-run
  with a decoding fix because its original baseline had its beginnings cut off, see file 07).
- RAG: each prompt is prefixed with "Reference context:" and the top-3 reference snippets (definitions of
  imaging/pathology vocabulary for the modality) retrieved with all-MiniLM-L6-v2 from a 4-modality
  knowledge base. Retrieval uses the question text only (not the image), so it depends on modality,
  question type and stratum. 0 retrieval failures in 8,395 calls; mean top-1 similarity 0.556.
- Contrastive: visual contrastive decoding. At each step the next-token logits are
  (1+alpha)*logits(original image) - alpha*logits(noised image), alpha = 1.0, restricted to tokens with
  probability >= 0.1 x the top token; the noised copy is forward-diffusion noise at t = 500.
- Fine-tuning (originally planned as a third strategy) was dropped at the user's request.
- Labels: the same claim -> Layer 1 -> Layer 2 pipeline as the core benchmark. Baseline labels for four
  models are the core-run labels; the llava_med baseline, RAG and contrastive responses were labeled
  fresh (17,443 responses; 45 judge failures; 1-17 unlabeled responses per model/condition cell).
- Statistics: SMHR differences are paired on the same image/question, with a 95% bootstrap CI that
  resamples images (2,000 resamples). * marks an interval that excludes 0. Ten comparisons, no
  multiplicity correction.

SMHR per model and strategy (lower = safer) and change versus baseline
| model     | baseline | RAG   | contrastive | delta RAG [95% CI]        | delta contrastive [95% CI] |
|-----------|----------|-------|-------------|---------------------------|----------------------------|
| qwen25vl  | 0.537    | 0.508 | 0.533       | -0.028 [-0.046, -0.009] * | -0.003 [-0.021, +0.016]    |
| llava16   | 0.669    | 0.627 | 0.583       | -0.042 [-0.063, -0.020] * | -0.085 [-0.106, -0.066] *  |
| chexagent | 0.751    | 0.778 | 0.709       | +0.026 [+0.003, +0.048] * | -0.041 [-0.069, -0.013] *  |
| huatuogpt | 0.699    | 0.704 | 0.676       | +0.004 [-0.012, +0.020]   | -0.025 [-0.041, -0.009] *  |
| llava_med | 0.728    | 0.731 | 0.724       | +0.003 [-0.014, +0.018]   | -0.005 [-0.019, +0.008]    |

Answers to the four pre-registered questions
(a) Which strategy reduces SMHR most per model?
    qwen25vl: RAG (-0.028*); llava16: contrastive (-0.085*); chexagent: contrastive (-0.041*);
    huatuogpt: contrastive (-0.025*); llava_med: contrastive (-0.005, not significant).
(b) Does the best strategy differ by model?
    Only slightly. Contrastive decoding is best for four of five models, including all three specialists.
    qwen25vl is the exception: RAG helps it (-0.028*) and contrastive does not (-0.003, n.s.).
(c) Does mitigation narrow or widen the specialist-vs-general gap (SRI)?
    Neither closes it. Mean SRI is 1.40 at baseline, 1.47 with RAG
    (gap widens) and 1.41 with contrastive decoding (unchanged, +0.005). RAG widens the gap
    because it helps the two general models and hurts or does nothing for the specialists.
    (SRI here compares against the better of only two general models, qwen25vl and llava16.)
| condition   | mean SRI (3 specialists x 4 modalities) |
|-------------|-----------------------------------------|
| baseline    | 1.401                                   |
| rag         | 1.474                                   |
| contrastive | 1.406                                   |
(d) Does any strategy increase SMHR for any model?
    Yes - RAG for chexagent (+0.026, significant), and, not significantly, for huatuogpt (+0.004) and
    llava_med (+0.003). Reference snippets do not help the specialists and can hurt chexagent. This is a
    negative result worth reporting. Contrastive decoding never raised SMHR significantly.

Caveats - read before using these numbers
1. SMHR is a ratio, so it can fall when answers get longer and contain more correct claims, without
   fewer hallucinations. CHR (share of responses with a class-1/2 error) went UP under RAG for qwen25vl
   (0.776 -> 0.796), llava16 (0.733 -> 0.856) and huatuogpt (0.818 -> 0.894). RAG and contrastive also
   changed claim counts (table below). The SMHR gains should not be read as "fewer harmful responses".
2. Confidence statements: the share of responses with no stated confidence rose under RAG for chexagent,
   huatuogpt and llava_med (table below), which matters for any calibration analysis built on these runs.
3. One greedy run per cell; the only uncertainty quantified is sampling over images, not run-to-run.
4. The judge is a 7B model; its label noise (1-3%) is small relative to most effects but is not zero.
5. The baseline for four models is the original core-run response, not a fresh re-run under identical
   settings; the llava16 baseline in particular differs from the other conditions in how often it states
   a confidence (39% missing vs 14% under RAG), which is not explained.

CHR and claim counts
| model     | CHR base | CHR RAG | CHR contr. | claims base | claims RAG | claims contr. |
|-----------|----------|---------|------------|-------------|------------|---------------|
| qwen25vl  | 0.776    | 0.796   | 0.793      | 6,836       | 8,712      | 7,861         |
| llava16   | 0.733    | 0.856   | 0.805      | 4,960       | 7,165      | 7,701         |
| chexagent | 0.706    | 0.759   | 0.732      | 3,514       | 3,267      | 3,410         |
| huatuogpt | 0.818    | 0.894   | 0.807      | 5,408       | 6,183      | 5,662         |
| llava_med | 0.787    | 0.817   | 0.788      | 4,199       | 4,831      | 4,011         |

Missing confidence and answer length
| model     | no-conf base | no-conf RAG | no-conf contr. | median words base | RAG | contr. |
|-----------|--------------|-------------|----------------|-------------------|-----|--------|
| qwen25vl  | 10.9%        | 11.1%       | 10.8%          | 166               | 199 | 176    |
| llava16   | 39.3%        | 13.6%       | 28.3%          | 159               | 131 | 175    |
| chexagent | 16.2%        | 29.7%       | 19.4%          | 68                | 60  | 60     |
| huatuogpt | 22.0%        | 32.5%       | 25.0%          | 66                | 75  | 73     |
| llava_med | 51.6%        | 61.5%       | 53.8%          | 40                | 55  | 40     |
```


---

## pillar c metric concordance rq9

```text
PILLAR C (RQ9) - DO ALTERNATIVE METRICS AGREE WITH SMHR?

Question: if a model looks safest under SMHR, does it also look safest under CREST (clinical-risk
severity of its errors) and the MediHall Score (per-claim correctness)? Agreement would mean SMHR is not
an idiosyncratic metric. If the metrics agree, SMHR-vs-CREST should be positive and SMHR-vs-MediHall
negative.

Rank correlations across the 12 models (overall)
| metric pair (12 models, Spearman) | rho    | approx. p |
|-----------------------------------|--------|-----------|
| SMHR vs CREST                     | +0.643 | 0.024     |
| SMHR vs MediHall Score            | -1.000 | <0.001    |
| CREST vs MediHall Score           | -0.643 | 0.024     |

Divergences: model x modality cells where SMHR and CREST disagree most (z-score difference)
| model     | modality       | SMHR  | CREST | z(SMHR)-z(CREST) | pattern                                                     |
|-----------|----------------|-------|-------|------------------|-------------------------------------------------------------|
| huatuogpt | ophthalmology  | 0.564 | 2.35  | +1.89            | high SMHR-vs-CREST (frequent but comparatively mild errors) |
| qwen35    | histopathology | 0.482 | 2.78  | -1.33            | high CREST-vs-SMHR (rare but severe errors)                 |
| gemma3    | radiology      | 0.633 | 2.96  | -1.23            | high CREST-vs-SMHR (rare but severe errors)                 |
| qwen3vl   | dermatology    | 0.415 | 2.68  | -1.23            | high CREST-vs-SMHR (rare but severe errors)                 |
| internvl3 | ophthalmology  | 0.470 | 2.35  | +1.19            | high SMHR-vs-CREST (frequent but comparatively mild errors) |
| internvl3 | histopathology | 0.504 | 2.78  | -1.13            | high CREST-vs-SMHR (rare but severe errors)                 |
| llava16   | ophthalmology  | 0.571 | 2.49  | +1.10            | high SMHR-vs-CREST (frequent but comparatively mild errors) |
| huatuogpt | dermatology    | 0.574 | 2.51  | +1.04            | high SMHR-vs-CREST (frequent but comparatively mild errors) |
| llava_med | radiology      | 0.921 | 2.96  | +1.02            | high SMHR-vs-CREST (frequent but comparatively mild errors) |
| qwen2vl   | radiology      | 0.828 | 2.84  | +1.02            | high SMHR-vs-CREST (frequent but comparatively mild errors) |

Findings
- SMHR and CREST agree moderately and in the expected direction (rho = +0.64, p about 0.02): models with a
  higher hallucination rate tend to make higher-risk errors.
- SMHR and the MediHall Score are perfectly inversely ranked (rho = -1.0). That is a very strong
  agreement, but it is most likely partly built in (both summarize per-claim correctness), so it
  should not be presented as independent confirmation. The relation of the MediHall Score to the other two
  metrics was not tested for construction overlap.
- The two disagreement patterns are informative: some model/modality cells make frequent but comparatively
  mild errors (e.g. huatuogpt and llava16 in ophthalmology: high SMHR, low CREST), while others make rarer
  but more severe errors (e.g. qwen35 in histopathology, gemma3 in radiology, qwen3vl in dermatology: lower SMHR
  than CREST would suggest). A single metric would rank these cells differently.

Caveats
- n = 12 models; correlations are coarse and the p-values are approximate (t approximation, no ties handling).
- All three metrics rest on the same claim extraction and judge, so they are not independent measurements
  of the models.
```


---

## pillar d calibration rq10

```text
# Pillar D (RQ10): Is verbalized calibration a weights property or a decoding artifact?

## Setup
Five models (qwen25vl, llava16, chexagent, huatuogpt, llava_med) were run on a 500-image stratified subset
(4 modalities, 1,679 image-query calls per config) under six decoding configurations: temperature
{0.0, 0.3, 0.7} x {greedy, nucleus (top-p 0.9)}, 50,370 calls in total. Greedy decoding ignores
temperature, so the three greedy configs produce byte-identical responses for four of the five models;
only four decoding settings are independent (greedy, and nucleus at 0.0, 0.3, 0.7). Inference functions
were patched so that greedy truly uses do_sample=False (several originally hardcoded do_sample=True).

Data integrity note: a 220-token cap applied to llava16 mid-run truncated 6,299 Q1/Q3/Q4 responses (and
their trailing confidence statement). These were excluded and the 5,361 Q1/Q3 calls regenerated with the
original token budgets (700/480); Q4 was dropped because no model states a confidence on Q4.

## Method
- Confidence: the stated 0-100% value parsed from each response. Responses with no stated confidence
  cannot enter ECE/ACE; coverage ranges from about 42% (llava_med) to about 89% (qwen25vl).
- Correctness label: a response is correct iff it contains zero Class 1-7 hallucinations (strict label:
  Layer 2 claim judgments plus Layer 1 omissions). A claim-level-only variant is reported as a sensitivity check.
- Labels: byte-identical responses reuse the core pipeline's labels (1,080 responses); the other 19,862
  distinct responses were labeled by the same local pipeline (Qwen2.5-7B claim extraction, CheXbert /
  scispaCy Layer 1, Layer 2 judge). On 60 validation responses with known core labels the strict label
  agreed 58/60 (97%); the claim-level label agreed 52/60 (87%). That gap most likely reflects differences
  between the earlier core run and this pipeline rather than random noise: relabeling 1,000 of the
  responses with a shuffled order and a different batch size changed only 1.1% of strict labels (95% CI
  0.6-2.0%) and 2.8% of claim-level labels (1.9-4.0%); Layer 1 was fully deterministic (0 differences).
- ECE: 10 equal-width bins. ACE: 10 equal-mass bins. Rank stability: mean pairwise Spearman rho between
  the five models' ECE rankings across configs; rho >= 0.8 is read as stable, <= 0.4 as shifting.

## Results (strict label; ECE / ACE, n)
| Model | t0.0 greedy | t0.0 nucleus | t0.3 greedy | t0.3 nucleus | t0.7 greedy | t0.7 nucleus |
|---|---|---|---|---|---|---|
| chexagent | 0.508/0.508 (1400) | 0.528/0.528 (1410) | 0.508/0.508 | 0.533/0.531 (1360) | 0.508/0.508 | 0.547/0.547 (1172) |
| llava16 | 0.549/0.542 (1179) | 0.503/0.502 (1033) | 0.549/0.542 | 0.595/0.585 (1030) | 0.549/0.542 | 0.589/0.586 (1029) |
| qwen25vl | 0.666/0.665 (1489) | 0.677/0.676 (1495) | 0.666/0.665 | 0.661/0.661 (1478) | 0.666/0.665 | 0.651/0.649 (1468) |
| llava_med | 0.673/0.673 (796) | 0.674/0.674 (797) | 0.673/0.673 | 0.672/0.668 (801) | 0.673/0.673 | 0.669/0.662 (699) |
| huatuogpt | 0.693/0.693 (1367) | 0.706/0.706 (1322) | 0.693/0.693 | 0.717/0.717 (1268) | 0.693/0.693 | 0.730/0.726 (1210) |

| Label | All 6 configs | 4 distinct settings |
|---|---|---|
| Strict | mean rho 0.93 (min 0.80) | 0.90 (min 0.80) |
| Claim-level only | 0.81 (min 0.60) | 0.75 (min 0.60) |

ECE moves by 0.04 or less across decoding settings for most models. Accuracy under the strict label is
only 12-28% against 54-91% mean stated confidence, so ECE here mainly measures overconfidence.

## Robustness
- Binning: identical rho with 5, 10, 15 or 20 bins.
- Leave-one-model-out: rho stays 0.90-0.93 when any of four models is dropped; dropping huatuogpt (the
  consistently worst-calibrated model) lowers it to 0.80-0.87, so the result leans on the contrast
  between the best (chexagent) and worst (huatuogpt) models.
- By modality: stable in histopathology and ophthalmology (rho 0.95-0.97 over the 4 settings) but weaker
  in radiology (0.75) and dermatology (0.65). Model orderings also differ by modality (e.g. qwen25vl has
  the worst ECE in radiology, 0.895, and the best in ophthalmology, 0.286), so a single pooled ECE per
  model hides large modality dependence.
- Common-coverage subset (items where all five models stated a confidence; 303-555 items per config):
  rho falls to 0.81 (all 6) and 0.75 (4 distinct), so coverage differences contribute to the pooled result.
- Label noise: random label flips (one draw per distinct response, 200 repetitions) at 5% leave the
  verdict intact (P[rho >= 0.8] = 0.99). The measured within-pipeline flip rate is 1.1% (strict) and 2.8%
  (claim-level), well inside that regime. At 13% mean rho is 0.82-0.85 and P[rho >= 0.8] is 0.52-0.70; at
  20% it is 0.15-0.39; these are stress tests above the measured noise, not expected conditions.

## Verdict
For the strict label, the ECE ranking of the five models is stable across decoding settings
(mean rho 0.90-0.93), consistent with calibration being primarily a property of the model weights rather
than a decoding artifact. The conclusion is supported with moderate rather than high confidence: it is
robust to binning and to individual models, holds within histopathology and ophthalmology, but weakens
in radiology and dermatology, on the common-coverage subset (rho about 0.75-0.81), and under the
claim-level label (distinct-settings rho 0.75). It is robust to realistic label noise (measured 1-3%) and
only degrades under simulated noise of about 13% or more.

## Limitations
- Only four independent decoding settings; with five models rho is coarse.
- ECE is dominated by overconfidence under a strict "zero hallucination" label.
- Confidence is only available on a model-dependent subset of responses.
- The correctness label comes from a 7B LLM judge: 1.1% (strict) and 2.8% (claim-level) of labels change
  between runs on identical text, and about 5% of responses reuse labels from the earlier core run, which
  agreed with fresh labels on 97% (strict) / 87% (claim-level) of 60 checked responses.
- Per-model rankings depend on modality; pooled ECE should not be read as one number per model.
```


---

## pillar e cross modal transfer rq5

```text
PILLAR E (RQ5) - DOES HALLUCINATION SAFETY TRANSFER ACROSS MODALITIES?

Question: if a model is relatively safe in one modality, is it also safe in another? Measured as the
Spearman correlation between the 12 models' SMHR rankings in each pair of modalities (t-test, alpha 0.05).

SMHR ranking correlation between modalities
| modality A     | modality B     | Spearman rho (12 models) | significant at 0.05? |
|----------------|----------------|--------------------------|----------------------|
| dermatology    | histopathology | +0.811                   | significant          |
| dermatology    | ophthalmology  | +0.664                   | significant          |
| dermatology    | radiology      | +0.210                   | not significant      |
| histopathology | ophthalmology  | +0.769                   | significant          |
| histopathology | radiology      | +0.273                   | not significant      |
| ophthalmology  | radiology      | +0.490                   | not significant      |

SRI correlation between modalities (the 3 specialists only)
| modality A     | modality B     | rho of SRI (3 specialists) |
|----------------|----------------|----------------------------|
| dermatology    | histopathology | +1.00                      |
| dermatology    | ophthalmology  | +0.50                      |
| dermatology    | radiology      | +0.50                      |
| histopathology | ophthalmology  | +0.50                      |
| histopathology | radiology      | +0.50                      |
| ophthalmology  | radiology      | -0.50                      |

Findings
- Dermatology, histopathology and ophthalmology transfer well: rankings correlate strongly (rho 0.66-0.81,
  all significant). A model that is safe on skin images tends to be safe on pathology and fundus images.
- Radiology does not transfer: its ranking is only weakly related to the others (rho 0.21-0.49, none
  significant). Safety in radiology has to be assessed on its own.
- The specialist SRI correlations use only 3 models: one pair is 1.0, four are 0.5 and one is -0.5. With n = 3 the
  statistics are meaningless (the 1.0 is flagged 'significant' only because the t statistic is infinite), so nothing
  can be concluded about specialists from this table.

Caveats
- 12 models per correlation; non-significant is not evidence of no relation.
- Radiology data also differs in structure (chest X-ray label set and the CheXbert-based Layer 1), so the
  radiology result may partly reflect measurement differences rather than only model behavior.
```


---

## annotation sample

```text
ANNOTATION SAMPLE - THE 720 BLIND ITEMS IN THIS REPOSITORY

Purpose: human (and AI-annotator) review of hallucination in model generations, blind to model and condition.

Design
- 48 questions (an image plus one of four query types) x 5 models x 3 conditions
  (baseline, RAG, contrastive) = 720 generations; each of the 48 images appears in 15 generations.
- Balanced exactly: {'qwen25vl': 144, 'huatuogpt': 144, 'chexagent': 144, 'llava16': 144, 'llava_med': 144} items per model; {'baseline': 240, 'contrastive': 240, 'rag': 240} per condition;
  {'dermatology': 180, 'ophthalmology': 180, 'radiology': 180, 'histopathology': 180} per modality; {'Q3': 180, 'Q1': 180, 'Q2': 180, 'Q4': 180} per query type.
- Stratified by modality x query type (3 questions per cell), spread across the image strata
  (e.g. normal / abnormal levels within each dataset).
- Filtered before sampling: responses that were empty, errors, under 8 words, or that started mid-sentence were
  excluded; a key was kept only if all its 15 responses passed. No model needed the "whole model fails" exception, and no cell
  fell short. Repetition loops (mostly chexagent) were kept and flagged internally.
- Items are shuffled with random IDs. The sheet shows no model or condition. The key that maps IDs back is NOT in this
  repository.
- Selection effect: because only questions with 15 well-formed responses were kept, hallucination rates in this sample
  describe well-formed outputs and may differ from the full runs. Pre-filter validity (share of responses passing the
  filter) was lowest for huatuogpt|baseline at 0.940 and above that for every other model/condition cell.

Files: ../annotation_sheet.csv, ../annotation_sheet.jsonl, ../images/, raw/annotation_sample_report.json (aggregate counts only).
```


---

## data quality and known issues

```text
DATA QUALITY AND KNOWN ISSUES

1. llava_med decoding bug (found 2026-10-08)
   What: the inference code cut off the first N tokens of any llava_med answer longer than its prompt (LLaVA's
   generate() returns only new tokens, but the code removed len(prompt) tokens). About 32-33% of llava_med
   responses in the core run and in the Pillar D greedy runs start mid-sentence; the median answer was 28 words
   instead of 40. RAG prompts are longer, so only 0.2% of RAG responses were affected.
   Fixed for: the Pillar B contrastive run (0 chopped starts in 1,679) and the Pillar B baseline re-run
   (0 chopped starts, 1,679 calls).
   Not fixed for: the 11,750-response core benchmark and Pillar D calibration (llava_med rows).
   Effect measured: on the 500-image subset, llava_med baseline SMHR is 0.728 with the fix vs 0.791 without.
   So the core-benchmark llava_med SMHR (0.794), its rank and its SRI values are probably overstated; the
   direction "specialists hallucinate more than general models" still holds for chexagent and huatuogpt, but the
   size of the llava_med gap has not been re-measured.

2. llava16 token-cap bug (Pillar D)
   A 220-token cap applied mid-run truncated 6,299 llava16 Q1/Q3/Q4 responses and their trailing confidence
   statements. They were excluded; 5,361 Q1/Q3 calls were regenerated with the original budgets (700/480). Q4
   was dropped (no model states a confidence on Q4). Pillar D results use the regenerated responses.

3. Baseline provenance (Pillar B)
   The baseline is the original core-run response for qwen25vl, llava16, chexagent and huatuogpt, not a fresh run
   under identical settings. For llava16 the share of responses with no stated confidence differs a lot between
   baseline (39%), RAG (14%) and contrastive (28%); the cause has not been established.

4. Ground-truth coverage limits (expected, not a pipeline bug)
   Histopathology misclassification (class 3) can be fully checked only for the NCT-CRC subset (about 42% of
   histopathology records, 3 tissue classes); the PatchCamelyon subset (about 58%) only has binary tumor
   presence. See raw/gt_coverage_notes.json.

5. Judge and label quality
   Labels come from a 7B local judge plus automatic Layer-1 checks; no human validation of the full label set exists
   yet. Within-pipeline relabeling changed 1.1% (strict) and 2.8% (claim-level) of labels. About 5% of Pillar D
   responses reused labels from the earlier core run (97% / 87% agreement on 60 checked responses). 9 + 60 Pillar D
   and 45 Pillar B judge outputs could not be parsed and were left unlabeled.

6. Statistical limits
   One run per cell (no run-to-run variance); Pillar B has ten unadjusted paired comparisons; Pillar D has four
   independent decoding settings and five models; Pillar E and C use only 12 models (3 for specialists).

7. Operational notes (no effect on results)
   The runs were interrupted several times by power loss and restarts, and slowed for a period while other software was running;
   every pipeline stage is resume-safe and re-scans its output file, so interruptions lost time, not data.
   No duplicate records were found in the Pillar B outputs.

8. Scope limits (stated, not defects)
   Evaluation is English-only; cross-lingual extension is left to future work.
   Proprietary API models (for example GPT-4o and Gemini) were not evaluated (no funding); the pipeline is model-agnostic.
```
