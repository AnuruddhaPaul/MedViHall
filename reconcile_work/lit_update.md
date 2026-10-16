# MedViHall literature update

Run date: 2026-10-13. Search window: 2026-06-01 to 2026-10-13, plus a back-sweep 2025-09-01 to 2026-05-31 for papers missed in the June 2026 search.
Tools: `lit_tool.py` (arXiv API, OpenAlex, DOI content negotiation), driver scripts `run_lit_queries.py`, `run_lit_queries2.py`, `run_lit_backsweep.py`, `run_citing.py`; every response cached in `lit_cache/`.

## How to read this
- **Verified** = the record was fetched from a primary source (arXiv API for arXiv ids; the DOI registrar via doi.org content negotiation, Crossref, the medRxiv API or the publisher landing page for the others) and the abstract was read. Only verified papers are in the table and in `lit_update.bib`.
- **Read** column = how much I actually read. `full text` means I read the arXiv HTML rendering (for several, only the first ~100k characters were returned). `abstract only` means I did NOT read the paper: re-read before quoting numbers.
- Contribution numbers: 1 SMHR/CHR/SRI; 2 fingerprints across four modalities (three with no prior benchmark); 3 specialization paradox; 4 cross-modal safety transfer; 5 calibration robustness across decoding; 6 comparative mitigation (RAG, contrastive decoding; the planned fine-tuning arm was dropped); 7 causal stage localization; 8 context-occlusion robustness. Overlap values: `direct` / `partial`; contributions not listed = none.
- I did not read the MedViHall implementation of contribution 8; I interpreted 'context-occlusion robustness' as removing or masking image regions or accompanying context and measuring the change. If that is wrong, re-rate SHOVIR and MC-CXR.
- A paper tagged `missed before` was already public before 2026-06-01 and is not on the known list.

## Summary

45 verified papers triaged: 5 HIGH, 21 MEDIUM, 19 LOW (the known papers are re-listed because their status matters).

## Table of verified papers (HIGH, then MEDIUM, then LOW)

| Level | Paper | Posted | Version / status | Overlap with contributions | Read | Flags |
|---|---|---|---|---|---|---|
| HIGH | [Errors, Hallucinations, and Clinical Impact of General-Purpose Multimodal Large Language Models](https://doi.org/10.64898/2026.09.18.26363369) | 2026-09-24 | v1 | 1:partial; 2:direct | abstract only (medRxiv API); full text blocked (HTTP 403) |  |
| HIGH | [SHOVIR: A Benchmark for Evaluating Vision Shortcut Learning in Radiology Report Generation](https://arxiv.org/abs/2606.30201) | 2026-06-29 | v2 (updated 2026-07-22) | 8:direct | full text (arXiv HTML) |  |
| HIGH | [ClinHallu: A Benchmark for Diagnosing Stage-Wise Hallucinations in Medical MLLM Reasoning](https://arxiv.org/abs/2606.14697) | 2026-06-12 | v1 (updated 2026-06-12) | 2:partial; 3:partial; 6:partial; 7:direct | full text (arXiv HTML) | known |
| HIGH | [Hallucination in Medical Imaging AI: A Cross-Modality Analytical Framework for Taxonomy, Detect](https://arxiv.org/abs/2606.13211) | 2026-06-11 | v1 (updated 2026-06-11) | 1:partial; 2:partial; 3:direct; 6:partial | full text (arXiv HTML) |  |
| HIGH | [MedVH: Towards Systematic Evaluation of Hallucination for Large Vision Language Models in the M](https://arxiv.org/abs/2407.02730) | 2024-07-03 | v1 (updated 2024-07-03) | 3:direct | abstract (arXiv API); known paper | known |
| MEDIUM | [CRAFT: Causal Responsibility and Failure Tracing in Medical Vision Language Models](https://arxiv.org/abs/2609.38810) | 2026-09-30 | v2 (updated 2026-10-02) | 7:partial; 8:partial | full text (arXiv HTML, first 100k chars) |  |
| MEDIUM | [Contamination, Prior, or Evidence? Decomposing and Training Evidence Use in Whole-Slide Vision-](https://arxiv.org/abs/2609.32185) | 2026-09-26 | v1 (updated 2026-09-26) | 2:partial; 8:partial | abstract (arXiv API) |  |
| MEDIUM | [When Retrieval Hurts: Measuring and Explaining Retrieval-Induced Hallucination in Chest X-ray R](https://arxiv.org/abs/2609.31733) | 2026-09-22 | v1 (updated 2026-09-22) | 6:partial | full text (arXiv HTML) |  |
| MEDIUM | [The illusion of clinical reasoning: a benchmark reveals the pervasive gap in vision-language mo](https://doi.org/10.1038/s41746-026-03191-3) | 2026-09-03 | published | 3:partial | abstract (arXiv version 2512.22275 via API; DOI metadata via registrar) |  |
| MEDIUM | [MVC-Bench: Benchmarking Calibration of Medical Vision-Language Models](https://arxiv.org/abs/2608.27004) | 2026-08-27 | v2 (updated 2026-08-31) | 3:partial; 4:partial; 5:partial | full text (arXiv HTML, first 100k chars) |  |
| MEDIUM | [MC-CXR: A Multi-Context Chest X-ray Benchmark for Context-Induced Disruption in Vision-Language](https://arxiv.org/abs/2608.24118) | 2026-08-25 | v1 (updated 2026-08-25) | 3:partial; 8:partial | full text (arXiv HTML, first 100k chars) |  |
| MEDIUM | [Evaluating the Diagnostic Robustness of Vision-Language Models Under Visual and Textual Perturb](https://arxiv.org/abs/2608.04885) | 2026-08-05 | v1 (updated 2026-08-05) | 5:partial; 8:partial | full text (arXiv HTML) |  |
| MEDIUM | [Confident but Unreliable: A Behavioral Safety Audit of Vision-Language Models on Brain MRI](https://arxiv.org/abs/2608.02790) | 2026-08-03 | v1 (updated 2026-08-03) | 2:partial; 3:partial; 5:partial | full text (arXiv HTML) |  |
| MEDIUM | [Hearsay: Vision-Language Medical Diagnoses Without an Image](https://arxiv.org/abs/2607.26886) | 2026-07-29 | v1 (updated 2026-07-29) | 2:partial; 4:partial | abstract (arXiv API) |  |
| MEDIUM | [Do Pathology Vision-Language Models Truly See Pathology?](https://arxiv.org/abs/2607.21065) | 2026-07-23 | v1 (updated 2026-07-23) | 3:partial; 8:partial | full text (arXiv HTML, first 100k chars) |  |
| MEDIUM | [Seeing Nothing, Saying Something: The Lack of Visual Grounding and Confabulation in Gemini Mode](https://doi.org/10.64898/2026.07.04.26357257) | 2026-07-07 | v1 | 2:partial; 5:partial; 8:partial | abstract only (medRxiv API) |  |
| MEDIUM | [Do Medical Vision Language Models Actually See? A Counterfactual Grounding Framework and Hard-N](https://arxiv.org/abs/2607.03647) | 2026-07-04 | v1 (updated 2026-07-04) | 6:partial; 8:partial | full text (arXiv HTML) |  |
| MEDIUM | [MedBench v5: A Dynamic, Process-Oriented, and Hallucination-Aware Benchmark for Clinical Multim](https://arxiv.org/abs/2606.24155) | 2026-06-23 | v4 (updated 2026-07-06) | 1:partial; 7:partial | full text (arXiv HTML, first 100k chars) |  |
| MEDIUM | [Uncertainty Is Not a Safety Net for Clinical VQA, but Can It Anticipate Model Failure?](https://arxiv.org/abs/2606.16583) | 2026-06-15 | v2 (updated 2026-09-03) | 5:partial | full text (arXiv HTML, first 100k chars) |  |
| MEDIUM | [Beyond Accuracy: A Multi-dimensional Cognitive Audit of Medical Large Vision–Language Models in](https://doi.org/10.3390/app16126064) | 2026-06-15 | published | 2:partial; 8:partial | abstract (Crossref) |  |
| MEDIUM | [Calibrated Triage, Not Autonomy: Confidence Estimation for Medical Vision-Language Models](https://arxiv.org/abs/2606.15910) | 2026-06-14 | v2 (updated 2026-08-20) | 4:partial; 5:partial | full text (arXiv HTML, first 100k chars) |  |
| MEDIUM | [Med-StepBench: A Hierarchical Reasoning Framework for Evaluating Hallucinations in Medical Visi](https://arxiv.org/abs/2605.10002) | 2026-05-11 | v1 (updated 2026-05-11) | 3:partial; 6:partial; 7:partial | full text (arXiv HTML) | missed before |
| MEDIUM | [Overconfidence and Calibration in Medical VQA: Empirical Findings and Hallucination-Aware Mitig](https://arxiv.org/abs/2604.02543) | 2026-04-02 | v2 (updated 2026-09-30) | 1:partial; 5:partial | full text (arXiv HTML, first 100k chars) | known |
| MEDIUM | [To Agree or To Be Right? The Grounding-Sycophancy Tradeoff in Medical Vision-Language Models](https://arxiv.org/abs/2603.22623) | 2026-03-23 | v1 (updated 2026-03-23) | 1:partial; 3:partial | full text (arXiv HTML) | missed before |
| MEDIUM | [Beyond Accuracy: Evaluating Visual Grounding In Multimodal Medical Reasoning](https://arxiv.org/abs/2603.03437) | 2026-03-03 | v1 (updated 2026-03-03) | 8:partial | abstract (arXiv API) |  |
| MEDIUM | [EchoBench: Benchmarking Sycophancy in Medical Large Vision-Language Models](https://arxiv.org/abs/2509.20146) | 2025-09-24 | v1 (updated 2025-09-24) | 2:partial; 3:partial | full text (arXiv HTML, first 100k chars) | missed before |
| LOW | [When Reasoning Hurts Confidence: Demographic Calibration of Vision-Language Models in Medicine ](https://doi.org/10.1609/aies.v9i4.43348) | 2026-10-11 | published | 5:partial | abstract (Crossref) |  |
| LOW | [Reliability Stress Tests and Decision-Time Routing for Chest X-ray Vision-Language Models](https://arxiv.org/abs/2610.02270) | 2026-10-01 | v1 (updated 2026-10-01) | 5:partial | abstract (arXiv API) |  |
| LOW | [Trustworthy Medical Multimodal Large Language Models: Taxonomy, Evaluation, and Benchmarks](https://doi.org/10.20944/preprints202609.0962.v1) | 2026-09-11 | published | - | abstract (Crossref) |  |
| LOW | [Counterfactual Anatomy-guided Spatial-Temporal Decoding for Annotation-Free Hallucination Mitig](https://arxiv.org/abs/2608.17427) | 2026-08-18 | v1 (updated 2026-08-18) | 6:partial; 8:partial | abstract (arXiv API) |  |
| LOW | [Talked Out of the Truth: Sycophancy in the Reasoning Chains of Multimodal Models](https://arxiv.org/abs/2608.28623) | 2026-07-30 | v3 (updated 2026-10-02) | 3:partial | abstract (arXiv API) |  |
| LOW | [Position, Not Provenance: Separating Reasoning Mediation from Sycophancy in Medical Vision-Lang](https://arxiv.org/abs/2607.27304) | 2026-07-29 | v1 (updated 2026-07-29) | 3:partial | abstract (arXiv API) |  |
| LOW | [Domain Pretraining Buys the Ranking, Not the Scale: A Calibration Audit of Medical Vision-Langu](https://doi.org/10.5281/zenodo.21310010) | 2026-07-11 | published | 3:partial; 5:partial | landing page (Zenodo) |  |
| LOW | [A Benchmark for Hallucination Detection in VLMs for Gastrointestinal Endoscopy](https://arxiv.org/abs/2606.24115) | 2026-06-23 | v1 (updated 2026-06-23) | 2:partial; 3:partial | full text (arXiv HTML) |  |
| LOW | [Confidence Calibration for Multimodal LLMs: An Empirical Study through Medical VQA](https://arxiv.org/abs/2606.19950) | 2026-06-18 | v1 (updated 2026-06-18) | 5:partial | abstract (arXiv API) |  |
| LOW | [Universal Boosts, Specific Suppressors: Sparse Autoencoder Steering of Medical Vision-Language ](https://arxiv.org/abs/2605.24977) | 2026-05-24 | v1 (updated 2026-05-24) | 6:partial | abstract (arXiv API) |  |
| LOW | [HalluCXR: Benchmarking and Mitigating Hallucinations in Medical Vision-Language Models for Ches](https://arxiv.org/abs/2605.20469) | 2026-05-19 | v1 (updated 2026-05-19) | 1:partial; 2:partial | abstract (arXiv API); known paper | known |
| LOW | [MedRCube: A Multidimensional Framework for Fine-Grained and In-Depth Evaluation of MLLMs in Med](https://arxiv.org/abs/2604.13756) | 2026-04-15 | v1 (updated 2026-04-15) | 8:partial | abstract (arXiv API) |  |
| LOW | [Anatomical Region-Guided Contrastive Decoding: A Plug-and-Play Strategy for Mitigating Hallucin](https://arxiv.org/abs/2512.17189) | 2025-12-19 | v1 (updated 2025-12-19) | 6:partial | abstract (arXiv API) | missed before |
| LOW | [Med-VCD: Mitigating Hallucination for Medical Large Vision Language Models through Visual Contr](https://arxiv.org/abs/2512.01922) | 2025-12-01 | v1 (updated 2025-12-01) | 6:partial | abstract (arXiv API) | missed before |
| LOW | [CCD: Mitigating Hallucinations in Radiology MLLMs via Clinical Contrastive Decoding](https://arxiv.org/abs/2509.23379) | 2025-09-27 | v2 (updated 2025-10-17) | 6:partial | abstract (arXiv API) | missed before |
| LOW | [Benchmarking and Mitigating Sycophancy in Medical Vision Language Models](https://arxiv.org/abs/2509.21979) | 2025-09-26 | v7 (updated 2026-05-28) | 3:partial | metadata only (arXiv API); known paper | known |
| LOW | [MedHallTune: An Instruction-Tuning Benchmark for Mitigating Medical Hallucination in Vision-Lan](https://arxiv.org/abs/2502.20780) | 2025-02-28 | v2 (updated 2026-07-30) | 6:partial | metadata only (arXiv API); known paper | known |
| LOW | [MedHallBench: A New Benchmark for Assessing Hallucination in Medical Large Language Models](https://arxiv.org/abs/2412.18947) | 2024-12-25 | v4 (updated 2025-03-28) | 1:partial | metadata only (arXiv API); known paper | known |
| LOW | [Detecting and Evaluating Medical Hallucinations in Large Vision Language Models](https://arxiv.org/abs/2406.10185) | 2024-06-14 | v2 (updated 2026-04-27) | 1:partial | metadata only (arXiv API); known paper | known |

## Known papers: new versions since the June search

| Paper | Latest version | Last updated | Note |
|---|---|---|---|
| HalluCXR: Benchmarking and Mitigating Hallucinations in Medical Vision (arXiv:2605.20469) | v1 | 2026-05-19 | no new version |
| ClinHallu: A Benchmark for Diagnosing Stage-Wise Hallucinations in Med (arXiv:2606.14697) | v1 | 2026-06-12 | no new version |
| Benchmarking and Mitigating Sycophancy in Medical Vision Language Mode (arXiv:2509.21979) | v7 | 2026-05-28 | v7; last update 2026-05-28, i.e. before the June search |
| Detecting and Evaluating Medical Hallucinations in Large Vision Langua (arXiv:2406.10185) | v2 | 2026-04-27 | v2, last update 2026-04-27 |
| MedHallTune: An Instruction-Tuning Benchmark for Mitigating Medical Ha (arXiv:2502.20780) | v2 | 2026-07-30 | **v2 posted 2026-07-30 - new since June** |
| MedHallBench: A New Benchmark for Assessing Hallucination in Medical L (arXiv:2412.18947) | v4 | 2025-03-28 | v4, last update 2025-03-28 (AAAI-25 Bridge Program) |
| Overconfidence and Calibration in Medical VQA: Empirical Findings and  (arXiv:2604.02543) | v2 | 2026-09-30 | **v2 posted 2026-09-30, 'COLM 2026 accepted' - new since June** |
| MedVH: Towards Systematic Evaluation of Hallucination for Large Vision (arXiv:2407.02730) | v1 | 2024-07-03 | v1 only |

Not re-checked because they have no arXiv record: CREST (medRxiv 2025.07.13), MedHEval, CARES, GMAI-MMBench. OpenAlex lists zero citing works since 2026-06-01 for HalluCXR, ClinHallu, 2509.21979, MedHallTune and Byun et al., and one or two (a systematic review and a query-expansion paper, both irrelevant) for Med-HallMark and MedHallBench, but its citation coverage of recent arXiv preprints is thin, so 'no citing paper found' is weak evidence.

## Details for HIGH and MEDIUM papers

### [HIGH] Errors, Hallucinations, and Clinical Impact of General-Purpose Multimodal Large Language Models in Histopathology

- **Citation:** Lami K, Agarwal S, Asaturova A, et al.. Errors, Hallucinations, and Clinical Impact of General-Purpose Multimodal Large Language Models in Histopathology. medRxiv preprint. doi:10.64898/2026.09.18.26363369.
- **Link:** https://doi.org/10.64898/2026.09.18.26363369
- **Posted:** 2026-09-24; **version:** v1
- **Read:** abstract only (medRxiv API); full text blocked (HTTP 403)
- **Overlap:** SMHR/CHR/SRI (partial), fingerprints, 4 modalities (direct)
- **What it does:** Retrospective multicentre study: 153 pathology cases from 20 organs, four general-purpose LLMs (ChatGPT-5.3, Gemini 3, Grok 4.20, Claude Opus 4.6) given multi-magnification histology images plus clinical context; 21 pathologists graded 612 outputs for correctness, error and hallucination type and burden, and clinical impact (0-4). Errors in 82.0% and hallucinations in 76.6% of outputs; fabricated histologic features were the dominant hallucination type (74.5%). General-purpose models only (no medical-tuned VLMs), 4 models, no released-benchmark claim visible in the abstract.
- **What we should do:** CHANGE A CLAIM. If the paper says histopathology had 'no prior hallucination benchmark/evaluation', that sentence is now false: this preprint is a clinician-graded hallucination study in histopathology with a clinical-impact scale. Reword to 'no prior multi-model, severity-weighted hallucination benchmark spanning medical-tuned and general VLMs', cite it, and compare its hallucination categories and impact scale with our severity levels. Read the full text before citing numbers.

### [HIGH] SHOVIR: A Benchmark for Evaluating Vision Shortcut Learning in Radiology Report Generation

- **Citation:** Filippo Ruffini, Marco Salmé, Rosa Sicilia et al.. SHOVIR: A Benchmark for Evaluating Vision Shortcut Learning in Radiology Report Generation. arXiv:2606.30201.
- **Link:** https://arxiv.org/abs/2606.30201
- **Posted:** 2026-06-29; **version:** v2 (updated 2026-07-22)
- **Read:** full text (arXiv HTML)
- **Overlap:** context-occlusion (direct)
- **What it does:** Benchmark for vision shortcut learning in chest X-ray report generation. Image-level occlusion (whole image replaced by matched Gaussian noise) and disease-level occlusion (OCO: noise on the target finding's boxes; DOCO: noise on co-occurring findings only; RO: random-box control) on MIMIC-CXR (2,160 images) and PadChest-GR (1,390), eight RRG models (CheXagent-2, CXRMate, Libra-v1, LLaVA-Rad, MAIRA-2, MedGemma, RaDialog, NV-Reason-CXR). Reports F1-CheXbert/RadGraph/GREEN drops (dFN, dOCO, dDOCO); it measures NO hallucination rate and NO severity, and it is chest X-ray only.
- **What we should do:** CHANGE A CLAIM if contribution 8 is worded as occlusion robustness in general: for chest X-ray, SHOVIR already does region-level occlusion with a context-occlusion control (DOCO). Cite and distinguish: our version must be tied to hallucination rate/severity and must cover the other three modalities. Consider running our CXR occlusion on SHOVIR's protocol for a direct comparison.

### [HIGH] ClinHallu: A Benchmark for Diagnosing Stage-Wise Hallucinations in Medical MLLM Reasoning

- **Citation:** Sicheng Yang, Hangjie Yuan, Wenjun Zhang et al.. ClinHallu: A Benchmark for Diagnosing Stage-Wise Hallucinations in Medical MLLM Reasoning. arXiv:2606.14697.
- **Link:** https://arxiv.org/abs/2606.14697
- **Posted:** 2026-06-12; **version:** v1 (updated 2026-06-12)
- **Read:** full text (arXiv HTML)
- **Overlap:** fingerprints, 4 modalities (partial), specialization paradox (partial), comparative mitigation (partial), causal stage localization (direct)
- **What it does:** Benchmark of 7,031 instances from VQA-RAD, PathVQA, MedFrameQA and MedXpertQA whose reasoning traces are split into Visual Recognition, Knowledge Recall and Reasoning Integration. Stage-replacement interventions (Rep-V, Rep-K, Rep-VK) supply the reference stage and measure the change in final accuracy, and per-stage hallucination rates are computed with an LLM judge (89.7-94.0% agreement with humans on a 10% subset). 11 models (Lingshu-7B and MedGemma-4B are the medical ones); only trace-supervised fine-tuning is tested as mitigation; no severity weighting, calibration or occlusion analysis; no formal medical-vs-general comparison (MedGemma-4B has the highest reasoning hallucination among open models, Lingshu-7B is on par with general models).
- **What we should do:** CHANGE A CLAIM. Do not present visual/knowledge/reasoning stage localization with replacement interventions as new. Cite ClinHallu as the origin and distinguish on: four named imaging modalities instead of four VQA sets, severity weighting, 12 VLMs, and the link between stage and mitigation effect (ClinHallu tests fine-tuning only). Check that our stage definitions and intervention protocol are not a re-implementation of its Eqs. 9-12.

### [HIGH] Hallucination in Medical Imaging AI: A Cross-Modality Analytical Framework for Taxonomy, Detection, and Mitigation under Regulatory Constraints

- **Citation:** Omar Alshahrani, Muzammil Behzad. Hallucination in Medical Imaging AI: A Cross-Modality Analytical Framework for Taxonomy, Detection, and Mitigation under Regulatory Constraints. arXiv:2606.13211.
- **Link:** https://arxiv.org/abs/2606.13211
- **Posted:** 2026-06-11; **version:** v1 (updated 2026-06-11)
- **Read:** full text (arXiv HTML)
- **Overlap:** SMHR/CHR/SRI (partial), fingerprints, 4 modalities (partial), specialization paradox (direct), comparative mitigation (partial)
- **What it does:** Structured narrative review (no new model evaluations) across CT, MRI, PET/SPECT, ultrasound and digital pathology that unifies three existing taxonomies and maps mitigation to FDA lifecycle guidance. Its claim that general-purpose models outperform medical-specialised ones on hallucination benchmarks rests on re-aggregated published numbers (Med-HALT: median hallucination-free 76.6% vs 51.3%, a text benchmark; no per-model list), and it proposes that narrow fine-tuning induces overfitting-driven confabulation. It uses the existing five-tier MediHall severity hierarchy and proposes no severity-weighted metric. The text has internal inconsistencies (p=0.012 in Sec. 3.4 vs p<0.001 in Sec. 4.2; 83.7% vs ~18% for human-in-the-loop reduction; a mismatched citation [8]).
- **What we should do:** CITE AND DISTINGUISH. It states the 'general beats medical-specialised' conclusion across modalities in print before us, so the novelty of contribution 3 cannot be 'first to say it'. Frame ours as the first controlled empirical measurement on 12 VLMs x 4 modalities with severity weighting. Do not reuse its numbers (inconsistent, re-aggregated, text-benchmark based).

### [HIGH] MedVH: Towards Systematic Evaluation of Hallucination for Large Vision Language Models in the Medical Context

- **Citation:** Zishan Gu, Changchang Yin, Fenglin Liu et al.. MedVH: Towards Systematic Evaluation of Hallucination for Large Vision Language Models in the Medical Context. arXiv:2407.02730.
- **Link:** https://arxiv.org/abs/2407.02730
- **Posted:** 2024-07-03; **version:** v1 (updated 2024-07-03)
- **Read:** abstract (arXiv API); known paper
- **Overlap:** specialization paradox (direct)
- **What it does:** MedVH (listed as known). Five hallucination tasks; experiments with general and medical LVLMs find that medical LVLMs, although good on standard tasks, are more susceptible to hallucination, often more than the general models.
- **What we should do:** CITE AND DISTINGUISH. This is the 2024 origin of the 'medical-tuned hallucinate more than general' direction. Contribution 3 must be positioned as scale, modality coverage and severity-weighting, not as discovery of the direction.

### [MEDIUM] CRAFT: Causal Responsibility and Failure Tracing in Medical Vision Language Models

- **Citation:** Chunzheng Zhu, Jiaqi Zeng, Hongbo Zhao et al.. CRAFT: Causal Responsibility and Failure Tracing in Medical Vision Language Models. arXiv:2609.38810.
- **Link:** https://arxiv.org/abs/2609.38810
- **Posted:** 2026-09-30; **version:** v2 (updated 2026-10-02)
- **Read:** full text (arXiv HTML, first 100k chars)
- **Overlap:** causal stage localization (partial), context-occlusion (partial)
- **What it does:** CRAFT (NeurIPS 2026 Spotlight). Mechanistic causal analysis of two failure modes in medical VLMs: 'arbitration failure' (misleading text overrides a correct image answer) and 'brake failure' (model commits when visual evidence is degraded, e.g. diagnostic regions masked). Localizes each to <1% of attention heads by layer patching/excision and verifies with probes and Tuned Lens; Hulu-Med 4B/7B/14B, InternVL3.5, Qwen3-VL-8B on VQA-RAD, SLAKE, HealMed-VQA. No hallucination rate or severity, no perception/knowledge/reasoning taxonomy, no systematic medical-vs-general comparison.
- **What we should do:** CITE AND DISTINGUISH. It is causal localization at head level for context-conflict and masking, which is adjacent to contributions 7 and 8 but not the same unit of analysis (heads vs reasoning stages). Use as support that causal interventions are an accepted method; state the difference explicitly.

### [MEDIUM] Contamination, Prior, or Evidence? Decomposing and Training Evidence Use in Whole-Slide Vision-Language Models

- **Citation:** Wenhao Zhang, Zhongliang Zhou, Shiyuan Zhang et al.. Contamination, Prior, or Evidence? Decomposing and Training Evidence Use in Whole-Slide Vision-Language Models. arXiv:2609.32185.
- **Link:** https://arxiv.org/abs/2609.32185
- **Posted:** 2026-09-26; **version:** v1 (updated 2026-09-26)
- **Read:** abstract (arXiv API)
- **Overlap:** fingerprints, 4 modalities (partial), context-occlusion (partial)
- **What it does:** CleanSlide: contamination-audited TCGA VQA benchmark (149K questions over 9,985 slides); finds most public pathology VLMs change little when given a whole-slide image, an annotated lesion, or no image at all; proposes Pair-DPO over counterfactual evidence pairs.
- **What we should do:** CITE as histopathology evidence-use prior art (contribution 8) and as a fine-tuning mitigation (contribution 6). Read the full text.

### [MEDIUM] When Retrieval Hurts: Measuring and Explaining Retrieval-Induced Hallucination in Chest X-ray Report Generation

- **Citation:** Emmanuel Idoko, Abdusshakur Olabisi, Shiloh Oni et al.. When Retrieval Hurts: Measuring and Explaining Retrieval-Induced Hallucination in Chest X-ray Report Generation. arXiv:2609.31733.
- **Link:** https://arxiv.org/abs/2609.31733
- **Posted:** 2026-09-22; **version:** v1 (updated 2026-09-22)
- **Read:** full text (arXiv HTML)
- **Overlap:** comparative mitigation (partial)
- **What it does:** Pilot (100 MIMIC-CXR studies) with frozen LLaVA-1.5 and BioMedCLIP retrieval: relevant retrieval doubles CheXbert F1 but retrieval-induced hallucination rises from 0.00 to 0.76 (0.98 with mismatched retrieval); embedding similarity does not predict harm; an oracle label-agreement gate removes 61% of unsupported evidence. Compares only retrieval conditions - not RAG vs contrastive decoding vs fine-tuning; no severity weighting; RGCA gate not evaluated end to end.
- **What we should do:** CITE AS SUPPORT / COMPARE. Directly relevant to our RAG arm: if our RAG result is positive, discuss why it differs (their harm is on a general LLaVA-1.5 generator with report retrieval); if negative, it corroborates. Does not threaten the head-to-head comparison claim.

### [MEDIUM] The illusion of clinical reasoning: a benchmark reveals the pervasive gap in vision-language models for clinical competency

- **Citation:** Dingyu Wang, Zimu Yuan, Jiajun Liu et al.. The illusion of clinical reasoning: a benchmark reveals the pervasive gap in vision-language models for clinical competency. npj Digital Medicine. doi:10.1038/s41746-026-03191-3.
- **Link:** https://doi.org/10.1038/s41746-026-03191-3
- **Posted:** 2026-09-03; **version:** published
- **Read:** abstract (arXiv version 2512.22275 via API; DOI metadata via registrar)
- **Overlap:** specialization paradox (partial)
- **What it does:** npj Digital Medicine. Bones and Joints benchmark (1,245 orthopaedics/sports-medicine questions) on 14 VLMs and 6 LLMs: >90% on multiple choice but ~60% on open-ended tasks needing image integration, text-driven hallucinations, and 'medical-specific models showed no consistent advantage over general-purpose' ones (sentence truncated in the OpenAlex abstract; the arXiv v1 abstract 2512.22275 is the primary text I read).
- **What we should do:** CITE as peer-reviewed evidence that medical-specific models have no consistent advantage (contribution 3). Check the exact wording in the published version.

### [MEDIUM] MVC-Bench: Benchmarking Calibration of Medical Vision-Language Models

- **Citation:** Ashshak Sharifdeen, Shihab Aaqil Ahamed, Ufaq Khan et al.. MVC-Bench: Benchmarking Calibration of Medical Vision-Language Models. arXiv:2608.27004.
- **Link:** https://arxiv.org/abs/2608.27004
- **Posted:** 2026-08-27; **version:** v2 (updated 2026-08-31)
- **Read:** full text (arXiv HTML, first 100k chars)
- **Overlap:** specialization paradox (partial), cross-modal safety transfer (partial), calibration robustness (partial)
- **What it does:** MVC-Bench (EMNLP 2026 Findings): calibration benchmark for medical image CLASSIFICATION with eight CLIP-type backbones (4 generic, 4 medical: PLIP, QuiltNet, MedCLIP, BioMedCLIP) on fundus, histopathology and chest X-ray, >1,638 experiments; stability to prompt template and random seed; medical pretraining generally lowers ECE but MedCLIP-X-ray is a counterexample. No generative/hallucination evaluation, no decoding or temperature sweep.
- **What we should do:** CITE AND DISTINGUISH on contribution 5: calibration robustness here is across prompt templates and seeds for classifiers, ours is across decoding settings for generative VLMs. Its 'medical pretraining improves calibration' finding is evidence against a blanket specialization paradox; discuss.

### [MEDIUM] MC-CXR: A Multi-Context Chest X-ray Benchmark for Context-Induced Disruption in Vision-Language Models

- **Citation:** Junhyeok Lee, Songsoo Kim, Kyu Sung Choi. MC-CXR: A Multi-Context Chest X-ray Benchmark for Context-Induced Disruption in Vision-Language Models. arXiv:2608.24118.
- **Link:** https://arxiv.org/abs/2608.24118
- **Posted:** 2026-08-25; **version:** v1 (updated 2026-08-25)
- **Read:** full text (arXiv HTML, first 100k chars)
- **Overlap:** specialization paradox (partial), context-occlusion (partial)
- **What it does:** MC-CXR (Findings of EMNLP 2026): 240 chest X-ray cases expanded to 2,522 instances with paired reliable vs misleading context (text notes, prior CXR, PACS-style overlay arrows); ten VLMs (5 general, 2 medical: MedGemma-1.5-4B and NV-Reason-CXR-3B, 3 closed). Switch-to-wrong rates 45.6-78.1% for misleading text; text override is 57-point more likely to align with the misleading label than visual context; domain specialization 'does not insulate against textual override'. Adds annotations (arrows), does not occlude image regions. CXR only.
- **What we should do:** CITE AND DISTINGUISH on contribution 8: it perturbs context, we occlude/remove it; its medical-vs-general finding on textual override is supporting evidence for contribution 3.

### [MEDIUM] Evaluating the Diagnostic Robustness of Vision-Language Models Under Visual and Textual Perturbations

- **Citation:** Ali Khoramfar, Mohammad Javad Dousti, Alireza Mohamadian et al.. Evaluating the Diagnostic Robustness of Vision-Language Models Under Visual and Textual Perturbations. arXiv:2608.04885.
- **Link:** https://arxiv.org/abs/2608.04885
- **Posted:** 2026-08-05; **version:** v1 (updated 2026-08-05)
- **Read:** full text (arXiv HTML)
- **Overlap:** calibration robustness (partial), context-occlusion (partial)
- **What it does:** Brain-MRI (90 patients, 4,091 slices) robustness test of GPT-5.4, Gemini-2.5-Pro, Qwen3-VL-32B and MedGemma-27B under slice reordering and label-position swaps; removing all lesion-containing slices (a negative control) still yields a forced diagnosis in up to 76.1% of cases (MedGemma-27B, T1CE). No hallucination or severity metric.
- **What we should do:** CITE as prior art for evidence-removal controls (contribution 8).

### [MEDIUM] Confident but Unreliable: A Behavioral Safety Audit of Vision-Language Models on Brain MRI

- **Citation:** Amir Sabbaghziarani, Mohammadsajad Abavisani, Sergey Plis. Confident but Unreliable: A Behavioral Safety Audit of Vision-Language Models on Brain MRI. arXiv:2608.02790.
- **Link:** https://arxiv.org/abs/2608.02790
- **Posted:** 2026-08-03; **version:** v1 (updated 2026-08-03)
- **Read:** full text (arXiv HTML)
- **Overlap:** fingerprints, 4 modalities (partial), specialization paradox (partial), calibration robustness (partial)
- **What it does:** Behavioural audit of six VLMs (MedGemma-4B the only medical specialist) on 4,102 brain-MRI images; greedy decoding. ECE 0.27-0.40, 33-46% high-confidence errors; MedGemma-4B ECE 0.381 vs 0.272 for Qwen2.5-VL-7B, but its open-ended hallucination rate (0.061) is the LOWEST in the panel and abstention on non-brain controls drops from 0.739 (base) to 0.504.
- **What we should do:** CITE AS COUNTER-EVIDENCE for contribution 3: a medical model with the lowest open-ended hallucination rate on one modality. Our paper should say under which measure and modality the paradox holds.

### [MEDIUM] Hearsay: Vision-Language Medical Diagnoses Without an Image

- **Citation:** Siddharth Vohra. Hearsay: Vision-Language Medical Diagnoses Without an Image. arXiv:2607.26886.
- **Link:** https://arxiv.org/abs/2607.26886
- **Posted:** 2026-07-29; **version:** v1 (updated 2026-07-29)
- **Read:** abstract (arXiv API)
- **Overlap:** fingerprints, 4 modalities (partial), cross-modal safety transfer (partial)
- **What it does:** Workshop paper (non-archival, TrustVLM @ ICMR 2026). Frontier VLMs (Claude Opus-4.7, GPT-5.4, Gemini-3.1-Pro) asked for a diagnosis with NO image on chest X-ray, brain MRI and dermatology confabulate a diagnosis that shifts with the stated demographics; a 'hedged regime' acknowledges the missing image in prose but still names a disease in the structured field.
- **What we should do:** CITE as prior evidence of cross-modality confabulation in dermatology and CXR (fingerprint-style findings, contribution 2) and as support for the no-image control in contribution 8. Read the full text before quoting numbers.

### [MEDIUM] Do Pathology Vision-Language Models Truly See Pathology?

- **Citation:** Chengyang Zhang, Wenchuan Zhang, Bo Li et al.. Do Pathology Vision-Language Models Truly See Pathology?. arXiv:2607.21065.
- **Link:** https://arxiv.org/abs/2607.21065
- **Posted:** 2026-07-23; **version:** v1 (updated 2026-07-23)
- **Read:** full text (arXiv HTML, first 100k chars)
- **Overlap:** specialization paradox (partial), context-occlusion (partial)
- **What it does:** PathBind benchmark for pathology VLMs: Gemini-3-Pro reaches 53.5% on five public pathology VQA sets with no image; domain-trained models bind to the image less than their general base (Patho-R1-7B vs Qwen2.5-VL-7B: 5.8-point lower multimodal gain, 3.7-point lower attention IoU), though PathGen-LLaVA and HuatuoGPT-Vision gain 4.1 and 2.9 points, so the pattern is inconsistent. Measures neither hallucination nor severity.
- **What we should do:** CITE as support for contribution 3 in pathology and for no-image controls (contribution 8), noting the mixed result.

### [MEDIUM] Seeing Nothing, Saying Something: The Lack of Visual Grounding and Confabulation in Gemini Models for Histopathology

- **Citation:** Hasan MM, Tozal ME, Ayhan MS. Seeing Nothing, Saying Something: The Lack of Visual Grounding and Confabulation in Gemini Models for Histopathology. medRxiv preprint. doi:10.64898/2026.07.04.26357257.
- **Link:** https://doi.org/10.64898/2026.07.04.26357257
- **Posted:** 2026-07-07; **version:** v1
- **Read:** abstract only (medRxiv API)
- **Overlap:** fingerprints, 4 modalities (partial), calibration robustness (partial), context-occlusion (partial)
- **What it does:** Gemini 3.0 Flash and 3.1 Pro on a histopathology classification set (98.75-100% accurate on real images) and an adversarial set of blank white images labelled benign/malignant: Gemini-pro fabricates detailed histology with mean confidence ~0.95 ('confident confabulation'), confabulation rate 77.8% at T=0.0, 44.4% at T=0.5, 66.7% at T=1.0; Gemini-flash 0% at all temperatures.
- **What we should do:** CITE for histopathology confabulation and as the only item found that varies temperature when measuring a hallucination-type behaviour in a medical VLM (partial overlap with contribution 5's decoding-setting axis). Read the full text.

### [MEDIUM] Do Medical Vision Language Models Actually See? A Counterfactual Grounding Framework and Hard-Negative Contrastive Training for Visually-Reliant Medical VLMs

- **Citation:** Anas Zafar, Leema Krishna Murali, Siddhant Bharadwaj et al.. Do Medical Vision Language Models Actually See? A Counterfactual Grounding Framework and Hard-Negative Contrastive Training for Visually-Reliant Medical VLMs. arXiv:2607.03647.
- **Link:** https://arxiv.org/abs/2607.03647
- **Posted:** 2026-07-04; **version:** v1 (updated 2026-07-04)
- **Read:** full text (arXiv HTML)
- **Overlap:** comparative mitigation (partial), context-occlusion (partial)
- **What it does:** Counterfactual image-substitution framework (blank, shuffled, no-image, CLIP hard-negative, corrupted incl. 30% patch occlusion) with Visual Reliance Score and Visual Hallucination Rate; CORAL, a LoRA fine-tune of Qwen2.5-VL-7B with a contrastive grounding objective, lowers VHR from 0.140 to 0.060. Four closed-form VQA sets (PathVQA, PMC-VQA, SLAKE, VQA-RAD), four 7B systems plus a 3B; no severity; no direct test of medical-tuned vs general reliance.
- **What we should do:** CITE AND DISTINGUISH on contribution 8 (image-level counterfactuals vs our context occlusion) and as another fine-tuning mitigation datapoint for contribution 6.

### [MEDIUM] MedBench v5: A Dynamic, Process-Oriented, and Hallucination-Aware Benchmark for Clinical Multimodal Models

- **Citation:** Jinru Ding, Chuchu Jiang, Lu Lu et al.. MedBench v5: A Dynamic, Process-Oriented, and Hallucination-Aware Benchmark for Clinical Multimodal Models. arXiv:2606.24155.
- **Link:** https://arxiv.org/abs/2606.24155
- **Posted:** 2026-06-23; **version:** v4 (updated 2026-07-06)
- **Read:** full text (arXiv HTML, first 100k chars)
- **Overlap:** SMHR/CHR/SRI (partial), causal stage localization (partial)
- **What it does:** MedBench v5: process-oriented benchmark with hallucination propagation monitoring (initiation, propagation, anchoring, hallucination-contradiction interaction), omission/contradiction/evidence-delay stressors, and a five-node reasoning audit; LLM, multimodal and agent tracks, MedGemma 1.5 the only medical model (lowest on every track). No severity weighting, no mitigation.
- **What we should do:** CITE AND DISTINGUISH: process-level hallucination tracking in multi-turn clinical scenarios, not stage-wise causal localization on imaging.

### [MEDIUM] Uncertainty Is Not a Safety Net for Clinical VQA, but Can It Anticipate Model Failure?

- **Citation:** Arnisa Fazla, Alberto Testoni, Ameen Abu-Hanna et al.. Uncertainty Is Not a Safety Net for Clinical VQA, but Can It Anticipate Model Failure?. arXiv:2606.16583.
- **Link:** https://arxiv.org/abs/2606.16583
- **Posted:** 2026-06-15; **version:** v2 (updated 2026-09-03)
- **Read:** full text (arXiv HTML, first 100k chars)
- **Overlap:** calibration robustness (partial)
- **What it does:** Findings of EMNLP 2026. Eight uncertainty-estimation methods on 12 VLMs (10 general, MedGemma-4B/27B) over GMAI-MMBench, 210 samples from each of 8 modalities (CT, MRI, endoscopy, histopathology, fundus, X-ray, microscopy, dermoscopy). Nucleus sampling at fixed p=0.9, T=0.6 (no sweep). The two MedGemma models are the worst calibrated; under 'none-of-the-above' perturbation accuracy collapses while uncertainty barely changes.
- **What we should do:** CITE AND DISTINGUISH on contribution 5 (fixed decoding, multiple-choice, no hallucination rate) and as support for contribution 3 (medical models worst calibrated). It also covers the same eight modalities as GMAI-MMBench, relevant to contribution 2.

### [MEDIUM] Beyond Accuracy: A Multi-dimensional Cognitive Audit of Medical Large Vision–Language Models in Fundus Image Interpretation

- **Citation:** Jingling Zhang, Shuting Zheng, Xiangfei Liu et al.. Beyond Accuracy: A Multi-dimensional Cognitive Audit of Medical Large Vision–Language Models in Fundus Image Interpretation. Applied Sciences. doi:10.3390/app16126064.
- **Link:** https://doi.org/10.3390/app16126064
- **Posted:** 2026-06-15; **version:** published
- **Read:** abstract (Crossref)
- **Overlap:** fingerprints, 4 modalities (partial), context-occlusion (partial)
- **What it does:** Cognitive Audit Framework for six 7B-31B fundus LVLMs on FunBench: textual dependency via modality ablation, lesion-diagnosis logical consistency, chain-of-thought fidelity, option-permutation robustness. High accuracy coexists with measurable textual dependency and logical inconsistency. No hallucination rate or severity.
- **What we should do:** CITE as ophthalmology prior art for image-ablation robustness (contributions 2 and 8).

### [MEDIUM] Calibrated Triage, Not Autonomy: Confidence Estimation for Medical Vision-Language Models

- **Citation:** Reza Khanmohammadi, Kundan Thind, Mohammad M. Ghassemi. Calibrated Triage, Not Autonomy: Confidence Estimation for Medical Vision-Language Models. arXiv:2606.15910.
- **Link:** https://arxiv.org/abs/2606.15910
- **Posted:** 2026-06-14; **version:** v2 (updated 2026-08-20)
- **Read:** full text (arXiv HTML, first 100k chars)
- **Overlap:** cross-modal safety transfer (partial), calibration robustness (partial)
- **What it does:** Nine confidence estimators, five open-weight LVLMs (general), three medical VQA datasets (GMAI-MMBench, SLAKE, PATH-VQA) with probes trained only on natural images (GQA) and applied to medicine; greedy decoding, no variation. Overconfidence is domain-specific, no estimator is best across domains, deferral capacity tracks base competence, and no estimator reliably lowers confidence when the image is replaced.
- **What we should do:** CITE AND DISTINGUISH on contribution 5 (greedy only) and contribution 4 (natural-to-medical transfer of a confidence signal, not cross-modality transfer of safety behaviour).

### [MEDIUM] Med-StepBench: A Hierarchical Reasoning Framework for Evaluating Hallucinations in Medical Vision-Language Models

- **Citation:** Minh Khoi Nguyen, Dai Lam Le, Amir Reza Jafari et al.. Med-StepBench: A Hierarchical Reasoning Framework for Evaluating Hallucinations in Medical Vision-Language Models. arXiv:2605.10002.
- **Link:** https://arxiv.org/abs/2605.10002
- **Posted:** 2026-05-11; **version:** v1 (updated 2026-05-11)
- **Read:** full text (arXiv HTML)
- **Overlap:** specialization paradox (partial), comparative mitigation (partial), causal stage localization (partial)
- **What it does:** Med-StepBench (IJCAI-ECAI 2026; submitted 2026-05-11, so it predates the June search and was missed). Step-wise hallucination benchmark for 3D oncological PET/CT (>12,000 images, >1M image-statement pairs) with four expert stages: anatomical mapping, lesion identification, feature characterization, diagnostic synthesis; binary hallucination per step scored with P/R/F1. 11 models (general: GPT-4o, Gemini 2.5, Qwen3-VL, LLaVA-7B; medical: LLaVA-Med, MedM-VL 2D/3D, Med-Flamingo, M3D), no explicit medical-vs-general verdict. Knowledge injection (RAG-like) gives marginal/inconsistent gains; no contrastive decoding or fine-tuning; no severity weighting; no calibration/occlusion; no formal causal attribution. Clinician rationales reduce detection more than LLM rationales ('clinically plausible narratives override visual verification').
- **What we should do:** CITE AND DISTINGUISH on contribution 7: it localizes WHERE (which diagnostic step) but does not run causal interventions separating perception, knowledge and reasoning. Also a second stage-wise prior work (with ClinHallu) and a third-modality (PET/CT) hallucination benchmark. Cite its knowledge-injection result next to our RAG result.

### [MEDIUM] Overconfidence and Calibration in Medical VQA: Empirical Findings and Hallucination-Aware Mitigation

- **Citation:** Ji Young Byun, Young-Jin Park, Jean-Philippe Corbeil et al.. Overconfidence and Calibration in Medical VQA: Empirical Findings and Hallucination-Aware Mitigation. arXiv:2604.02543.
- **Link:** https://arxiv.org/abs/2604.02543
- **Posted:** 2026-04-02; **version:** v2 (updated 2026-09-30)
- **Read:** full text (arXiv HTML, first 100k chars)
- **Overlap:** SMHR/CHR/SRI (partial), calibration robustness (partial)
- **What it does:** Known paper, NEW VERSION: v2 posted 2026-09-30 with comment 'COLM 2026 accepted' (v1 2026-04-02). Calibration study on Qwen3-VL, InternVL3, LLaVA-NeXT (2B-38B; general models only) across VQA-RAD, SLAKE, VQA-Med-2019; overconfidence persists with scale and prompting; Platt scaling beats prompt-based confidence; hallucination-aware calibration (VASE signal) improves ECE and AUROC. Temperature/sampling settings are not varied in the part I read; no medical-specialised model is evaluated (LLaVA-Med named as future work). The v1-to-v2 changelog is not visible.
- **What we should do:** CITE AND DISTINGUISH; update the citation to the COLM 2026 version. It is the closest calibration prior art: ours differs by decoding-setting robustness, medical-tuned models and four modalities. Re-read v2 diff before submission.

### [MEDIUM] To Agree or To Be Right? The Grounding-Sycophancy Tradeoff in Medical Vision-Language Models

- **Citation:** OFM Riaz Rahman Aranya, Kevin Desai. To Agree or To Be Right? The Grounding-Sycophancy Tradeoff in Medical Vision-Language Models. arXiv:2603.22623.
- **Link:** https://arxiv.org/abs/2603.22623
- **Posted:** 2026-03-23; **version:** v1 (updated 2026-03-23)
- **Read:** full text (arXiv HTML)
- **Overlap:** SMHR/CHR/SRI (partial), specialization paradox (partial)
- **What it does:** Six VLMs (general: LLaVA-1.5-7B, Qwen3-VL-8B, IDEFICS2-8B; medical: LLaVA-Med, MedVLM-R1, MedGemma) on VQA-RAD, SLAKE, PathVQA (1,151 cases). Finds a grounding-sycophancy trade-off: the lowest-hallucination model is the most sycophantic and the most pressure-resistant model (general) hallucinates more than all three medical models; 'medical fine-tuning does not consistently improve safety'. Defines a Clinical Safety Index (geometric mean of grounding, autonomy, calibration) that does NOT weight by clinical severity.
- **What we should do:** CITE AND DISTINGUISH. Evidence that the medical-vs-general ordering is mixed on this sample, so contribution 3 must state conditions (modality, metric, model size). CSI is a composite safety index, not a severity-weighted hallucination rate, but reviewers may ask how SMHR differs.

### [MEDIUM] Beyond Accuracy: Evaluating Visual Grounding In Multimodal Medical Reasoning

- **Citation:** Anas Zafar, Leema Krishna Murali, Ashish Vashist. Beyond Accuracy: Evaluating Visual Grounding In Multimodal Medical Reasoning. arXiv:2603.03437.
- **Link:** https://arxiv.org/abs/2603.03437
- **Posted:** 2026-03-03; **version:** v1 (updated 2026-03-03)
- **Read:** abstract (arXiv API)
- **Overlap:** context-occlusion (partial)
- **What it does:** Counterfactual evaluation (real, blank, shuffled images) on PathVQA, PMC-VQA, SLAKE, VQA-RAD with Visual Reliance Score, Image Sensitivity and a Hallucinated Visual Reasoning Rate (HVRR): 38-43% of visual claims are ungrounded; text-only RLVR keeps 81% of VQA-RAD performance with blank images.
- **What we should do:** CITE as prior art for image-removal controls (contribution 8). Read full text before comparing HVRR to our hallucination rate.

### [MEDIUM] EchoBench: Benchmarking Sycophancy in Medical Large Vision-Language Models

- **Citation:** Botai Yuan, Yutian Zhou, Yingjie Wang et al.. EchoBench: Benchmarking Sycophancy in Medical Large Vision-Language Models. arXiv:2509.20146.
- **Link:** https://arxiv.org/abs/2509.20146
- **Posted:** 2025-09-24; **version:** v1 (updated 2025-09-24)
- **Read:** full text (arXiv HTML, first 100k chars)
- **Overlap:** fingerprints, 4 modalities (partial), specialization paradox (partial)
- **What it does:** EchoBench (submitted 2025-09-24): sycophancy benchmark with 2,122 images, 18 departments and 20 modalities (including DERM, FUNDUS, HISTO, OCT, XR), 24 LVLMs. Medical-specific models average ~83.0% sycophancy vs ~74.7% for 12 general open-source models; LLaVA-Med V1.5 reaches 98.75% sycophancy vs 55.39% for its base LLaVA-V1.5-7B and has lower unbiased accuracy. Measures sycophancy, not hallucination; no severity weighting.
- **What we should do:** CITE AS SUPPORT for contribution 3 (medical specialisation can worsen reliability, with a base-model control) and as prior art for modality-level breakdowns of reliability including the three modalities we call new. It is a different paper from the known sycophancy paper 2509.21979 (different arXiv ID and title, submitted two days earlier) and was not on the known list; cite both.

## LOW-threat related papers

- **When Reasoning Hurts Confidence: Demographic Calibration of Vision-Language Models in Medicine (Extended Abstract)** ([link](https://doi.org/10.1609/aies.v9i4.43348); 2026-10-11; published; read: abstract (Crossref)). AIES 2026 extended abstract: demographic calibration of GPT-4o, R1-Onevision-7B and Qwen2.5-VL-7B on skin-lesion and CXR classification using token probability, verbalized confidence and self-consistency; temperature scaling cuts ECE by up to 96% but leaves equity gaps unchanged. *Action:* Cite for calibration signals on dermatology and CXR (contribution 5).
- **Reliability Stress Tests and Decision-Time Routing for Chest X-ray Vision-Language Models** ([link](https://arxiv.org/abs/2610.02270); 2026-10-01; v1 (updated 2026-10-01); read: abstract (arXiv API)). Reliability stress tests of three CXR VLMs (CheXagent, MedGemma-4B/27B) over three prompt styles and two workflows; exact-match accuracy overstates conservative models that default to 'Normal'. *Action:* Cite for prompt-sensitivity of CXR VLMs (contribution 5 context).
- **Trustworthy Medical Multimodal Large Language Models: Taxonomy, Evaluation, and Benchmarks** ([link](https://doi.org/10.20944/preprints202609.0962.v1); 2026-09-11; published; read: abstract (Crossref)). Preprints.org survey of trustworthiness (truthfulness, robustness, fairness, safety, privacy, explainability) in medical MLLMs. *Action:* Cite as background survey if needed.
- **Counterfactual Anatomy-guided Spatial-Temporal Decoding for Annotation-Free Hallucination Mitigation in Medical VLMs** ([link](https://arxiv.org/abs/2608.17427); 2026-08-18; v1 (updated 2026-08-18); read: abstract (arXiv API)). CAST (MICCAI 2026): training-free counterfactual-anatomy-guided contrastive decoding; selects a region via the drop in answer likelihood under occlusion. *Action:* Cite as contrastive-decoding prior art in medical VLMs (contribution 6).
- **Talked Out of the Truth: Sycophancy in the Reasoning Chains of Multimodal Models** ([link](https://arxiv.org/abs/2608.28623); 2026-07-30; v3 (updated 2026-10-02); read: abstract (arXiv API)). Sycophancy benchmark for multimodal reasoning models including clinical (PathVQA) data; reasoning-level sycophancy reaches 95.7% under multi-turn pressure. *Action:* Cite for sycophancy context.
- **Position, Not Provenance: Separating Reasoning Mediation from Sycophancy in Medical Vision-Language Models** ([link](https://arxiv.org/abs/2607.27304); 2026-07-29; v1 (updated 2026-07-29); read: abstract (arXiv API)). CoT-Mediate: perturbs a clinical attribute inside LLaVA-Med's and MedGemma's own reasoning on 1,000 VQA-RAD samples each; contextual position, not stated provenance, determines whether reasoning is used. *Action:* Cite for medical VLM reasoning faithfulness.
- **Domain Pretraining Buys the Ranking, Not the Scale: A Calibration Audit of Medical Vision-Language Models** ([link](https://doi.org/10.5281/zenodo.21310010); 2026-07-11; published; read: landing page (Zenodo)). Single-author Zenodo preprint (2026-07-11): BiomedCLIP vs OpenAI CLIP (frozen ViT-B/16) on modality/anatomy classification from PMC-VQA; domain pretraining improves discrimination but is worse calibrated before temperature scaling in all four cells. *Action:* Optional citation, with caution: not peer reviewed, classification not generative.
- **A Benchmark for Hallucination Detection in VLMs for Gastrointestinal Endoscopy** ([link](https://arxiv.org/abs/2606.24115); 2026-06-23; v1 (updated 2026-06-23); read: full text (arXiv HTML)). MIUA 2026. Nine hallucination-detection methods on Gut-VLM (GI endoscopy, 4,392 test pairs), five VLMs (MedGemma-4B/27B, LLaVA-Med-7B, LLaVA-v1.6-7B, Lingshu-32B); hallucination rates 44.1-76.5%, the general model is in the middle of the medical ones; severity discussed only qualitatively; no mitigation. *Action:* Cite as evidence that another modality (endoscopy) already has a hallucination benchmark and for the mixed medical-vs-general ordering.
- **Confidence Calibration for Multimodal LLMs: An Empirical Study through Medical VQA** ([link](https://arxiv.org/abs/2606.19950); 2026-06-18; v1 (updated 2026-06-18); read: abstract (arXiv API)). Empirical study of confidence calibration of medical MLLMs on three medical VQA datasets with an interrogation-plus-expert-LLM method (ECE reduced ~40%); MICCAI 2025 per the arXiv comment. *Action:* Cite as calibration prior art (contribution 5).
- **Universal Boosts, Specific Suppressors: Sparse Autoencoder Steering of Medical Vision-Language Models** ([link](https://arxiv.org/abs/2605.24977); 2026-05-24; v1 (updated 2026-05-24); read: abstract (arXiv API)). Sparse-autoencoder residual steering of three radiology VLMs for CXR report hallucination; suppress directions are model-specific. *Action:* Cite as inference-time mitigation (contribution 6).
- **HalluCXR: Benchmarking and Mitigating Hallucinations in Medical Vision-Language Models for Chest Radiograph Interpretation** ([link](https://arxiv.org/abs/2605.20469); 2026-05-19; v1 (updated 2026-05-19); read: abstract (arXiv API); known paper). Known paper, no new version (v1, 2026-05-19). Chest-X-ray-only hallucination benchmark: 6 VLMs, 856 MIMIC-CXR images, 15,408 evaluations, eight-category taxonomy with clinical severity ratings, two-layer detector validated on 250 human annotations; 61.9-82.3% of outputs contain hallucinations; six-model ensemble cuts fabrication up to 84.8%. *Action:* Already known. It is the nearest prior art for contribution 1 (severity ratings) in CXR - keep the explicit SMHR-vs-HalluCXR comparison.
- **MedRCube: A Multidimensional Framework for Fine-Grained and In-Depth Evaluation of MLLMs in Medical Imaging** ([link](https://arxiv.org/abs/2604.13756); 2026-04-15; v1 (updated 2026-04-15); read: abstract (arXiv API)). MedRCube: 33 MLLMs, credibility subset reporting a positive association between shortcut behaviour and diagnostic performance. *Action:* Cite for shortcut behaviour (contribution 8).
- **Anatomical Region-Guided Contrastive Decoding: A Plug-and-Play Strategy for Mitigating Hallucinations in Medical VLMs** ([link](https://arxiv.org/abs/2512.17189); 2025-12-19; v1 (updated 2025-12-19); read: abstract (arXiv API)). ARCD: anatomical-region-guided contrastive decoding for medical VLMs, arguing global untargeted contrastive decoding can be unreliable in clinical settings. *Action:* Cite as contrastive-decoding prior art (contribution 6).
- **Med-VCD: Mitigating Hallucination for Medical Large Vision Language Models through Visual Contrastive Decoding** ([link](https://arxiv.org/abs/2512.01922); 2025-12-01; v1 (updated 2025-12-01); read: abstract (arXiv API)). Med-VCD: sparse visual-contrastive decoding for medical LVLMs. *Action:* Cite as contrastive-decoding prior art (contribution 6).
- **CCD: Mitigating Hallucinations in Radiology MLLMs via Clinical Contrastive Decoding** ([link](https://arxiv.org/abs/2509.23379); 2025-09-27; v2 (updated 2025-10-17); read: abstract (arXiv API)). CCD: Clinical Contrastive Decoding for radiology MLLMs (training-free, retrieval-free; up to +17% RadGraph-F1 on MIMIC-CXR); also published at ACL 2026 (Underline DOI 10.48448/ydvs-p287). *Action:* Cite as contrastive-decoding prior art (contribution 6); it was not in the known list.
- **Benchmarking and Mitigating Sycophancy in Medical Vision Language Models** ([link](https://arxiv.org/abs/2509.21979); 2025-09-26; v7 (updated 2026-05-28); read: metadata only (arXiv API); known paper). Known paper 'Benchmarking and Mitigating Sycophancy in Medical Vision Language Models': now v7, last updated 2026-05-28 (before the June search), 61 pages. *Action:* Already known; re-check the v7 text if any sentence of ours relies on its numbers.
- **MedHallTune: An Instruction-Tuning Benchmark for Mitigating Medical Hallucination in Vision-Language Models** ([link](https://arxiv.org/abs/2502.20780); 2025-02-28; v2 (updated 2026-07-30); read: metadata only (arXiv API); known paper). Known paper (MedHallTune): NEW VERSION v2 posted 2026-07-30 (v1 2025-02-28). *Action:* Re-read v2 before final submission; it may change the instruction-tuning mitigation numbers.
- **MedHallBench: A New Benchmark for Assessing Hallucination in Medical Large Language Models** ([link](https://arxiv.org/abs/2412.18947); 2024-12-25; v4 (updated 2025-03-28); read: metadata only (arXiv API); known paper). Known paper (MedHallBench): v4, last updated 2025-03-28; AAAI-25 Bridge Program. *Action:* Already known; no change.
- **Detecting and Evaluating Medical Hallucinations in Large Vision Language Models** ([link](https://arxiv.org/abs/2406.10185); 2024-06-14; v2 (updated 2026-04-27); read: metadata only (arXiv API); known paper). Known paper (Med-HallMark / MediHall Score): now v2, last updated 2026-04-27. *Action:* Already known; check the v2 changes if we quote its severity tiers.

## Excluded and unverified

### Excluded after verification
- **arXiv:2607.25589** 'Forensic Reproducibility Audit of a Radiology Vision-Language Model Benchmark' (v2, 2026-08-10): the arXiv record says 'Withdrawn by the author ... earlier versions should not be cited'. Not triaged, not in the bib.
- **doi:10.1038/s41598-026-71999-w** (Scientific Reports): surfaced as 'Systematic benchmarking of evaluation paradigms, safety boundaries, and clinical reasoning gaps for ...' but the registrar abstract shows it is a motor-rehabilitation video benchmark (ActionEval-MedBench). Irrelevant.

### Unverified / content not read (do NOT cite)
These were found through OpenAlex or web search. Their existence is confirmed for some (DOI metadata resolves) but I did not read an abstract from a primary source, so they are not triaged and not in the bib.
- doi:10.1007/978-3-032-38098-2_52 'Pressure-Tuned Auditor for Sycophancy-Resistant Breast Ultrasound VLM Diagnosis' (LNCS, 2026-09-25): DOI resolves via registrar; no abstract available to me. Possibly relevant to sycophancy in an extra modality.
- doi:10.1136/bjo-2025-328992 'Evaluating reasoning in multimodal large language models for ophthalmology: a bilingual benchmark study' (Br J Ophthalmol, 2026-06-10): DOI resolves; abstract not read. Possibly relevant to contribution 2 (ophthalmology).
- doi:10.3389/fmed.2026.1934968 'Comparative performance of contemporary multimodal large language models in retinal imaging question ...' (Front Med, 2026-08-20): DOI resolves; abstract not read.
- doi:10.1038/s41598-026-74077-3 'Image-embedded prompt injection vulnerability of vision-language models in dental radiology' (Sci Rep, 2026-10-03): DOI resolves; abstract not read. Adversarial robustness, probably LOW.
- doi:10.5281/zenodo.20807946 'Medical VLM Confidence Reliability' and doi:10.5281/zenodo.22245989 'cpath-triage' and doi:10.5281/zenodo.20513746 'BEYOND ACCURACY': Zenodo records (DOI resolves); I saw only a one-line description (code/artefacts for confidence-calibration audits of fine-tuned medical VLMs / MedGemma-27b on colorectal H&E patches). Not peer reviewed, not triaged.
- Papers whose arXiv metadata I verified but whose content I judged unrelated to the eight contributions (e.g. segmentation, survival prediction, LLM-only clinical text, dental/gait agents) are omitted; the full candidate pool is in `lit_cache/candidates.json`.
- Full text of the medRxiv histopathology study (10.64898/2026.09.18.26363369) could not be fetched (HTTP 403); only the API abstract was read.

### Verified and read, but not tabulated
- doi:10.3389/fdgth.2026.1904053 'Cross-modal bias in medical vision-language models: a pipeline-aware framework for mechanisms, evaluation, and mitigation' (Front Digit Health, 2026-08-07; landing page read): a narrative mini-review about demographic bias with no new experiments. It relays EchoBench numbers (LLaVA-Med >95% sycophantic reversals) and says specialist models are often more vulnerable; background for contribution 3 only, cite EchoBench directly instead.

## Queries run (2026-10-13)

All arXiv queries use `export.arxiv.org/api/query`, sorted by submittedDate descending. Round 1 restricted to cs.CV, cs.CL, cs.AI, cs.LG, eess.IV with submittedDate 2026-06-01 onward, up to 100 results per query. Round 2 and the back-sweep had NO category restriction, because round 1 missed cross-listed papers (CRAFT, MC-CXR, Hearsay, SHOVIR were found first through OpenAlex); round 2 paged up to 400 results per query.


**arxiv / benchmark-general** (7 queries)
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs) AND (abs:benchmark OR abs:evaluation)` -> 32 results
- `ti:hallucination AND (abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical)` -> 26 results
- `ti:hallucination AND (ti:vision OR ti:multimodal OR ti:VLM OR ti:LVLM OR ti:MLLM)` -> 70 results
- `abs:"medical" AND abs:"hallucination benchmark"` -> 2 results
- `abs:"medical multimodal" AND abs:hallucination` -> 3 results
- `abs:"medical VQA" AND abs:hallucination` -> 4 results
- `abs:"radiology report generation" AND abs:hallucination` -> 5 results

**arxiv / cxr** (3 queries)
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:"chest X-ray" OR abs:"chest radiograph" OR abs:CXR)` -> 6 results
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:radiology OR abs:radiologist) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs)` -> 4 results
- `abs:"report generation" AND (abs:"chest X-ray" OR abs:CXR) AND (abs:factual OR abs:hallucination)` -> 1 results

**arxiv / derm** (2 queries)
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:dermatology OR abs:dermoscopy OR abs:dermatoscopic OR abs:skin)` -> 3 results
- `(abs:dermatology OR abs:dermoscopy OR abs:"skin lesion") AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs) AND (abs:benchmark OR abs:reliability OR abs:safety)` -> 10 results

**arxiv / path** (2 queries)
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:histopathology OR abs:pathology OR abs:"whole slide")` -> 16 results
- `(abs:pathology OR abs:histopathology) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs) AND (abs:benchmark OR abs:reliability OR abs:safety OR abs:trustworthy)` -> 69 results

**arxiv / ophth** (2 queries)
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:ophthalmology OR abs:fundus OR abs:retinal OR abs:OCT)` -> 3 results
- `(abs:ophthalmology OR abs:fundus OR abs:retina) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs) AND (abs:benchmark OR abs:reliability OR abs:safety)` -> 8 results

**arxiv / severity-metric** (4 queries)
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:severity OR abs:"clinical risk" OR abs:"clinically weighted" OR abs:"risk-weighted" OR abs:harm) AND (abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical)` -> 16 results
- `abs:"severity-weighted" OR abs:"severity weighted"` -> 8 results
- `abs:"clinical significance" AND (abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs)` -> 0 results
- `abs:"clinical harm" AND (abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated)` -> 1 results

**arxiv / specialization** (4 queries)
- `abs:medical AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs) AND (abs:"general-purpose" OR abs:"general purpose" OR abs:"general-domain" OR abs:generalist) AND (abs:hallucination OR abs:safety OR abs:reliability)` -> 21 results
- `abs:"specialization paradox" OR abs:"specialisation paradox"` -> 0 results
- `(abs:"domain-specific" OR abs:"medical-specific" OR abs:"medical-tuned" OR abs:"medical fine-tuned") AND (abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs)` -> 10 results
- `abs:"medical fine-tuning" AND (abs:degrade OR abs:worse OR abs:underperform) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs)` -> 0 results

**arxiv / named-models** (2 queries)
- `(abs:LLaVA-Med OR abs:CheXagent OR abs:HuatuoGPT-Vision OR abs:Med-Flamingo OR abs:RadFM OR abs:MedGemma OR abs:Lingshu) AND (abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated)` -> 4 results
- `(abs:LLaVA-Med OR abs:CheXagent OR abs:HuatuoGPT-Vision OR abs:MedGemma OR abs:Lingshu) AND (abs:benchmark OR abs:safety OR abs:reliability)` -> 26 results

**arxiv / calibration** (4 queries)
- `(abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs) AND (abs:calibration OR abs:overconfidence OR abs:overconfident OR abs:"expected calibration error" OR abs:ECE)` -> 61 results
- `(abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs) AND (abs:"confidence elicitation" OR abs:"verbalized confidence" OR abs:uncertainty)` -> 53 results
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"uncertainty estimation" OR abs:"uncertainty quantification" OR abs:abstention OR abs:abstain)` -> 5 results
- `(abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs) AND (abs:decoding OR abs:temperature) AND (abs:robustness OR abs:calibration)` -> 14 results

**arxiv / mitigation** (5 queries)
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs) AND (abs:mitigation OR abs:mitigate OR abs:reduce OR abs:alleviate)` -> 15 results
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"retrieval-augmented" OR abs:RAG OR abs:"retrieval augmented")` -> 17 results
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"contrastive decoding" OR abs:"visual contrastive decoding" OR abs:VCD OR abs:"decoding strategy")` -> 1 results
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs) AND (abs:"fine-tuning" OR abs:"preference optimization" OR abs:DPO OR abs:RLHF)` -> 13 results
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"training-free" OR abs:"inference-time")` -> 10 results

**arxiv / stage-causal** (4 queries)
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"root cause" OR abs:causal OR abs:"error attribution" OR abs:"failure mode" OR abs:taxonomy)` -> 21 results
- `(abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs) AND abs:perception AND abs:knowledge AND abs:reasoning AND (abs:error OR abs:failure OR abs:hallucination)` -> 3 results
- `(abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs) AND (abs:"stage-wise" OR abs:"stage-level" OR abs:disentangle OR abs:"error localization")` -> 13 results
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"visual grounding" OR abs:"visual perception") AND (abs:"knowledge gap" OR abs:"medical knowledge")` -> 0 results

**arxiv / context-occlusion** (4 queries)
- `(abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs) AND (abs:occlusion OR abs:"masked region" OR abs:"region masking")` -> 8 results
- `(abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs) AND (abs:shortcut OR abs:"context bias" OR abs:"background bias" OR abs:"spurious correlation" OR abs:"language prior")` -> 24 results
- `(abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs) AND (abs:blind OR abs:"without the image" OR abs:"image-free" OR abs:"text-only") AND (abs:VQA OR abs:benchmark)` -> 23 results
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"visual reliance" OR abs:"image dependence" OR abs:"visual dependency")` -> 2 results

**arxiv / 3d** (2 queries)
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:CT OR abs:3D OR abs:volumetric OR abs:"PET/CT" OR abs:MRI) AND (abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs)` -> 6 results
- `(abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"3D medical" OR abs:volumetric) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs) AND abs:benchmark AND (abs:reliability OR abs:safety OR abs:hallucination)` -> 2 results

**arxiv / sycophancy** (3 queries)
- `(abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs) AND (abs:sycophancy OR abs:sycophantic)` -> 2 results
- `(abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"false premise" OR abs:counterfactual OR abs:"misleading prompt" OR abs:"adversarial prompt" OR abs:"leading question") AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs)` -> 14 results
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"false-premise" OR abs:"false premise" OR abs:misleading)` -> 5 results

**arxiv / judge** (3 queries)
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"LLM-as-a-judge" OR abs:"LLM-as-judge" OR abs:"LLM judge" OR abs:"automatic evaluation" OR abs:"claim-level" OR abs:"fact-checking")` -> 10 results
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:clinician OR abs:radiologist OR abs:"expert annotation" OR abs:"inter-annotator" OR abs:"human evaluation")` -> 20 results
- `(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated) AND (abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND abs:detection AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs)` -> 10 results

**arxiv / safety-transfer** (3 queries)
- `(abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs) AND (abs:"cross-modal" OR abs:"cross-modality" OR abs:"across modalities") AND (abs:safety OR abs:hallucination OR abs:reliability)` -> 19 results
- `(abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs) AND abs:benchmark AND (abs:"multi-modality" OR abs:"multiple modalities" OR abs:"four modalities") AND (abs:hallucination OR abs:trustworthiness OR abs:safety)` -> 0 results
- `abs:trustworthiness AND (abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical) AND (abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs) AND abs:benchmark` -> 15 results

**arxiv / known-followups** (9 queries)
- `abs:HalluCXR` -> 0 results
- `abs:ClinHallu` -> 1 results
- `abs:Med-HallMark OR abs:"MediHall Score"` -> 0 results
- `abs:MedHallTune` -> 0 results
- `abs:MedHEval OR abs:MedHallBench OR abs:MedVH` -> 0 results
- `abs:CARES AND abs:medical AND abs:trustworthiness` -> 2 results
- `abs:GMAI-MMBench` -> 0 results
- `abs:CREST AND abs:medical AND abs:hallucination` -> 0 results
- `ti:specialization AND abs:medical AND abs:sycophancy` -> 0 results

**openalex / openalex** (12 queries)
- `medical vision-language model hallucination benchmark` -> 25 results
- `hallucination chest X-ray vision-language model` -> 25 results
- `hallucination dermatology vision-language model` -> 25 results
- `histopathology vision-language model hallucination` -> 25 results
- `ophthalmology fundus vision-language model hallucination` -> 25 results
- `severity-weighted hallucination medical` -> 25 results
- `medical multimodal large language model hallucination mitigation` -> 25 results
- `calibration confidence medical vision-language models` -> 25 results
- `medical vision-language model sycophancy` -> 25 results
- `radiology report generation hallucination evaluation` -> 25 results
- `medical-specific versus general-purpose vision language models hallucination` -> 25 results
- `clinical safety evaluation multimodal large language models medical imaging` -> 25 results

**arxiv / r2-medical-title-vlm** (1 queries)
- `(ti:medical OR ti:clinical OR ti:radiology OR ti:radiologic) AND (ti:VLM OR ti:VLMs OR ti:"vision-language" OR ti:"vision language" OR ti:MLLM OR ti:MLLMs OR ti:LVLM OR ti:LVLMs OR ti:multimodal OR ti:"large language model")` -> 226 results

**arxiv / r2-cxr-title-vlm** (1 queries)
- `(ti:chest OR ti:radiograph OR ti:"X-ray" OR ti:CXR) AND (ti:VLM OR ti:VLMs OR ti:"vision-language" OR ti:"vision language" OR ti:MLLM OR ti:MLLMs OR ti:LVLM OR ti:LVLMs OR ti:multimodal OR ti:"large language model")` -> 29 results

**arxiv / r2-derm-title** (1 queries)
- `(ti:dermatology OR ti:dermoscopy OR ti:skin OR ti:dermatologic) AND (ti:VLM OR ti:VLMs OR ti:"vision-language" OR ti:"vision language" OR ti:MLLM OR ti:MLLMs OR ti:LVLM OR ti:LVLMs OR ti:multimodal OR ti:"large language model")` -> 6 results

**arxiv / r2-path-title** (1 queries)
- `(ti:pathology OR ti:histopathology OR ti:"whole-slide" OR ti:"whole slide") AND (ti:VLM OR ti:VLMs OR ti:"vision-language" OR ti:"vision language" OR ti:MLLM OR ti:MLLMs OR ti:LVLM OR ti:LVLMs OR ti:multimodal OR ti:"large language model")` -> 29 results

**arxiv / r2-ophth-title** (1 queries)
- `(ti:ophthalmology OR ti:fundus OR ti:retinal OR ti:ophthalmic) AND (ti:VLM OR ti:VLMs OR ti:"vision-language" OR ti:"vision language" OR ti:MLLM OR ti:MLLMs OR ti:LVLM OR ti:LVLMs OR ti:multimodal OR ti:"large language model")` -> 6 results

**arxiv / r2-halluc-title-all** (1 queries)
- `ti:hallucination OR ti:hallucinations OR ti:hallucinate` -> 298 results

**arxiv / r2-halluc-abs-medvqa** (1 queries)
- `abs:hallucination AND (abs:"medical visual question answering" OR abs:"medical VQA" OR abs:"Med-VQA" OR abs:"medical image")` -> 21 results

**arxiv / r2-sycophancy-title** (1 queries)
- `ti:sycophancy OR ti:sycophantic` -> 66 results

**arxiv / r2-calibration-title-med** (1 queries)
- `(ti:calibration OR ti:confidence OR ti:uncertainty OR ti:overconfident OR ti:overconfidence) AND (ti:medical OR ti:clinical OR ti:radiology OR ti:pathology)` -> 62 results

**arxiv / r2-shortcut-med** (1 queries)
- `(ti:shortcut OR ti:shortcuts OR ti:"blind" OR ti:"without an image" OR ti:"language prior" OR ti:context) AND (ti:medical OR ti:radiology OR ti:clinical OR ti:chest) AND abs:vision` -> 10 results

**arxiv / r2-benchmark-med-mllm** (1 queries)
- `(ti:benchmark OR ti:bench) AND (ti:medical OR ti:clinical) AND (ti:multimodal OR ti:vision OR ti:VLM OR ti:MLLM OR ti:LVLM)` -> 16 results

**arxiv / r2-causal-failure-med** (1 queries)
- `(ti:causal OR ti:failure OR ti:"error analysis" OR ti:diagnosing OR ti:tracing) AND (ti:medical OR ti:clinical) AND (ti:vision OR ti:multimodal OR ti:VLM OR ti:MLLM)` -> 8 results

**arxiv / back-sweep 2025-09-01..2026-05-31, no category restriction (paged to 300)**
- group `bs-calib` (see run_lit_backsweep.py for the exact query)
- group `bs-halluc-med-vlm` (see run_lit_backsweep.py for the exact query)
- group `bs-halluc-title-med` (see run_lit_backsweep.py for the exact query)
- group `bs-mitig` (see run_lit_backsweep.py for the exact query)
- group `bs-multimod` (see run_lit_backsweep.py for the exact query)
- group `bs-occl` (see run_lit_backsweep.py for the exact query)
- group `bs-severity` (see run_lit_backsweep.py for the exact query)
- group `bs-special` (see run_lit_backsweep.py for the exact query)
- group `bs-stage` (see run_lit_backsweep.py for the exact query)
- group `bs-syc` (see run_lit_backsweep.py for the exact query)

**Other lookups:** `arxiv_get` on every paper listed above (and on the known papers); `doi_get` (doi.org content negotiation) on 21 DOIs; Crossref and the medRxiv API for abstracts; OpenAlex `cites:` filter for the seven known arXiv papers (from 2026-06-01); WebSearch (standard) x2 for 'severity-weighted hallucination rate ... four modalities' and 'medical-tuned VLMs hallucinate more ... specialization paradox' (these surfaced 2603.22623 and 2603.23501, verified with `arxiv_get`).

## Limits of this search
- arXiv-first: journals indexed late or paywalled (Nature-family pages redirect to a login cookie endpoint) were verified through registrar metadata and OpenAlex/Crossref abstracts only.
- Round-1 arXiv recall was demonstrably incomplete (see above); round 2 and the back-sweep reduced but cannot rule out misses, particularly for papers that use none of the query vocabulary.
- OpenAlex citation counts for 2026 arXiv preprints are near zero, so 'no citing paper' is weak.
- A fetched arXiv HTML page (EchoBench) contained text that read like formatting instructions addressed to the reader; it was ignored.
